import time
import os
import shutil
from datetime import datetime

import envoy
import celery
import yaml
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from django.conf import settings

from volumes.models import Volume

from stacks.models import (
    Stack,
    Level,
)
from cloud.models import SecurityGroup
from core.exceptions import BadRequest

logger = get_task_logger(__name__)

ERROR_ALL_NODES_EXIST = 'All nodes in this map already exist'
ERROR_ALL_NODES_RUNNING = 'The following virtual machines were found ' \
                          'already running'
ERROR_ALREADY_RUNNING = 'Already running'
ERROR_REQUISITE = 'One or more requisite failed'


class StackTaskException(Exception):
    pass


def symlink(source, target):
    '''
    Symlink the given source to the given target
    '''
    if os.path.isfile(target):
        os.remove(target)
    os.symlink(source, target)


def is_state_error(state_meta):
    '''
    Determines if the state resulted in an error.
    '''
    return not state_meta['result']


def is_requisite_error(state_meta):
    '''
    Is the state error because of a requisite state failure?
    '''
    return state_meta['comment'] == ERROR_REQUISITE


def state_to_dict(state_string):
    '''
    Takes the state string and transforms it into a dict of key/value
    pairs that are a bit easier to handle.

    Before: group_|-stackdio_group_|-abe_|-present

    After: {
        'module': 'group',
        'function': 'present',
        'name': 'abe',
        'declaration_id': 'stackdio_group'
    }
    '''
    state_labels = settings.STATE_EXECUTION_FIELDS
    state_fields = state_string.split(settings.STATE_EXECUTION_DELIMITER)
    return dict(zip(state_labels, state_fields))


def is_recoverable(err):
    '''
    Checks the provided error against a blacklist of errors
    determined to be unrecoverable. This should be used to
    prevent retrying of provisioning or orchestration because
    the error will continue to occur.
    '''
    # TODO: determine the blacklist of errors that
    # will trigger a return of False here
    return True


def state_error(state_str, state_meta):
    '''
    Takes the given state result string and the metadata
    of the state execution result and returns a consistent
    dict for the error along with whether or not the error
    is recoverable.
    '''
    state = state_to_dict(state_str)
    func = '{module}.{func}'.format(**state)
    decl_id = state['declaration_id']
    err = {
        'error': state_meta['comment'],
        'function': func,
        'declaration_id': decl_id,
    }
    if 'stderr' in state_meta['changes']:
        err['stderr'] = \
            state_meta['changes']['stderr']
    if 'stdout' in state_meta['changes']:
        err['stdout'] = \
            state_meta['changes']['stdout']
    return err, is_recoverable(err)


@celery.task(name='stacks.handle_error')
def handle_error(stack_id, task_id):
    logger.debug('stack_id: {0}'.format(stack_id))
    logger.debug('task_id: {0}'.format(task_id))
    result = AsyncResult(task_id)
    exc = result.get(propagate=False)
    logger.debug('Task {0} raised exception: {1!r}\n{2!r}'.format(
        task_id, exc, result.traceback))


# TODO: Ignoring code complexity issues for now
@celery.task(name='stacks.launch_hosts')  # NOQA
def launch_hosts(stack_id, parallel=True):
    '''
    Use salt cloud to launch machines using the given stack's map_file
    that was generated when the stack was created. Salt cloud will
    handle launching machines, provisioning them as salt minions,
    connecting to the master, etc. Downstream stack.tasks will
    handle the rest...
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        hosts = stack.get_hosts()

        logger.info('Launching hosts for stack: {0!r}'.format(stack))
        stack.set_status(
            launch_hosts.name,
            'Hosts are being launched. This could take a while.')

        # Set up logging for this launch
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()

        now = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_file = os.path.join(log_dir, '{0}.launch.log'.format(now))
        log_symlink = os.path.join(root_dir, 'launch.log.latest')

        # "touch" the log file and symlink it to the latest
        with open(log_file, 'w') as f:  # NOQA
            pass
        symlink(log_file, log_symlink)

        # Launch stack
        cmd_args = [
            'salt-cloud',
            '-y',                    # assume yes
            '-lquiet',               # no logging on console
            '--log-file {0}',        # where to log
            '--log-file-level debug',  # full logging
            '--out=yaml',            # return YAML formatted results
            '-m {1}',                # the map file to use for launching
            # Until environment variables work
            '--providers-config={2}',
            '--profiles={3}',
            '--cloud-config={4}',
        ]

        # parallize the salt-cloud launch
        if parallel:
            cmd_args.append('-P')
            logger.info('Launching hosts in PARALLEL mode!')
        else:
            logger.info('Launching hosts in SERIAL mode!')

        cmd = ' '.join(cmd_args).format(
            log_file,
            stack.map_file.path,
            settings.STACKDIO_CONFIG.salt_providers_dir,
            settings.STACKDIO_CONFIG.salt_profiles_dir,
            settings.STACKDIO_CONFIG.salt_cloud_config,
        )

        logger.debug('Executing command: {0}'.format(cmd))
        launch_result = envoy.run(str(cmd))
        logger.debug('Command results:')
        logger.debug('status_code = {0}'.format(launch_result.status_code))
        logger.debug('std_out = {0}'.format(launch_result.std_out))
        logger.debug('std_err = {0}'.format(launch_result.std_err))

        # Start verifying hosts were launched and all are available
        try:
            launch_yaml = yaml.safe_load(launch_result.std_out)

            # are all launched hosts accounted for?
            expected_hosts = set([h.hostname for h in hosts])
            launched_hosts = set(launch_yaml.keys())
            unlaunched_hosts = expected_hosts.difference(launched_hosts)

            if unlaunched_hosts:
                err_msg = 'Unlaunched hosts: {0}'.format(
                    ', '.join(unlaunched_hosts))
                stack.set_status(launch_hosts.name, err_msg, Level.ERROR)
                raise StackTaskException(err_msg)

            # grab all the hosts that salt knows about
            cmd = 'salt-run --config-dir={0} manage.present'.format(
                settings.STACKDIO_CONFIG.salt_config_root)
            verify_result = envoy.run(cmd)
            if verify_result.std_out:
                all_hosts = set(yaml.safe_load(verify_result.std_out))
                unavailable_hosts = launched_hosts.difference(all_hosts)

                if unavailable_hosts:
                    err_msg = 'Unavailable hosts: {0}'.format(
                        ', '.join(unavailable_hosts)
                    )
                    stack.set_status(launch_hosts.name, err_msg, Level.ERROR)
                    raise StackTaskException(err_msg)

            # Look for errors if we got valid JSON
            errors = set()
            for h, v in launch_yaml.iteritems():
                logger.debug('Checking host {0} for errors.'.format(h))

                # Error format #1
                if 'Errors' in v and 'Error' in v['Errors']:
                    err_msg = v['Errors']['Error']['Message']
                    logger.debug('Error on host {0}: {1}'.format(h, err_msg))
                    errors.add(err_msg)

                # Error format #2
                elif 'Error' in v:
                    err_msg = v['Error']
                    logger.debug('Error on host {0}: {1}'.format(h, err_msg))
                    errors.add(err_msg)

                # Not exactly error format #3
                #elif 'Message' in v and v['Message'] == ERROR_ALREADY_RUNNING:
                #    err_msg = 'A host with this name already exists.'
                #    logger.debug('Error on host {0}: {1}'.format(h, err_msg))
                #    errors.add(err_msg)

            if errors:
                logger.debug('Errors found!: {0!r}'.format(errors))
                for err_msg in errors:
                    stack.set_status(launch_hosts.name, err_msg, Level.ERROR)
                raise StackTaskException('Error(s) while launching stack '
                                         '{0}'.format(stack_id))
        except Exception, e:
            if isinstance(e, StackTaskException):
                raise
            err_msg = 'Unhandled exception while launching hosts.'
            logger.exception(err_msg)
            raise StackTaskException(err_msg)

        if launch_result.status_code > 0:
            if ERROR_ALL_NODES_EXIST not in launch_result.std_err and \
               ERROR_ALL_NODES_EXIST not in launch_result.std_out and \
               ERROR_ALL_NODES_RUNNING not in launch_result.std_err and \
               ERROR_ALL_NODES_RUNNING not in launch_result.std_out:
                err_msg = launch_result.std_err \
                    if launch_result.std_err else launch_result.std_out
                stack.set_status(launch_hosts.name, err_msg, Level.ERROR)
                raise StackTaskException('Error launching stack {0} with '
                                         'salt-cloud: {1!r}'.format(
                                             stack_id,
                                             err_msg))

        # Seems good...let's set the status and allow other tasks to go through
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


# TODO: Ignoring code complexity issues for now
@celery.task(name='stacks.update_metadata')  # NOQA
def update_metadata(stack_id, host_ids=None, remove_absent=True):
    try:

        # All hosts are running (we hope!) so now we can pull the various
        # metadata and store what we want to keep track of.

        stack = Stack.objects.get(id=stack_id)
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

            #XXX - can't remember what this was for...there's an edge case
            # i'm sure, so leaving this in until I remember
            #if 'state' in host_data \
            #    and host_data['state'] == driver.STATE_TERMINATED:
            #    hosts_to_remove.append(host)
            #    continue

            # FIXME: This is cloud provider specific. Should farm it out to
            # the right implementation

            # host could be "absent" from salt
            if host_data == 'Absent':
                if remove_absent:
                    hosts_to_remove.append(host)
                continue

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

        # for each set of hosts on a provider, use the driver implementation
        # to tag the various infrastructure
        driver_hosts = stack.get_driver_hosts_map()

        for driver, hosts in driver_hosts.iteritems():
            volumes = stack.volumes.filter(host__in=hosts)
            driver.tag_resources(stack, hosts, volumes)

        stack.set_status(tag_infrastructure.name,
                         'Finished tagging stack infrastructure.')

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
        driver_hosts = stack.get_driver_hosts_map()
        for driver, hosts in driver_hosts.iteritems():
            driver.register_dns(hosts)

        stack.set_status(register_dns.name,
                         'Finished registering hosts with DNS provider.')

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


# TODO: Ignoring code complexity issues for now
@celery.task(name='stacks.ping')  # NOQA
def ping(stack_id, timeout=5 * 60, interval=5, max_failures=25):
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
        required_hosts = set([h.hostname for h in stack.get_hosts()])
        stack.set_status(ping.name,
                         'Attempting to ping all hosts.',
                         Level.INFO)

        # Ping
        cmd_args = [
            'salt',
            '--config-dir={0}'.format(
                settings.STACKDIO_CONFIG.salt_config_root),
            '--out=yaml',
            '-G stack_id:{0}'.format(stack_id),  # target the nodes in this
                                                 # stack only
            'test.ping',                         # ping all VMs
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
                    result_yaml = yaml.safe_load(result.std_out)

                    # check that we got a report back for all hosts
                    pinged_hosts = set(result_yaml.keys())
                    missing_hosts = required_hosts.difference(pinged_hosts)
                    if missing_hosts:
                        failures += 1
                        logger.debug('The following hosts did not respond to '
                                     'the ping request: {0}; Total failures: '
                                     '{1}'.format(
                                         missing_hosts,
                                         failures))

                    if result_yaml:
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

        # make sure all hosts reported a successful ping
        false_hosts = []
        for host, value in result_yaml.iteritems():
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
            '--config-dir={0}'.format(
                settings.STACKDIO_CONFIG.salt_config_root),
            '-G stack_id:{0}'.format(stack_id),  # target the nodes in this
                                                 # stack only
            'saltutil.sync_all',                 # sync all systems
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
                                         err_msg))

        stack.set_status(sync_all.name,
                         'Finished synchronizing salt systems on all hosts.')

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


# TODO: Ignoring code complexity issues for now
@celery.task(name='stacks.highstate')  # NOQA
def highstate(stack_id, host_ids=None, max_retries=0):
    '''
    Executes the state.top function using the custom top file generated via
    the stacks.models._generate_top_file. This will only target the 'base'
    environment and core.* states for the stack. These core states are
    purposely separate from others to provision hosts with things that
    stackdio needs.

    TODO: We aren't orchestrating the core states in any way (like the
    stacks.orchestrate task.) They are all executed in the order defined
    by the SLS. I don't see this as a problem right now, but something we
    might have to tackle in the future if someone were to need that.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Running core provisioning for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(highstate.name,
                         'Executing core provisioning. This may take a while.')

        # Set up logging for this task
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()

        # we'll break out of the loop based on the given number of retries
        current_try, unrecoverable_error = 0, False
        while True:
            current_try += 1
            logger.info('Task {0} try #{1} for stack {2!r}'.format(
                highstate.name,
                current_try,
                stack))

            now = datetime.now().strftime('%Y%m%d-%H%M%S')
            log_file = os.path.join(log_dir,
                                    '{0}.provisioning.log'.format(now))
            err_file = os.path.join(log_dir,
                                    '{0}.provisioning.err'.format(now))
            log_symlink = os.path.join(root_dir, 'provisioning.log.latest')
            err_symlink = os.path.join(root_dir, 'provisioning.err.latest')

            # "touch" the log file and symlink it to the latest
            for l in (log_file, err_file):
                with open(l, 'w') as f:
                    pass
            symlink(log_file, log_symlink)
            symlink(err_file, err_symlink)

            ##
            # Execute state.top with custom top file
            ##
            cmd = ' '.join([
                'salt',
                '--config-dir={0}'.format(
                    settings.STACKDIO_CONFIG.salt_config_root),
                '--out=yaml',              # yaml formatted output
                '-G stack_id:{0}',         # target only the vms in this stack
                '--log-file {1}',          # where to log
                '--log-file-level debug',  # full logging
                'state.top',               # run this stack's top file
                stack.top_file.name
            ]).format(
                stack_id,
                log_file
            )

            try:
                # Execute
                logger.debug('Executing command: {0}'.format(cmd))
                result = envoy.run(str(cmd))
            except AttributeError, e:
                # Unrecoverable error, no retrying possible
                err_msg = 'Error running command: \'{0}\''.format(cmd)
                logger.exception(err_msg)
                stack.set_status(highstate.name, err_msg, Level.ERROR)
                raise StackTaskException(err_msg)

            if result is None:
                # What does it mean for envoy to return a result of None?
                # Is it even possible? If so, is it a recoverable error?
                if current_try <= max_retries:
                    continue
                msg = 'Core provisioning command returned None. Status, ' \
                      'stdout and stderr unknown.'
                logger.warn(msg)
                stack.set_status(msg)
            elif result.status_code > 0:
                logger.debug('envoy returned non-zero status code')
                logger.debug('envoy status_code: {0}'.format(
                    result.status_code))
                logger.debug('envoy std_out: {0}'.format(result.std_out))
                logger.debug('envoy std_err: {0}'.format(result.std_err))

                if current_try <= max_retries:
                    continue
                err_msg = result.std_err if result.std_err else result.std_out
                stack.set_status(highstate.name, err_msg, Level.ERROR)
                raise StackTaskException('Error executing core provisioning: '
                                         '{0!r}'.format(err_msg))
            else:
                # dump the output to the log file
                with open(log_file, 'a') as f:
                    f.write(result.std_out)

                # load JSON so we can attempt to catch provisioning errors
                output = yaml.safe_load(result.std_out)

                # each key in the dict is a host, and the value of the host
                # is either a list or dict. Those that are lists we can
                # assume to be a list of errors
                if output is not None:
                    errors = {}
                    for host, states in output.iteritems():
                        if type(states) is list:
                            errors[host] = states
                            continue

                        # iterate over the individual states in the host
                        # looking for state failures
                        for state_str, state_meta in states.iteritems():
                            if not is_state_error(state_meta):
                                continue

                            if not is_requisite_error(state_meta):
                                err, recoverable = state_error(state_str,
                                                               state_meta)
                                if not recoverable:
                                    unrecoverable_error = True
                                errors.setdefault(host, []).append(err)

                    if errors:
                        # write the errors to the err_file
                        with open(err_file, 'a') as f:
                            f.write(yaml.safe_dump(errors))

                        if not unrecoverable_error and current_try <= max_retries: # NOQA
                            continue

                        err_msg = 'Core provisioning errors on hosts: ' \
                            '{0}. Please see the provisioning errors API ' \
                            'or the log file for more details: {1}'.format(
                                ', '.join(errors.keys()),
                                os.path.basename(log_file))
                        stack.set_status(highstate.name,
                                         err_msg,
                                         Level.ERROR)
                        raise StackTaskException(err_msg)

                    # Everything worked?
                    break

        stack.set_status(highstate.name,
                         'Finished core provisioning all hosts.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(highstate.name, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


# TODO: Ignoring code complexity issues
@celery.task(name='stacks.orchestrate') # NOQA
def orchestrate(stack_id, host_ids=None, max_retries=0):
    '''
    Executes the runners.state.over function with the custom overstate
    file  generated via the stacks.models._generate_overstate_file. This
    will only target the user's environment and provision the hosts with
    the formulas defined in the blueprint and in the order specified.

    TODO: We aren't allowing users to provision from formulas owned by
    others at the moment, but if we do want to support that without
    forcing them to clone those formulas into their own account, we
    will need to support executing multiple overstate files in different
    environments.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Executing orchestration for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(orchestrate.name,
                         'Executing orchestration. This may take a while.')

        # Set up logging for this task
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()

        # we'll break out of the loop based on the given number of retries
        current_try, unrecoverable_error = 0, False
        while True:
            current_try += 1
            logger.info('Task {0} try #{1} for stack {2!r}'.format(
                orchestrate.name,
                current_try,
                stack))

            now = datetime.now().strftime('%Y%m%d-%H%M%S')
            log_file = os.path.join(log_dir,
                                    '{0}.orchestration.log'.format(now))
            err_file = os.path.join(log_dir,
                                    '{0}.orchestration.err'.format(now))
            log_symlink = os.path.join(root_dir, 'orchestration.log.latest')
            err_symlink = os.path.join(root_dir, 'orchestration.err.latest')

            for l in (log_file, err_file):
                with open(l, 'w') as f:
                    pass
            symlink(log_file, log_symlink)
            symlink(err_file, err_symlink)

            ##
            # Execute custom orchestration runner
            ##
            cmd = ' '.join([
                'salt-run',
                '--config-dir={0}'.format(
                    settings.STACKDIO_CONFIG.salt_config_root),
                '-lquiet',                  # quiet stdout
                '--log-file {0}',           # where to log
                '--log-file-level debug',   # full logging
                'stackdio.orchestrate',     # custom overstate execution
                stack.owner.username,       # username is the environment to
                                            # execute in
                stack.overstate_file.path
            ]).format(
                log_file
            )

            # Execute
            logger.debug('Executing command: {0}'.format(cmd))

            try:
                result = envoy.run(str(cmd))
            except AttributeError, e:
                # Unrecoverable error, no retrying possible
                err_msg = 'Error running command: \'{0}\''.format(cmd)
                logger.exception(err_msg)
                stack.set_status(orchestrate.name, err_msg, Level.ERROR)
                raise StackTaskException(err_msg)

            if result is None:
                # What does it mean for envoy to return a result of None?
                # Is it even possible? If so, is it a recoverable error?
                if current_try <= max_retries:
                    continue
                msg = 'Orchestration command returned None. Status, stdout ' \
                    'and stderr unknown.'
                logger.warn(msg)
                stack.set_status(msg)
            elif result.status_code > 0:
                logger.debug('envoy returned non-zero status code')
                logger.debug('envoy status_code: {0}'.format(
                    result.status_code))
                logger.debug('envoy std_out: {0}'.format(result.std_out))
                logger.debug('envoy std_err: {0}'.format(result.std_err))

                if current_try <= max_retries:
                    continue

                err_msg = result.std_err \
                    if result.std_err else result.std_out
                stack.set_status(orchestrate.name, err_msg, Level.ERROR)
                raise StackTaskException('Error executing orchestration: '
                                         '{0!r}'.format(err_msg))
            else:
                with open(log_file, 'a') as f:
                    f.write(result.std_out)

                # load JSON so we can attempt to catch provisioning errors
                output = yaml.safe_load(result.std_out)

                # each key in the dict is a host, and the value of the host
                # is either a list or dict. Those that are lists we can
                # assume to be a list of errors
                if output is not None:
                    errors = {}

                    for host, stage_results in output.iteritems():
                        # check for orchestration stage errors first
                        if host == '__stage__error__':
                            continue

                        for stage_result in stage_results:

                            if isinstance(stage_result, list):
                                for err in stage_result:
                                    errors.setdefault(host, []) \
                                        .append({
                                            'error': err
                                        })
                                continue

                            # iterate over the individual states in the
                            # host looking for states that had a result
                            # of false
                            for state_str, state_meta in stage_result.iteritems(): # NOQA
                                if not is_state_error(state_meta):
                                    continue

                                if not is_requisite_error(state_meta):
                                    err, recoverable = state_error(state_str,
                                                                   state_meta)
                                    if not recoverable:
                                        unrecoverable_error = True
                                    errors.setdefault(host, []).append(err)

                    if errors:
                        # write the errors to the err_file
                        with open(err_file, 'a') as f:
                            f.write(yaml.safe_dump(errors))

                        if not unrecoverable_error and current_try <= max_retries: # NOQA
                            continue

                        err_msg = 'Orchestration errors on hosts: ' \
                            '{0}. Please see the orchestration errors ' \
                            'API or the orchestration log file for more ' \
                            'details: {1}'.format(
                                ', '.join(errors.keys()),
                                os.path.basename(log_file))
                        stack.set_status(highstate.name,
                                         err_msg,
                                         Level.ERROR)
                        raise StackTaskException(err_msg)

                    # Everything worked?
                    break

        stack.set_status(orchestrate.name,
                         'Finished executing orchestration all hosts.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(orchestrate.name, err_msg, Level.ERROR)
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
        stack.set_status(finish_stack.name,
                         'Registering volumes for deletion.')

        hosts = stack.get_hosts(host_ids)
        if not hosts:
            return

        # use the stack driver to register all volumes on the hosts to
        # automatically delete after the host is terminated
        driver_hosts = stack.get_driver_hosts_map()
        for driver, hosts in driver_hosts.iteritems():
            driver.register_volumes_for_delete(hosts)

        stack.set_status(finish_stack.name,
                         'Finished registering volumes for deletion.')

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


# TODO: Ignoring code complexity issues for now
@celery.task(name='stacks.destroy_hosts') # NOQA
def destroy_hosts(stack_id, host_ids=None, delete_stack=True, parallel=True):
    '''
    Destroy the given stack id or a subset of the stack if host_ids
    is set. After all hosts have been destroyed we must also clean
    up any managed security groups on the stack.
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        stack.set_status(destroy_hosts.name,
                         'Destroying stack infrastructure. This could '
                         'take a while.')
        hosts = stack.get_hosts(host_ids)

        # Build up the salt-cloud command
        cmd_args = [
            'salt-cloud',
            '-y',                   # assume yes
            '-d',                   # destroy argument
            '--out=yaml',           # output in JSON
        ]

        if parallel:
            cmd_args.append('-P')

        # if host ids are given, we're going to terminate only those hosts
        if host_ids:
            logger.info('Destroying hosts {0!r} on stack {1!r}'.format(
                hosts,
                stack
            ))

            # add the machines to destroy on to the cmd_args list
            cmd_args.extend([h.hostname for h in hosts])

        # or we'll destroy the entire stack by giving the map file with all
        # hosts defined
        else:
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

        # Until environment variables work
        cmd_args.extend([
            '--providers-config={0}',
            '--profiles={1}',
            '--cloud-config={2}'
        ])

        cmd = ' '.join(cmd_args).format(
            settings.STACKDIO_CONFIG.salt_providers_dir,
            settings.STACKDIO_CONFIG.salt_profiles_dir,
            settings.STACKDIO_CONFIG.salt_cloud_config,
        )

        logger.debug('Executing command: {0}'.format(cmd))
        result = envoy.run(str(cmd))
        logger.debug('Command results:')
        logger.debug('status_code = {0}'.format(result.status_code))
        logger.debug('std_out = {0}'.format(result.std_out))
        logger.debug('std_err = {0}'.format(result.std_err))

        if result.status_code > 0:
            err_msg = result.std_err if result.std_err else result.std_out
            stack.set_status(destroy_hosts.name, err_msg, Stack.ERROR)
            raise StackTaskException('Error destroying hosts on stack {0}: '
                                     '{1!r}'.format(
                                         stack_id,
                                         err_msg))

        # wait for all hosts to finish terminating so we can
        # destroy security groups
        driver_hosts = stack.get_driver_hosts_map()
        security_groups = set()
        for driver, hosts in driver_hosts.iteritems():
            security_groups.update(SecurityGroup.objects.filter(
                hosts__in=hosts,
                owner=stack.owner))

            known_hosts = hosts.exclude(instance_id='')
            if known_hosts:
                ok, result = driver.wait_for_state(known_hosts,
                                                   driver.STATE_TERMINATED)
                if not ok:
                    stack.set_status(destroy_hosts.name, result, Stack.ERROR)
                    raise StackTaskException(result)
                known_hosts.update(instance_id='', state='terminated')

        if delete_stack:
            for security_group in security_groups:
                try:
                    driver.delete_security_group(security_group.name)
                except BadRequest, e:
                    if 'does not exist' in e.message:
                        logger.warn(e.message)
                    else:
                        raise
                security_group.delete()

        # delete hosts
        if delete_stack:
            hosts.delete()

        stack.set_status(destroy_hosts.name,
                         'Finished destroying stack infrastructure.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException, e:
        raise
    except Exception, e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(destroy_hosts.name, err_msg, level=Stack.ERROR)
        logger.exception(err_msg)
        raise


@celery.task(name='stacks.destroy_stack')
def destroy_stack(stack_id):
    '''
    '''
    try:
        stack = Stack.objects.get(id=stack_id)
        stack.set_status(destroy_stack.name,
                         'Performing final cleanup of stack.')
        hosts = stack.get_hosts()

        if hosts.count() > 0:
            stack.set_status(destroy_stack.name,
                             'Stack appears to have hosts attached and '
                             'can\'t be completely destroyed.',
                             level=Stack.ERROR)
        else:
            # delete the stack storage directory
            shutil.rmtree(stack.get_root_directory())
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
        driver_hosts = stack.get_driver_hosts_map()
        for driver, hosts in driver_hosts.iteritems():
            driver.unregister_dns(hosts)

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
        driver_hosts_map = stack.get_driver_hosts_map()
        for driver, hosts in driver_hosts_map.iteritems():
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
