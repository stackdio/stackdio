import yaml
import time
import os
from datetime import datetime

import envoy
import celery
from celery.utils.log import get_task_logger

from cloud.utils import (
    get_provider_host_map,
    get_provider_type_and_class,
)

from .models import Stack

logger = get_task_logger(__name__)

ERROR_ALL_NODES_EXIST = 'All nodes in this map already exist'
ERROR_ALL_NODES_RUNNING = 'The following virtual machines were found already running'

def symlink(source, target):
    if os.path.isfile(target):
        os.remove(target)
    os.symlink(source, target)

@celery.task(name='stacks.launch_hosts')
def launch_hosts(stack_id, host_ids=None):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Launching hosts for stack: {0!r}'.format(stack))

        # Use SaltCloud to launch machines using the given stack's
        # map_file that should already be generated

        stack.set_status(Stack.LAUNCHING)

        # Set up logging for this launch
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()

        now = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_file = os.path.join(log_dir, 
                                '{}-{}.launch.log'.format(stack.slug, now))
        log_symlink = os.path.join(root_dir, '{}.launch.latest'.format(stack.slug))
        
        # "touch" the log file and symlink it to the latest
        with open(log_file, 'w') as f:
            pass
        symlink(log_file, log_symlink)

        # Launch stack
        cmd = ' '.join([
            'salt-cloud',
            '-y',                    # assume yes
            '-P',                    # parallelize VM launching
            '-lquiet',               # no logging on console
            '--log-file {0}',        # where to log
            '--log-file-level all',  # full logging
            '--out json',            # return JSON formatted results
            '--out-indent -1',       # don't format them; this is because of
                                     # a bug in salt-cloud
            '-m {1}',                # the map file to use for launching
        ]).format(log_file, stack.map_file.path)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        if result.status_code > 0:

            if ERROR_ALL_NODES_EXIST not in result.std_err and \
               ERROR_ALL_NODES_EXIST not in result.std_out and \
               ERROR_ALL_NODES_RUNNING not in result.std_err and \
               ERROR_ALL_NODES_RUNNING not in result.std_out:
                logger.error('launch command status_code: {}'.format(result.status_code))
                logger.error('launch command std_out: "{}"'.format(result.std_out))
                logger.error('launch command std_err: "{}"'.format(result.std_err))
                err_msg = result.std_err if len(result.std_err) else result.std_out
                stack.set_status(Stack.ERROR, err_msg)
                return False

        # All hosts are running (we hope!) so now we can pull the host metadata
        # and store what we want to keep track of.

        # Update status
        stack.set_status(Stack.CONFIGURING, 'Updating host metadata from running stack machines.')

        # Use salt-cloud to look up host information we need now that
        # they machines are running
        query_results = stack.query_hosts()

        for host in stack.hosts.all():
            # FIXME: This is cloud provider specific. Should farm it out to
            # the right implementation
            dns_name = query_results[host.hostname]['dnsName']
            logger.debug('{} = {}'.format(host.hostname, dns_name))

            # update the state of the host as provided by ec2
            state = query_results[host.hostname]['state']

            host.provider_dns = dns_name
            host.state = state
            host.save()

    except Stack.DoesNotExist:
        logger.exception('Attempted to launch an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while launching a Stack')
        stack.set_status(Stack.ERROR, str(e))

@celery.task(name='stacks.register_dns')
def register_dns(stack_id, host_ids=None):
    '''
    Must be ran after a Stack is up and running and all host information has
    been pulled and stored in the database.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Registering DNS for stack: {0!r}'.format(stack))

        stack.set_status(Stack.CONFIGURING)

        provider_host_map = get_provider_host_map(stack, host_ids=host_ids)
        for provider_obj, hosts in provider_host_map.iteritems():
            # Lookup the proper cloud provider implementation
            provider_type, provider_class = \
                get_provider_type_and_class(provider_obj.provider_type.id)

            # Use the provider implementation to register a set of hosts
            # with the appropriate cloud's DNS service
            provider_impl = provider_class(obj=provider_obj)
            provider_impl.register_dns(hosts)

    except Stack.DoesNotExist:
        logger.exception('Attempted to launch an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while launching a Stack')
        stack.set_status(Stack.ERROR, str(e))

@celery.task(name='stacks.provision_hosts')
def provision_hosts(stack_id, host_ids=None):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Provisioning hosts for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(Stack.PROVISIONING)

        # Set up logging for this task
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()
        now = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_file = os.path.join(log_dir, 
                                '{}-{}.provision.log'.format(stack.slug, now))

        # TODO: do we want to handle a subset of the hosts in a stack (e.g.,
        # when adding additional hosts?) for the moment it seems just fine
        # to run the highstate on all hosts even if some have already been
        # provisioned.

        # build up the command for salt
        cmd_args = [
            'salt',
            '-C',                   # compound targeting
            'G@stack_id:{}'.format(stack_id),  # target the nodes in this stack only
            'state.top',            # run this stack's top file
            stack.top_file.name,
        ]

        # Run the appropriate top file
        cmd = ' '.join(cmd_args)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        logger.debug('Command results:')
        logger.debug('status_code = {}'.format(result.status_code))
        logger.debug('std_out = {}'.format(result.std_out))
        logger.debug('std_err = {}'.format(result.std_err))

        with open(log_file, 'a') as f:
            f.write('\n')
            f.write(result.std_out)

        # symlink the logfile
        log_symlink = os.path.join(root_dir, 
                                   '{}.provision.latest'.format(stack.slug))
        symlink(log_file, log_symlink)
        
        # TODO: probably should figure out if an error occurred. A 
        # good mix of looking at envoy's status_code and parsing
        # the log file would be nice.

    except Stack.DoesNotExist:
        logger.exception('Attempted to provision an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while provisioning a Stack')
        stack.set_status(Stack.ERROR, str(e))


@celery.task(name='stacks.finish_stack')
def finish_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Finishing stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(Stack.FINALIZING, 'Performing any last minute updates and checks.')

        # TODO: Are there any last minute updates and checks?

        # Update status
        stack.set_status(Stack.FINISHED)

    except Stack.DoesNotExist:
        logger.exception('Attempted to provision an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while finishing a Stack')
        stack.set_status(Stack.ERROR, str(e))

@celery.task(name='stacks.destroy_hosts', ignore_result=True)
def destroy_hosts(stack_id, host_ids=None):
    '''
    Destroy the given stack id or a subset of the stack if host_ids
    is set.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)

        # Build up the salt-cloud command
        cmd_args = [
            'salt-cloud',
            '-y',                   # assume yes
            '-P',                   # destroy in parallel
            '-d',                   # destroy argument
            '--out yaml',           # output in yaml
        ]

        # if host ids is given, we're going to terminate only those hosts
        if host_ids:
            stack.set_status(Stack.DESTROYING, 'Destroying hosts.')
            hosts = stack.hosts.filter(id__in=host_ids)
            logger.info('Destroying hosts {0!r} on stack {1!r}'.format(
                hosts, 
                stack
            ))

            # add the machines to destory on to the cmd_args list
            cmd_args.extend([h.hostname for h in hosts])

        # or we'll destroy the entire stack by giving the map file with all
        # hosts defined
        else:
            stack.set_status(Stack.DESTROYING, 'Destroying stack.')
            logger.info('Destroying complete stack: {0!r}'.format(stack))

            # Check for map file, and if it doesn't exist just remove
            # the stack and return
            if not os.path.isfile(stack.map_file.path):
                logger.warn('Map file for stack {} does not exist. '
                            'Deleting stack anyway.'.format(stack))
                stack.delete()
                return

            # Add the location to the map to destroy the entire stack
            cmd_args.append('-m {}'.format(stack.map_file.path))

        # Use salt-cloud to destroy the stack or hosts
        cmd = ' '.join(cmd_args)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        if result.status_code > 0:
            err_msg = result.std_err if result.std_err else result.std_out
            stack.set_status(Stack.ERROR, err_msg)
            return

        # delete the stack or delete the hosts
        if host_ids is None:
            stack.delete()
        else:
            hosts.delete()
            stack.set_status(Stack.OK, 'Hosts deleted.')

    except Stack.DoesNotExist:
        logger.exception('Attempted to destroy an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while finishing a Stack')
        stack.set_status(Stack.ERROR, str(e))

@celery.task(name='stacks.unregister_dns')
def unregister_dns(stack_id, host_ids=None):
    '''
    Removes all host information from DNS. Intended to be used just before a stack
    is terminated or stopped or put into some state where DNS no longer applies.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Unregistering DNS for stack: {0!r}'.format(stack))

        stack.set_status(Stack.CONFIGURING, 'Unregistering DNS entries.')

        provider_host_map = get_provider_host_map(stack, host_ids=host_ids)
        for provider_obj, hosts in provider_host_map.iteritems():
            # Lookup the proper cloud provider implementation
            provider_type, provider_class = \
                get_provider_type_and_class(provider_obj.provider_type.id)

            # Use the provider implementation to register a set of hosts
            # with the appropriate cloud's DNS service
            provider_impl = provider_class(obj=provider_obj)
            provider_impl.unregister_dns(hosts)

    except Stack.DoesNotExist:
        logger.exception('Attempted to unregister DNS for a Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while unregistering DNS for a stack')
        stack.set_status(Stack.ERROR, str(e))
