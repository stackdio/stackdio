import time
import os
import json
from datetime import datetime

import envoy
import celery
import yaml
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from django.utils.translation import ungettext

from volumes.models import Volume

from .models import (
    Stack,
    Level,
)

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

        stack.set_status(
            launch_hosts.name,
            'Hosts are being launched. This could take a while.')

        # Set up logging for this launch
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()

        now = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_file = os.path.join(log_dir, 
                                '{0}-{1}.launch.log'.format(stack.slug, now))
        log_symlink = os.path.join(root_dir, '{0}.launch.latest'.format(
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
            '--out=yaml',            # return YAML formatted results
            '-m {1}',                # the map file to use for launching
        ]).format(
            log_file,
            stack.map_file.path
        )

        logger.debug('Executing command: {0}'.format(cmd))
        result = envoy.run(str(cmd))
        logger.debug('Command results:')
        logger.debug('status_code = {0}'.format(result.status_code))
        logger.debug('std_out = {0}'.format(result.std_out))
        logger.debug('std_err = {0}'.format(result.std_err))

        try:
            # Look for errors if we got valid JSON
            result_json = yaml.safe_load(result.std_out)
            errors = set()
            for h, v in result_json.iteritems():
                logger.debug('Checking host {0} for errors.'.format(h))

                # Error format #1
                if 'Errors' in v and 'Error' in v['Errors']:
                    errors.add(v['Errors']['Error']['Message'])

                # Error format #2
                elif 'Error' in v:
                    errors.add(v['Error'])

            if errors:
                logger.debug('Errors found!: {0!r}'.format(errors))
                for err_msg in errors:
                    stack.set_status(launch_hosts.name, err_msg, Level.ERROR)
                raise StackTaskException('Error(s) while launching stack '
                                         '{0}'.format(stack_id))
        except Exception, e:
            logger.debug('Unable to parse YAML from envoy results.')
            pass

        if result.status_code > 0:
            if ERROR_ALL_NODES_EXIST not in result.std_err and \
               ERROR_ALL_NODES_EXIST not in result.std_out and \
               ERROR_ALL_NODES_RUNNING not in result.std_err and \
               ERROR_ALL_NODES_RUNNING not in result.std_out:
                err_msg = result.std_err if result.std_err else result.std_out
                stack.set_status(launch_hosts.name, err_msg, Level.ERROR)
                raise StackTaskException('Error launching stack {0} with '
                                         'salt-cloud: {1!r}'.format(
                                            stack_id, 
                                            err_msg))
        else:
            stack.set_status(launch_hosts.name, 'Finished launching hosts.')

    except Stack.DoesNotExist, e:
        err_msg = 'Unknown stack id {0}'.format(stack_id)
        logger.exception(err_msg)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(launch_hosts.name, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise

@celery.task(name='stacks.update_metadata')
def update_metadata(stack_id, host_ids=None):
    try:

        # All hosts are running (we hope!) so now we can pull the various
        # metadata and store what we want to keep track of.

        stack = Stack.objects.get(id=stack_id)
        driver = stack.get_driver()
        logger.info('Updating metadata for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(update_metadata.name, 
                         'Collecting host metadata from cloud provider.')

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
                    raise

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
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(update_metadata.name, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise

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
        stack.set_status(tag_infrastructure.name, 
                         'Tagging stack infrastructure.')

        driver = stack.get_driver()
        volumes = Volume.objects.filter(host__in=hosts)
        driver.tag_resources(stack, hosts, volumes)

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(tag_infrastructure.name, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise

@celery.task(name='stacks.register_dns')
def register_dns(stack_id, host_ids=None):
    '''
    Must be ran after a Stack is up and running and all host information has
    been pulled and stored in the database.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Registering DNS for stack: {0!r}'.format(stack))

        stack.set_status(register_dns.name, 
                         'Registering hosts with DNS provider.')

        # Use the provider implementation to register a set of hosts
        # with the appropriate cloud's DNS service
        driver = stack.get_driver()
        driver.register_dns(stack.get_hosts())

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(register_dns.name, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise

@celery.task(name='stacks.ping')
def ping(stack_id, timeout=5*60, interval=5, max_failures=25):
    '''
    Attempts to use salt's test.ping module to ping the entire stack
    and confirm that all hosts are reachable by salt.

    @stack_id: The id of the stack to ping. We will use salt's grain
               system to target the hosts with this stack id
    @timeout: The maximum amount of time (in seconds) to wait for ping
              to return valid JSON.
    @interval: The looping interval, ie, the amount of time to sleep
               before the next iteration.
    @max_failures: Number of ping failures before giving up completely.
                   The timeout does not affect this parameter.
    @raises StackTaskException
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        stack.set_status(ping.name,
                         'Attempting to ping all hosts.',
                         Level.INFO)

        # Ping
        cmd_args = [
            'salt',
            '--out=yaml',
            '-G stack_id:{0}'.format(stack_id), # target the nodes in this
                                                # stack only
            'test.ping',                        # ping all VMs
        ]

        # Execute until successful, failing after a few attempts
        cmd = ' '.join(cmd_args)
        failures = 0
        duration = timeout

        while True: 
            result = envoy.run(str(cmd))
            logger.debug('Executing command: {0}'.format(cmd))
            logger.debug('Command results:')
            logger.debug('status_code = {0}'.format(result.status_code))
            logger.debug('std_out = {0}'.format(result.std_out))
            logger.debug('std_err = {0}'.format(result.std_err))

            if result.status_code == 0:
                try:
                    result_json = yaml.safe_load(result.std_out)
                    if result_json:
                        break
                except Exception, e:
                    failures += 1
                    logger.debug('Unable to parse YAML from envoy results. '
                                 'Total failures: {0}'.format(failures))

            if timeout < 0:
                err_msg = 'Unable to ping hosts in 00:{0:02d}:{1:02d}'.format(
                    duration // 60,
                    duration % 60,
                )
                stack.set_status(ping.name, err_msg, Level.ERROR)
                raise StackTaskException(err_msg)

            if failures > max_failures:
                err_msg = 'Max failures ({0}) reached while pinging ' \
                          'hosts.'.format(max_failures)
                stack.set_status(ping.name, err_msg, Level.ERROR)
                raise StackTaskException(err_msg)

            time.sleep(interval)
            timeout -= interval

        # make sure all hosts are accounted for
        false_hosts = []
        for host, value in result_json.iteritems():
            if isinstance(value, bool) and not value:
                false_hosts.append(host)

        if false_hosts:
            err_msg = 'Unable to ping hosts: {0}'.format(','.join(false_hosts))
            stack.set_status(ping.name, err_msg, Level.ERROR)
            raise StackTaskException(err_msg)

        stack.set_status(ping.name, 
                         'All hosts pinged successfully.',
                         Level.INFO)

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(ping.name, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise

@celery.task(name='stacks.sync_all')
def sync_all(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Syncing all salt systems for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(sync_all.name,
                         'Synchronizing salt systems on all hosts.')

        # build up the command for salt
        cmd_args = [
            'salt',
            '-G stack_id:{0}'.format(stack_id), # target the nodes in this
                                                # stack only
            'saltutil.sync_all',                # sync all systems
        ]

        # Execute
        cmd = ' '.join(cmd_args)
        logger.debug('Executing command: {0}'.format(cmd))
        result = envoy.run(str(cmd))
        logger.debug('Command results:')
        logger.debug('status_code = {0}'.format(result.status_code))
        logger.debug('std_out = {0}'.format(result.std_out))
        logger.debug('std_err = {0}'.format(result.std_err))

        if result.status_code > 0:
            err_msg = result.std_err if result.std_err else result.std_out
            stack.set_status(sync_all.name, err_msg, Level.ERROR)
            raise StackTaskException('Error syncing salt data on stack {0}: '
                                     '{1!r}'.format(
                                        stack_id, 
                                        err_msg)
                                     )

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(sync_all.name, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise

@celery.task(name='stacks.provision_hosts')
def provision_hosts(stack_id, host_ids=None):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Provisioning hosts for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(provision_hosts.name,
                         'Provisioning all hosts.')

        # Set up logging for this task
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()
        now = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_file = os.path.join(log_dir, 
                                '{0}-{1}.provision.log'.format(stack.slug, now))

        # TODO: do we want to handle a subset of the hosts in a stack (e.g.,
        # when adding additional hosts?) for the moment it seems just fine
        # to run the highstate on all hosts even if some have already been
        # provisioned.

        # build up the command for salt
        cmd_args = [
            'salt',
            '--out=yaml',           # yaml formatted output
            '-G stack_id:{0}'.format(stack_id), # target the nodes in this
                                                # stack only
            'state.top',            # run this stack's top file
            stack.top_file.name,
        ]

        # Run the appropriate top file
        cmd = ' '.join(cmd_args)

        logger.debug('Executing command: {0}'.format(cmd))
        try:
            result = envoy.run(str(cmd))
        except AttributeError, e:
            err_msg = 'Error running command: \'{0}\''.format(cmd)
            logger.exception(err_msg)
            stack.set_status(provision_hosts.name, err_msg, Level.ERROR)
            raise StackTaskException(err_msg)

        if result is None:
            msg = 'Provisioning command returned None. Status, stdout ' \
                  'and stderr unknown.'
            logger.warn(msg)
            stack.set_status(msg)
        else:
            logger.debug('Command results:')
            logger.debug('status_code = {0}'.format(result.status_code))
            logger.debug('std_out = {0}'.format(result.std_out))
            logger.debug('std_err = {0}'.format(result.std_err))

            if result.status_code > 0:
                err_msg = result.std_err if result.std_err else result.std_out
                stack.set_status(provision_hosts.name, err_msg, Level.ERROR)
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
                                       '{0}.provision.latest'.format(stack.slug))
            symlink(log_file, log_symlink)
        
            # load JSON so we can attempt to catch provisioning errors
            output = yaml.safe_load(result.std_out)

            # each key in the dict is a host, and the value of the host
            # is either a list or dict. Those that are lists we can
            # assume to be a list of errors
            if output is not None:
                errors = {}
                for host, host_result in output.iteritems():
                    if type(host_result) is list:
                        errors[host] = host_result

                    elif type(host_result) is dict:
                        # TODO: go deeper into the host_result dictionaries
                        # looking for bad salt state executions
                        pass

                if errors:
                    err_msg = 'Provisioning errors on hosts: {0}. Please see the ' \
                              'provisioning log for more details.'.format(
                                ', '.join(errors.keys()))
                    stack.set_status(provision_hosts.name, err_msg, Level.ERROR)
                    raise StackTaskException(err_msg)
        
    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(provision_hosts.name, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise

@celery.task(name='stacks.finish_stack')
def finish_stack(stack_id):
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Finishing stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(finish_stack.name,
                         'Performing final updates to Stack.')

        # TODO: Are there any last minute updates and checks?

        # Update status
        stack.set_status(finish_stack.name, 'Finished executing tasks.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(finish_stack.name, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise

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
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(Stack.ERROR, err_msg)
        logger.exception(err_msg)
        raise

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
            '--out=yaml',           # output in JSON
        ]

        # if host ids is given, we're going to terminate only those hosts
        if host_ids:
            stack.set_status(Stack.DESTROYING, 
                             'Destroying hosts {0!r}.'.format(hosts))
            logger.info('Destroying hosts {0!r} on stack {1!r}'.format(
                hosts, 
                stack
            ))

            # add the machines to destory on to the cmd_args list
            cmd_args.extend([h.hostname for h in hosts])

        # or we'll destroy the entire stack by giving the map file with all
        # hosts defined
        else:
            stack.set_status(Stack.DESTROYING, 'Destroying all hosts.')
            logger.info('Destroying complete stack: {0!r}'.format(stack))

            # Check for map file, and if it doesn't exist just remove
            # the stack and return
            if not stack.map_file or not os.path.isfile(stack.map_file.path):
                logger.warn('Map file for stack {0} does not exist. '
                            'Deleting stack anyway.'.format(stack))
                stack.delete()
                return

            # Add the location to the map to destroy the entire stack
            cmd_args.append('-m {0}'.format(stack.map_file.path))

        # Use salt-cloud to destroy the stack or hosts
        cmd = ' '.join(cmd_args)

        logger.debug('Executing command: {0}'.format(cmd))
        result = envoy.run(str(cmd))
        logger.debug('Command results:')
        logger.debug('status_code = {0}'.format(result.status_code))
        logger.debug('std_out = {0}'.format(result.std_out))
        logger.debug('std_err = {0}'.format(result.std_err))

        if result.status_code > 0:
            err_msg = result.std_err if result.std_err else result.std_out
            stack.set_status(Stack.ERROR, err_msg)
            raise StackTaskException('Error destroying hosts on stack {0}: '
                                     '{1!r}'.format(
                                        stack_id, 
                                        err_msg)
                                     )

        # delete hosts
        hosts.delete()
        stack.set_status(Stack.OK, 'Hosts successfully deleted.')

        # optionally delete the stack as well
        if delete_stack:
            stack.delete()

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(Stack.ERROR, err_msg)
        logger.exception(err_msg)
        raise

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

        stack.set_status(Stack.CONFIGURING,
                         'Unregistering hosts with DNS provider.')

        # Use the provider implementation to register a set of hosts
        # with the appropriate cloud's DNS service
        driver = stack.get_driver()
        driver.unregister_dns(stack.get_hosts())

        stack.set_status(Stack.CONFIGURING,
                         'Finished unregistering hosts with DNS provider.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(Stack.ERROR, err_msg)
        logger.exception(err_msg)
        raise

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
        fun = getattr(driver, '_action_{0}'.format(action))
        fun(stack=stack, *args, **kwargs)

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(Stack.ERROR, err_msg)
        logger.exception(err_msg)
        raise

