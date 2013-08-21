import yaml
import time
import os
from datetime import datetime

import envoy
import celery
from celery.result import AsyncResult
from celery.utils.log import get_task_logger

from volumes.models import Volume

from .models import Stack

logger = get_task_logger(__name__)

ERROR_ALL_NODES_EXIST = 'All nodes in this map already exist'
ERROR_ALL_NODES_RUNNING = 'The following virtual machines were found ' \
                          'already running'


class StackTaskException(Exception):
    pass

def symlink(source, target):
    if os.path.isfile(target):
        os.remove(target)
    os.symlink(source, target)

@celery.task(name='stacks.handle_error')
def handle_error(stack_id, task_id):
    logger.debug('stack_id: {0}'.format(stack_id))
    logger.debug('task_id: {0}'.format(task_id))
    result = AsyncResult(task_id)
    exc = result.get(propagate=False)
    logger.debug('Task {0} raised exception: {1!r}\n{2!r}'
        .format(task_id, exc, result.traceback))

@celery.task(name='stacks.launch_hosts')
def launch_hosts(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        hosts = stack.get_hosts()

        # generate the hosts for the stack
        if not hosts:
            stack.create_hosts()

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
        log_symlink = os.path.join(root_dir, '{}.launch.latest'.format(
            stack.slug)
        )
        
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
        ]).format(
            log_file,
            stack.map_file.path
        )

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        if result.status_code > 0:

            if ERROR_ALL_NODES_EXIST not in result.std_err and \
               ERROR_ALL_NODES_EXIST not in result.std_out and \
               ERROR_ALL_NODES_RUNNING not in result.std_err and \
               ERROR_ALL_NODES_RUNNING not in result.std_out:
                logger.error('launch command status_code: {}'.format(
                    result.status_code)
                )
                logger.error('launch command std_out: "{}"'.format(
                    result.std_out)
                )
                logger.error('launch command std_err: "{}"'.format(
                    result.std_err)
                )
                err_msg = result.std_err if result.std_err else result.std_out
                stack.set_status(Stack.ERROR, err_msg)
                raise StackTaskException('Error launching stack {0} with '
                                         'salt-cloud: {1!r}'.format(
                                            stack_id, 
                                            err_msg)
                                         )
    except Stack.DoesNotExist, e:
        err_msg = 'Unknown stack id {0}'.format(stack_id)
        logger.exception(err_msg)
        raise StackTaskException(err_msg)
    except Exception, e:
        err_msg = 'Unhandled exception'
        logger.exception(err_msg)
        stack.set_status(Stack.ERROR, str(e))
        raise StackTaskException(err_msg)

@celery.task(name='stacks.update_metadata')
def update_metadata(stack_id, host_ids=None):
    try:

        # All hosts are running (we hope!) so now we can pull the various
        # metadata and store what we want to keep track of.

        stack = Stack.objects.get(id=stack_id)
        driver = stack.get_driver()
        logger.info('Updating metadata for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(Stack.CONFIGURING, 
                         'Updating host metadata from running stack '
                         'machines.')

        # Use salt-cloud to look up host information we need now that
        # the machines are running
        query_results = stack.query_hosts()

        # keep track of terminated hosts for future removal
        hosts_to_remove = []

        # also keep track if volume information was updated
        bdm_updated = False

        for host in stack.hosts.all():
            host_data = query_results[host.hostname]

            if 'state' in host_data \
                and host_data['state'] == driver.STATE_TERMINATED:

                hosts_to_remove.append(host)
                continue

            # FIXME: This is cloud provider specific. Should farm it out to
            # the right implementation

            # The instance id of the host
            host.instance_id = host_data['instanceId']

            # Get the host's public IP/host set by the cloud provider. This is
            # used later when we tie the machine to DNS
            host.provider_dns = host_data['dnsName'] or ''

            # update the state of the host as provided by ec2
            host.state = host_data['state']

            # update volume information
            block_device_mappings = host_data \
                .get('blockDeviceMapping', {}) \
                .get('item', [])

            if type(block_device_mappings) is not list:
                block_device_mappings = [block_device_mappings]

            # for each block device mapping found on the running host,
            # try to match the device name up with that stored in the DB
            # if a match is found, fill in the metadata and save the volume
            for bdm in block_device_mappings:
                bdm_volume_id = bdm['ebs']['volumeId']
                try:
                    # attempt to get the volume for this host that
                    # has been created
                    volume = host.volumes.get(device=bdm['deviceName'])

                    # update the volume information if needed
                    if volume.volume_id != bdm_volume_id:
                        volume.volume_id = bdm['ebs']['volumeId']
                        volume.attach_time = bdm['ebs']['attachTime']

                        # save the new volume info
                        volume.save()
                        bdm_updated = True

                except Volume.DoesNotExist, e:
                    # This is most likely fine. Usually means that the 
                    # EBS volume for the root drive was found instead.
                    pass
                except Exception, e:
                    err_msg = 'Unhandled exception while updating volume ' \
                              'metadata.'
                    logger.exception(err_msg)
                    logger.debug(block_device_mappings)
                    raise StackTaskException(err_msg)

            # Update spot instance metadata
            if 'spotInstanceRequestId' in host_data:
                host.sir_id = host_data['spotInstanceRequestId']
            else:
                host.sir_id = 'NA'

            # save the host
            host.save()

        for h in hosts_to_remove:
            h.delete()

        # if volume metadata was updated, regenerate the map file
        # to account for the volume_id changes
        if bdm_updated:
            stack._generate_map_file()

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

@celery.task(name='stacks.tag_infrastructure')
def tag_infrastructure(stack_id, host_ids=None):
    '''
    Tags hosts and volumes with certain metadata that should prove useful
    to anyone using the AWS console.

    ORDER MATTERS! Make sure that tagging only comes after you've executed
    the `update_metadata` task as that task actually pulls in information
    we need to use the tagging API effectively.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        hosts = stack.get_hosts()

        logger.info('Tagging infrastructure for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(Stack.CONFIGURING, 
                         'Tagging hosts and volumes for stack.')

        driver = stack.get_driver()
        volumes = Volume.objects.filter(host__in=hosts)
        driver.tag_resources(stack, hosts, volumes)

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

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

        # Use the provider implementation to register a set of hosts
        # with the appropriate cloud's DNS service
        driver = stack.get_driver()
        driver.register_dns(stack.get_hosts())

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

@celery.task(name='stacks.sync_all')
def sync_all(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Syncing all salt systems for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(Stack.SYNCING)

        # build up the command for salt
        cmd_args = [
            'salt',
            '-C',                               # compound targeting
            'G@stack_id:{}'.format(stack_id),   # target the nodes in this
                                                # stack only
            'saltutil.sync_all',                # sync all systems
        ]

        # Execute
        cmd = ' '.join(cmd_args)
        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        if result.status_code > 0:
            logger.debug('Command results:')
            logger.debug('status_code = {}'.format(result.status_code))
            logger.debug('std_out = {}'.format(result.std_out))
            logger.debug('std_err = {}'.format(result.std_err))

            err_msg = result.std_err if result.std_err else result.std_out
            stack.set_status(Stack.ERROR, err_msg)
            raise StackTaskException('Error syncing salt data on stack {0}: '
                                     '{1!r}'.format(
                                        stack_id, 
                                        err_msg)
                                     )

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

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
            'G@stack_id:{}'.format(stack_id),   # target the nodes in this
                                                #stack only
            'state.top',            # run this stack's top file
            stack.top_file.name,
        ]

        # Run the appropriate top file
        cmd = ' '.join(cmd_args)

        logger.debug('Excuting command: {0}'.format(cmd))
        result = envoy.run(cmd)

        if result.status_code > 0:
            logger.debug('Command results:')
            logger.debug('status_code = {}'.format(result.status_code))
            logger.debug('std_out = {}'.format(result.std_out))
            logger.debug('std_err = {}'.format(result.std_err))

            err_msg = result.std_err if result.std_err else result.std_out
            stack.set_status(Stack.ERROR, err_msg)
            raise StackTaskException('Error provisioning stack {0}: '
                                     '{1!r}'.format(
                                        stack_id, 
                                        err_msg)
                                     )

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
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

@celery.task(name='stacks.finish_stack')
def finish_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Finishing stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(Stack.FINALIZING,
                         'Performing any last minute updates and checks.')

        # TODO: Are there any last minute updates and checks?

        # Update status
        stack.set_status(Stack.RUNNING)

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

@celery.task(name='stacks.register_volume_delete')
def register_volume_delete(stack_id, host_ids=None):
    '''
    Modifies the instance attributes for the volumes in a stack (or host_ids)
    that will automatically delete the volumes when the machines are
    terminated.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        hosts = stack.get_hosts(host_ids) 
        if not hosts:
            return

        # use the stack driver to register all volumes on the hosts to
        # automatically delete after the host is terminated
        driver = stack.get_driver()
        driver.register_volumes_for_delete(hosts)

    except Stack.DoesNotExist, e:
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

@celery.task(name='stacks.destroy_hosts')
def destroy_hosts(stack_id, host_ids=None, delete_stack=True):
    '''
    Destroy the given stack id or a subset of the stack if host_ids
    is set.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        hosts = stack.get_hosts(host_ids)

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
            if not stack.map_file or not os.path.isfile(stack.map_file.path):
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
            logger.debug('Command results:')
            logger.debug('status_code = {}'.format(result.status_code))
            logger.debug('std_out = {}'.format(result.std_out))
            logger.debug('std_err = {}'.format(result.std_err))

            err_msg = result.std_err if result.std_err else result.std_out
            stack.set_status(Stack.ERROR, err_msg)
            raise StackTaskException('Error destroying hosts on stack {0}: '
                                     '{1!r}'.format(
                                        stack_id, 
                                        err_msg)
                                     )

        # delete hosts
        hosts.delete()
        stack.set_status(Stack.OK, 'Hosts deleted.')

        # optionally delete the stack as well
        if delete_stack:
            stack.delete()

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

@celery.task(name='stacks.unregister_dns')
def unregister_dns(stack_id, host_ids=None):
    '''
    Removes all host information from DNS. Intended to be used just before a
    stack is terminated or stopped or put into some state where DNS no longer
    applies.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Unregistering DNS for stack: {0!r}'.format(stack))

        stack.set_status(Stack.CONFIGURING, 'Unregistering DNS entries.')

        # Use the provider implementation to register a set of hosts
        # with the appropriate cloud's DNS service
        driver = stack.get_driver()
        driver.unregister_dns(stack.get_hosts())

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

@celery.task(name='stacks.execute_action')
def execute_action(stack_id, action, *args, **kwargs):
    '''
    Executes a defined action using the stack's cloud provider implementation.
    Actions are defined on the implementation class (e.g, _action_{action})
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Executing action \'{0}\' on stack: {1!r}'.format(
            action,
            stack)
        )

        # Use the provider implementation to register a set of hosts
        # with the appropriate cloud's DNS service
        driver = stack.get_driver()
        hosts = stack.get_hosts()
        fun = getattr(driver, '_action_{}'.format(action))
        fun(stack=stack, *args, **kwargs)

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {}'.format(stack_id)
        raise StackTaskException(err_msg)
    except Exception, e:
        stack.set_status(Stack.ERROR, str(e))
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        raise StackTaskException(err_msg)

