import yaml
import time
import os.path
from datetime import datetime
from collections import defaultdict

import envoy
import celery
from celery.utils.log import get_task_logger

from cloud.utils import get_provider_type_and_class

from .models import Stack

logger = get_task_logger(__name__)

ERROR_ALL_NODES_EXIST = 'All nodes in this map already exist'


@celery.task(name='stacks.launch_stack')
def launch_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Launching new stack: {0!r}'.format(stack))

        # Use SaltCloud to launch machines using the given stack's
        # map_file that should already be generated

        stack.set_status(Stack.LAUNCHING)

        # TODO: It would be nice if we could control the salt-cloud log
        # file at runtime

        # Get paths
        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_file = stack.map_file.path
        log_file = stack.map_file.path + '.{}.log'.format(now)

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
        ]).format(log_file, map_file)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        if result.status_code > 0:

            if ERROR_ALL_NODES_EXIST not in (result.std_err, result.std_out):
                logger.error(result.status_code)
                logger.error(result.std_out)
                logger.error(result.std_err)
                err_msg = result.std_err if len(result.std_err) else result.std_out
                stack.set_status(Stack.ERROR, err_msg)
                return

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
            host.public_dns = query_results[host.hostname]['extra']['dns_name']
            host.save()

    except Stack.DoesNotExist:
        logger.error('Attempted to launch an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while launching a Stack')
        stack.set_status(Stack.ERROR, str(e))

@celery.task(name='stacks.configure_dns')
def configure_dns(stack_id):
    '''
    Must be ran after a Stack is up and running and all host information has
    been pulled and stored in the database
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Configuring DNS for stack: {0!r}'.format(stack))

        stack.set_status(Stack.CONFIGURING)

        # build up a map of cloud provider to hosts as each host could
        # be on a separate cloud provider
        hosts = stack.hosts.all()
        provider_host_map = defaultdict(list)
        for host in hosts:
            provider = host.get_provider()
            provider_host_map[provider].append(host)

        for provider_obj, hosts in provider_host_map.iteritems():
            # Lookup the proper cloud provider implementation
            provider_type, provider_class = \
                get_provider_type_and_class(provider.provider_type.id)

            # Use the provider implementation to register a set of hosts
            # with the appropriate cloud's DNS service
            provider_impl = provider_class(obj=provider_obj)
            provider_impl.register_dns(hosts)

    except Stack.DoesNotExist:
        logger.error('Attempted to launch an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while launching a Stack')
        stack.set_status(Stack.ERROR, str(e))

@celery.task(name='stacks.provision_stack')
def provision_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Provisioning stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(Stack.PROVISIONING)

        # Run the appropriate top file
        cmd = ' '.join([
            'salt',
            '-C',                   # compound targeting
            'G@stack_id:{}'.format(stack_id),  # target the nodes in this stack only
            'state.top',            # run this stack's top file
            stack.top_file.name,
            '--out yaml'            # output in yaml format
        ]).format(stack_id)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        logger.debug('salt state.top stdout:')
        logger.debug(result.std_out)

        logger.debug('salt state.top stderr:')
        logger.debug(result.std_err)

    except Stack.DoesNotExist:
        logger.error('Attempted to provision an unknown Stack with id {}'.format(stack_id))
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
        logger.error('Attempted to provision an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while finishing a Stack')
        stack.set_status(Stack.ERROR, str(e))

@celery.task(name='stacks.destroy_stack', ignore_result=True)
def destroy_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Destroying stack: {0!r}'.format(stack))

        # Check for map file, and if it doesn't exist just remove
        # the stack and return
        if not os.path.isfile(stack.map_file.path):
            logger.warn('Map file for stack {} does not exist. '
                        'Deleting stack anyway.'.format(stack))
            stack.delete()
            return

        # Run the appropriate top file
        cmd = ' '.join([
            'salt-cloud',
            '-y',                   # assume yes
            '-P',                   # destroy in parallel
            '-m {0}',               # the map file to use for launching
            '-d',                   # destroy the stack
            '--out yaml',           # output in yaml
        ]).format(stack.map_file.path)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        if result.status_code > 0:
            err_msg = result.std_err if len(result.std_err) else result.std_out
            stack.set_status(Stack.ERROR, err_msg)
            return

        stack.delete()

    except Stack.DoesNotExist:
        logger.error('Attempted to destroy an unknown Stack with id {}'.format(stack_id))
    except Exception, e:
        logger.exception('Unhandled exception while finishing a Stack')
        stack.set_status(Stack.ERROR, str(e))
