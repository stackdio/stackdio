# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime

import salt.client
import salt.cloud
import salt.config
import salt.runner
import six
import yaml
from celery import shared_task
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from django.conf import settings

from stackdio.api.cloud.models import SecurityGroup
from stackdio.api.cloud.providers.base import DeleteGroupException
from stackdio.api.formulas.models import FormulaVersion
from stackdio.api.formulas.tasks import update_formula
from stackdio.api.volumes.models import Volume
from . import utils
from .models import (
    Stack,
    Level,
    StackCommand,
    Host,
)

logger = get_task_logger(__name__)

root_logger = logging.getLogger()

ERROR_ALL_NODES_EXIST = 'All nodes in this map already exist'
ERROR_ALL_NODES_RUNNING = 'The following virtual machines were found ' \
                          'already running'
ERROR_ALREADY_RUNNING = 'Already running'


class StackTaskException(Exception):
    pass


def symlink(source, target):
    """
    Symlink the given source to the given target
    """
    if os.path.islink(target):
        os.remove(target)
    os.symlink(source, target)


def is_state_error(state_meta):
    """
    Determines if the state resulted in an error.
    """
    return not state_meta['result']


def copy_formulas(stack_or_account):
    dest_dir = os.path.join(stack_or_account.get_root_directory(), 'formulas')

    # Be sure to create a formula version for all formulas needed
    for formula in stack_or_account.get_formulas():
        try:
            # Try to the version if it exists
            stack_or_account.formula_versions.get(formula=formula)
        except FormulaVersion.DoesNotExist:
            # Default to the head branch
            stack_or_account.formula_versions.create(formula=formula,
                                                     version=formula.default_version)

    for formula_version in stack_or_account.formula_versions.all():
        formula = formula_version.formula
        version = formula_version.version

        formula_dir = os.path.join(dest_dir, formula.get_repo_name())

        # Blow away the private repo and re-copy.  This way we get the most recent states
        # that have been updated
        if formula.private_git_repo and os.path.exists(formula_dir):
            shutil.rmtree(formula_dir)

        if not os.path.isdir(formula_dir):
            # Copy over the formula - but just bail if it already exists
            shutil.copytree(formula.get_repo_dir(), formula_dir)
        else:
            logger.debug('Formula not copied, already exists: {0}'.format(formula.uri))

        if formula.private_git_repo:
            # If it's private, we can't update it but we can at least checkout the right branch
            if formula.repo is not None:
                formula.repo.git.checkout(version)
            logger.debug('Skipping update of private formula: {0}'.format(formula.uri))
            continue

        # Update the formula
        update_formula.si(formula.id, None, version, formula_dir, raise_exception=False)()


def copy_global_orchestrate(stack):
    stack.generate_global_orchestrate_file()

    src_file = stack.global_orchestrate_file.path

    accounts = set([host.cloud_image.account for host in stack.hosts.all()])

    for account in accounts:
        dest_dir = os.path.join(account.get_root_directory(), 'formulas', '__stackdio__')

        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir, 0o755)

        shutil.copyfile(src_file, '{0}/stack_{1}_global_orchestrate.sls'.format(dest_dir, stack.id))


@shared_task(name='stacks.handle_error')
def handle_error(stack_id, task_id):
    logger.debug('stack_id: {0}'.format(stack_id))
    logger.debug('task_id: {0}'.format(task_id))
    result = AsyncResult(task_id)
    exc = result.get(propagate=False)
    logger.debug('Task {0} raised exception: {1!r}\n{2!r}'.format(
        task_id, exc, result.traceback))


# TODO: Ignoring code complexity issues for now
@shared_task(name='stacks.launch_hosts')
def launch_hosts(stack_id, parallel=True, max_retries=2,
                 simulate_launch_failures=False, simulate_zombies=False,
                 simulate_ssh_failures=False, failure_percent=0.3):
    """
    Uses salt cloud to launch machines using the given Stack's map_file
    that was generated when the Stack was created. Salt cloud will
    handle launching machines, provisioning them as salt minions,
    connecting to the master, etc. Downstream tasks will
    handle the rest of the operational details.

    @param stack_id (int) - the primary key of the stack to launch
    @param parallel (bool) - if True, salt-cloud will launch the stack
        in parallel using multiprocessing.
    @param max_retries (int) - the number of retries to use if launch
        failures are detected.

    Failure simulations:
    @param simulate_launch_failures (bool) - if True, will modify the stack's
        map file to set a new `private_key` parameter that does not actually
        exist. This causes salt-cloud to bail out when launching the host,
        and then retry logic will kick in. After a launch attempt, this flag
        is removed.
    @param simulate_ssh_failures (bool) - if True, we will modify the map file
        to use an existing, yet invalid SSH key, causing SSH failures in
        salt-cloud during any SSH auth attempts. After launch, we clean this
        modification up so subsequent launches do not intentionally fail.
    @param simulate_zombies (bool) - if True, after a successful launch of
        hosts, we will manually kill salt-minion service on a random subset of
        the stack's hosts. This task doesn't actually attempt to fix zombie
        hosts, but we will in the `cure_zombies` task later.
    @param failure_percent (float) - percentage of the Stack's hosts to be
        flagged to fail during launch or become zombie hosts. This param
        is ignored if all of the above failure flags are set to False.
        Defaults to 0.3 (30%).
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        hosts = stack.get_hosts()
        num_hosts = len(hosts)
        log_file = utils.get_salt_cloud_log_file(stack, 'launch')

        # Generate the pillar file.  We need it!
        stack.generate_pillar_file(update_formulas=True)

        logger.info('Launching hosts for stack: {0!r}'.format(stack))
        logger.info('Log file: {0}'.format(log_file))

        salt_cloud = utils.StackdioSaltCloudClient(settings.STACKDIO_CONFIG.salt_cloud_config)
        query = salt_cloud.query()

        hostnames = [host.hostname for host in hosts]

        # Since a blueprint can have multiple accounts
        accounts = set()
        for host in hosts:
            accounts.add(host.cloud_image.account)

        for account in accounts:
            provider = account.provider.name

            for instance, details in query.get(account.slug, {}).get(provider, {}).items():
                if instance in hostnames:
                    if details['state'] in ('shutting-down', 'terminated'):
                        salt_cloud.action(
                            'set_tags',
                            names=[instance],
                            kwargs={
                                'Name': '{0}-DEL_BY_STACKDIO'.format(instance)
                            }
                        )

        current_try, unrecoverable_error = 0, False
        while True:
            current_try += 1
            logger.info('Task {0} try {1} of {2} for stack {3!r}'.format(
                launch_hosts.name,
                current_try,
                max_retries + 1,
                stack))

            if num_hosts > 1:
                label = '{0} hosts are'.format(num_hosts)
            else:
                label = '1 host is'

            stack.set_status(
                launch_hosts.name,
                Stack.LAUNCHING,
                '{0} being launched. Try {1} of {2}. '
                'This may take a while.'.format(
                    label,
                    current_try,
                    max_retries + 1))

            cloud_map = stack.generate_cloud_map()

            # Modify the stack's map to inject a private key that does not
            # exist, which will fail immediately and the host will not launch
            if simulate_launch_failures:
                n = int(len(hosts) * failure_percent)
                logger.info('Simulating failures on {0} host(s).'.format(n))
                utils.mod_hosts_map(cloud_map, n, private_key='/tmp/bogus-key-file')

            # Modify the map file to inject a real key file, but one that
            # will not auth via SSH
            if not simulate_launch_failures and simulate_ssh_failures:
                bogus_key = '/tmp/id_rsa-bogus-key'
                if os.path.isfile(bogus_key):
                    os.remove(bogus_key)
                subprocess.call(['ssh-keygen', '-f', bogus_key, '-N', ''])
                n = int(len(hosts) * failure_percent)
                logger.info('Simulating SSH failures on {0} host(s).'.format(n))
                utils.mod_hosts_map(cloud_map, n, private_key=bogus_key)

            if parallel:
                logger.info('Launching hosts in PARALLEL mode.')
            else:
                logger.info('Launching hosts in SERIAL mode.')

            # Launch everything!
            launch_result = salt_cloud.launch_map(
                cloud_map=cloud_map,
                parallel=parallel,
                log_level='quiet',
                log_file=log_file,
                log_level_logfile='debug'
            )

            if not launch_result:
                # This means nothing was launched b/c everything is already running
                break

            # Remove the failure modifications if necessary
            if simulate_launch_failures:
                simulate_launch_failures = False

            # Start verifying hosts were launched and all are available
            try:
                # Check for launch failures...a couple things happen here:
                #
                # 1) We'll query salt-cloud looking for hosts that salt
                # believes need to be created. This indicates that the
                # host never came online, so we'll just retry and attempt
                # to launch those hosts again; and
                #
                # 2) We'll look for zombie hosts check for a successful
                # SSH connection. If we couldn't connect via SSH then we'll
                # consider this a launch failure, terminate the machine and
                # let salt relaunch them

                # First we'll attempt to SSH to all zombie nodes and terminate
                # the unsuccessful ones so we can relaunch them
                zombies = utils.find_zombie_hosts(stack)
                terminate_list = []
                if zombies is not None and zombies.count() > 0:
                    check_ssh_results = utils.check_for_ssh(cloud_map, zombies)
                    if check_ssh_results:
                        for ssh_ok, host in check_ssh_results:
                            if not ssh_ok:
                                # build the list of hosts we need to kill
                                # and relaunch
                                terminate_list.append(host)

                        n = len(terminate_list)
                        if n > 0:
                            label = '{0} host'.format(n)
                            if n > 1:
                                label += 's were'
                            else:
                                label += ' was'

                            err_msg = (
                                '{0} unresponsive and will be terminated '
                                'and tried again.'.format(label))
                            logger.debug(err_msg)
                            stack.set_status(
                                launch_hosts.name,
                                Stack.LAUNCHING,
                                err_msg,
                                Level.WARN)

                            # terminate the unresponsive zombie hosts
                            utils.terminate_hosts(stack, terminate_list)

                # Revert SSH failure simulation after we've found the SSH
                # issues and terminated the hosts
                if simulate_ssh_failures:
                    logger.debug('Reverting SSH failure simulation '
                                 'modifications.')
                    utils.unmod_hosts_map(cloud_map,
                                          'private_key')
                    simulate_ssh_failures = False

                # The map data structure gives us the list of hosts that
                # salt believes need to be created. This also includes any
                # unresponsive zombie hosts we just terminated. Note that
                # we don't have to actually wait for those hosts to die
                # because salt-cloud renames them and will not consider
                # them available.
                dmap = utils.get_stack_map_data(cloud_map)

                if 'create' in dmap and len(dmap['create']) > 0:
                    failed_hosts = dmap['create'].keys()

                    # reset number of hosts we think we are launching
                    num_hosts = len(failed_hosts)
                    label = '{0} host'.format(num_hosts)
                    if num_hosts > 1:
                        label += 's'

                    logger.debug('VMs failed to launch: {0}'.format(
                        failed_hosts
                    ))

                    if current_try <= max_retries:
                        stack.set_status(launch_hosts.name,
                                         Stack.LAUNCHING,
                                         '{0} failed to launch and '
                                         'will be retried.'.format(label),
                                         Level.WARN)
                        continue

                    else:
                        # Max tries reached...unrecoverable failure.
                        err_msg = ('{0} failed to launch and the '
                                   'maximum number of tries have been '
                                   'reached.'.format(label))
                        stack.set_status(launch_hosts.name,
                                         Stack.ERROR,
                                         err_msg,
                                         Level.ERROR)
                        raise StackTaskException(err_msg)

                # Simulating zombies is a bit more work than just modifying the
                # stacks' map file. At this point we assume hosts are up and
                # functional, so we simply need to disable the salt-minion
                # service on some of the hosts.
                if simulate_zombies:
                    n = int(len(hosts) * failure_percent)
                    logger.info('Simulating zombies on {0} host(s).'.format(n))
                    utils.create_zombies(stack, n)

                # Look for errors if we got valid JSON
                errors = set()
                for h, v in launch_result.items():
                    logger.debug('Checking host {0} for errors.'.format(h))

                    # Error format #1
                    if 'Errors' in v and 'Error' in v['Errors']:
                        err_msg = v['Errors']['Error']['Message']
                        logger.debug('Error on host {0}: {1}'.format(
                            h,
                            err_msg)
                        )
                        errors.add(err_msg)

                    # Error format #2
                    elif 'Error' in v:
                        err_msg = v['Error']
                        logger.debug('Error on host {0}: {1}'.format(
                            h,
                            err_msg))
                        errors.add(err_msg)

                if errors:
                    logger.debug('Errors found!: {0!r}'.format(errors))

                    if not unrecoverable_error and current_try <= max_retries:
                        continue

                    for err_msg in errors:
                        stack.set_status(launch_hosts.name,
                                         Stack.ERROR,
                                         err_msg,
                                         Level.ERROR)
                    raise StackTaskException('Error(s) while launching stack '
                                             '{0}'.format(stack_id))

                # Everything worked?
                break

            except Exception as e:
                if isinstance(e, StackTaskException):
                    raise
                err_msg = 'Unhandled exception while launching hosts.'
                logger.exception(err_msg)
                raise StackTaskException(err_msg)

        # Seems good...let's set the status and allow other tasks to
        # go through
        stack.set_status(launch_hosts.name, Stack.FINISHED, 'Finished launching hosts.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown stack id {0}'.format(stack_id)
        logger.exception(err_msg)
        raise StackTaskException(err_msg)
    except StackTaskException as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(launch_hosts.name, stack.ERROR, err_msg, Level.ERROR)
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(launch_hosts.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


# TODO: Ignoring code complexity issues for now
@shared_task(name='stacks.cure_zombies')
def cure_zombies(stack_id, max_retries=2):
    """
    Attempts to detect zombie hosts, or those hosts in the stack that are
    up and running but are failing to be pinged. This usually means that
    the bootstrapping process failed or went wrong. To fix this, we will
    try to rerun the bootstrap process to get the zombie hosts to sync
    up with the master.

    @ param stack_id (int) -
    @ param max_retries (int) -
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)

        current_try = 0
        while True:
            current_try += 1

            # Attempt to find zombie hosts
            zombies = utils.find_zombie_hosts(stack)

            if zombies is None or zombies.count() == 0:
                break

            n = len(zombies)
            label = '{0} zombie host'.format(n)
            if n > 1:
                label += 's'

            if current_try <= max_retries + 1:
                logger.info('Zombies found: {0}'.format(zombies))
                logger.info('Zombie bootstrap try {0} of {1}'.format(
                    current_try,
                    max_retries + 1))

                # If we have some zombie hosts, we'll attempt to bootstrap
                # them again, up to the max retries
                stack.set_status(
                    launch_hosts.name,
                    Stack.LAUNCHING,
                    '{0} detected. Attempting try {1} of {2} to '
                    'bootstrap. This may take a while.'
                    ''.format(
                        label,
                        current_try,
                        max_retries + 1),
                    Level.WARN)
                utils.bootstrap_hosts(
                    stack,
                    zombies,
                    parallel=True
                )
                continue
            else:
                err_msg = (
                    '{0} detected and the maximum number of '
                    'tries have been reached.'.format(label)
                )
                stack.set_status(
                    launch_hosts.name,
                    Stack.ERROR,
                    err_msg,
                    Level.ERROR
                )
                raise StackTaskException(err_msg)

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(cure_zombies.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


# TODO: Ignoring code complexity issues for now
@shared_task(name='stacks.update_metadata')
def update_metadata(stack_id, host_ids=None, remove_absent=True):
    stack = None
    try:
        # All hosts are running (we hope!) so now we can pull the various
        # metadata and store what we want to keep track of.

        stack = Stack.objects.get(id=stack_id)
        logger.info('Updating metadata for stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(update_metadata.name,
                         Stack.CONFIGURING,
                         'Collecting host metadata from cloud provider.')

        # Use salt-cloud to look up host information we need now that
        # the machines are running
        query_results = stack.query_hosts(force=True)

        # keep track of terminated hosts for future removal
        hosts_to_remove = []

        driver_hosts = stack.get_driver_hosts_map(host_ids)

        for driver, hosts in driver_hosts.items():
            bad_states = (driver.STATE_TERMINATED,
                          driver.STATE_SHUTTING_DOWN)

            for host in hosts:
                logger.debug('Updating metadata for host {0}'.format(host))

                # FIXME: This is cloud provider specific. Should farm it out to
                # the right implementation
                host_data = query_results.get(host.hostname)
                is_absent = host_data is None

                if isinstance(host_data, six.string_types):
                    raise TypeError('Expected dict, received {0}'.format(type(host_data)))

                # Check for terminated host state
                if is_absent or ('state' in host_data and host_data['state'] in bad_states):
                    if is_absent and remove_absent:
                        hosts_to_remove.append(host)
                        continue

                    # udpate relevant metadata
                    host.instance_id = ''
                    host.sir_id = 'NA'

                    host.state = 'Absent' if is_absent else host_data['state']

                    # if AWS gives a reason, save it with the host
                    if not is_absent:
                        state_reason = host_data \
                            .get('stateReason', {}) \
                            .get('message', None)
                        if state_reason:
                            host.state_reason = state_reason
                    host.save()
                    continue

                # The instance id of the host
                host.instance_id = host_data['instanceId']

                # Get the host's public IP/host set by the cloud provider. This
                # is used later when we tie the machine to DNS
                host.provider_dns = host_data.get('dnsName', '') or ''
                host.provider_private_dns = host_data.get('privateDnsName', '') or ''

                # If the instance is stopped, 'privateIpAddress' isn't in the returned dict, so this
                # throws an exception if we don't use host_data.get().  I changed the above two
                # keys to do the same for robustness
                host.provider_private_ip = host_data.get('privateIpAddress', '') or ''

                # update the state of the host as provided by ec2
                if host.state != Host.DELETING:
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

                    except Volume.DoesNotExist:
                        # This is most likely fine. Usually means that the
                        # EBS volume for the root drive was found instead.
                        pass
                    except Exception:
                        err_msg = ('Unhandled exception while updating volume '
                                   'metadata.')
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

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(update_metadata.name, Stack.ERROR,
                         err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.tag_infrastructure')
def tag_infrastructure(stack_id, host_ids=None, change_status=True):
    """
    Tags hosts and volumes with certain metadata that should prove useful
    to anyone using the AWS console.

    ORDER MATTERS! Make sure that tagging only comes after you've executed
    the `update_metadata` task as that task actually pulls in information
    we need to use the tagging API effectively.
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)

        logger.info('Tagging infrastructure for stack: {0!r}'.format(stack))

        # Update status
        if change_status:
            stack.set_status(tag_infrastructure.name, Stack.CONFIGURING,
                             'Tagging stack infrastructure.')

        # for each set of hosts on an account, use the driver implementation
        # to tag the various infrastructure
        driver_hosts = stack.get_driver_hosts_map(host_ids)

        for driver, hosts in driver_hosts.items():
            volumes = stack.volumes.filter(host__in=hosts)
            driver.tag_resources(stack, hosts, volumes)

        if change_status:
            stack.set_status(tag_infrastructure.name, Stack.CONFIGURING,
                             'Finished tagging stack infrastructure.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(tag_infrastructure.name, Stack.ERROR,
                         err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.register_dns')
def register_dns(stack_id, host_ids=None):
    """
    Must be ran after a Stack is up and running and all host information has
    been pulled and stored in the database.
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Registering DNS for stack: {0!r}'.format(stack))

        stack.set_status(register_dns.name, Stack.CONFIGURING,
                         'Registering hosts with DNS provider.')

        # Use the provider implementation to register a set of hosts
        # with the appropriate cloud's DNS service
        driver_hosts = stack.get_driver_hosts_map(host_ids)
        for driver, hosts in driver_hosts.items():
            driver.register_dns(hosts)

        stack.set_status(register_dns.name, Stack.CONFIGURING,
                         'Finished registering hosts with DNS provider.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(register_dns.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


# TODO: Ignoring code complexity issues for now
@shared_task(name='stacks.ping')
def ping(stack_id, interval=5, max_failures=10):
    """
    Attempts to use salt's test.ping module to ping the entire stack
    and confirm that all hosts are reachable by salt.

    @stack_id: The id of the stack to ping. We will use salt's grain
               system to target the hosts with this stack id
    @interval: The looping interval, ie, the amount of time to sleep
               before the next iteration.
    @max_failures: Number of ping failures before giving up completely.
                   The timeout does not affect this parameter.
    @raises StackTaskException
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        required_hosts = [h.hostname for h in stack.get_hosts()]
        stack.set_status(ping.name,
                         Stack.CONFIGURING,
                         'Attempting to ping all hosts.',
                         Level.INFO)

        client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

        # Execute until successful, failing after a few attempts
        failures = 0

        false_hosts = []

        while True:
            ret = client.cmd_iter(required_hosts, 'test.ping', expr_form='list')

            result = {}
            for res in ret:
                for host, data in res.items():
                    result[host] = data

            # check that we got a report back for all hosts
            pinged_hosts = set(result.keys())
            missing_hosts = set(required_hosts).difference(pinged_hosts)
            if missing_hosts:
                failures += 1
                logger.debug('The following hosts did not respond to '
                             'the ping request: {0}; Total failures: '
                             '{1}'.format(missing_hosts,
                                          failures))

            false_hosts = []
            for host, data in result.items():
                if data['ret'] is not True or data['retcode'] != 0:
                    failures += 1
                    false_hosts.append(host)

            if not missing_hosts and not false_hosts:
                # Successful ping.
                break

            if failures > max_failures:
                err_msg = 'Max failures ({0}) reached while pinging ' \
                          'hosts.'.format(max_failures)
                stack.set_status(ping.name, Stack.ERROR, err_msg, Level.ERROR)
                raise StackTaskException(err_msg)

            time.sleep(interval)

        if false_hosts:
            err_msg = 'Unable to ping hosts: {0}'.format(', '.join(false_hosts))
            stack.set_status(ping.name, Stack.ERROR, err_msg, Level.ERROR)
            raise StackTaskException(err_msg)

        stack.set_status(ping.name, Stack.CONFIGURING,
                         'All hosts pinged successfully.',
                         Level.INFO)

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(ping.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.sync_all')
def sync_all(stack_id):
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Syncing all salt systems for stack: {0!r}'.format(stack))

        # Generate all the files before we sync
        stack.generate_pillar_file(update_formulas=True)
        stack.generate_global_pillar_file(update_formulas=True)
        stack.generate_top_file()
        stack.generate_orchestrate_file()
        stack.generate_global_orchestrate_file()

        # Update status
        stack.set_status(sync_all.name, Stack.SYNCING,
                         'Synchronizing salt systems on all hosts.')

        target = [h.hostname for h in stack.get_hosts()]
        client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

        ret = client.cmd_iter(target, 'saltutil.sync_all', expr_form='list')

        result = {}
        for res in ret:
            for host, data in res.items():
                result[host] = data

        for host, data in result.items():
            if 'retcode' not in data:
                logger.warning('Host {0} missing a retcode... assuming failure'.format(host))

            if data.get('retcode', 1) != 0:
                err_msg = str(data['ret'])
                stack.set_status(sync_all.name, Stack.ERROR, err_msg, Level.ERROR)
                raise StackTaskException('Error syncing salt data on stack {0}: '
                                         '{1!r}'.format(stack_id,
                                                        err_msg))

        stack.set_status(sync_all.name, Stack.CONFIGURING,
                         'Finished synchronizing salt systems on all hosts.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(sync_all.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


def change_pillar(stack, new_pillar_file):
    salt_client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

    target = [h.hostname for h in stack.get_hosts()]

    # From the testing I've done, this also automatically refreshes the pillar
    ret = salt_client.cmd_iter(
        target,
        'grains.setval',
        [
            'stack_pillar_file',
            new_pillar_file
        ],
        expr_form='list',
    )

    # TODO Want to do error checking, but don't know what errors look
    result = {}

    for res in ret:
        for minion, state_ret in res.items():
            result[minion] = state_ret


# TODO: Ignoring code complexity issues for now
@shared_task(name='stacks.highstate')
def highstate(stack_id, max_retries=2):
    """
    Executes the state.top function using the custom top file generated via
    the stacks.models._generate_top_file. This will only target the 'base'
    environment and core.* states for the stack. These core states are
    purposely separate from others to provision hosts with things that
    stackdio needs.

    TODO: We aren't orchestrating the core states in any way (like the
    stacks.orchestrate task.) They are all executed in the order defined
    by the SLS. I don't see this as a problem right now, but something we
    might have to tackle in the future if someone were to need that.
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        num_hosts = len(stack.get_hosts())
        target = [h.hostname for h in stack.get_hosts()]
        logger.info('Running core provisioning for stack: {0!r}'.format(stack))

        # Make sure the pillar is properly set
        change_pillar(stack, stack.pillar_file.path)

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

            # Update status
            stack.set_status(highstate.name, Stack.PROVISIONING,
                             'Executing core provisioning try {0} of {1}. '
                             'This may take a while.'.format(
                                 current_try,
                                 max_retries + 1))

            now = datetime.now().strftime('%Y%m%d-%H%M%S')
            log_file = os.path.join(log_dir,
                                    '{0}.provisioning.log'.format(now))
            err_file = os.path.join(log_dir,
                                    '{0}.provisioning.err'.format(now))
            log_symlink = os.path.join(root_dir, 'provisioning.log.latest')
            err_symlink = os.path.join(root_dir, 'provisioning.err.latest')

            # "touch" the log file and symlink it to the latest
            for l in (log_file, err_file):
                with open(l, 'w') as _:
                    pass
            symlink(log_file, log_symlink)
            symlink(err_file, err_symlink)

            file_log_handler = utils.setup_logfile_logger(log_file)

            # Remove the other handlers, but save them so we can put them back later
            old_handlers = []
            for handler in root_logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    old_handlers.append(handler)
                    root_logger.removeHandler(handler)

            # Put this in a try block so the handler always gets cleaned up
            try:
                salt_client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

                ret = salt_client.cmd_iter(
                    target,
                    'state.top',
                    [stack.top_file.name],
                    expr_form='list'
                )

                result = {}
                # cmd_iter returns a generator that blocks until jobs finish, so
                # we want to loop through it until the jobs are done
                for i in ret:
                    for k, v in i.items():
                        result[k] = v['ret']

            finally:
                root_logger.removeHandler(file_log_handler)
                for handler in old_handlers:
                    root_logger.addHandler(handler)

            with open(log_file, 'a') as f:
                f.write(yaml.safe_dump(result))

            if len(result) != num_hosts:
                logger.debug('salt did not provision all hosts')
                if current_try <= max_retries:
                    continue
                err_msg = 'Salt errored and did not provision all the hosts'
                stack.set_status(highstate.name, Stack.ERROR,
                                 err_msg, Level.ERROR)
                raise StackTaskException('Error executing core provisioning: '
                                         '{0!r}'.format(err_msg))

            else:
                # each key in the dict is a host, and the value of the host
                # is either a list or dict. Those that are lists we can
                # assume to be a list of errors
                errors = {}
                for host, states in result.items():
                    if not isinstance(states, dict):
                        errors[host] = states
                        continue

                    # iterate over the individual states in the host
                    # looking for state failures
                    for state_str, state_meta in states.items():
                        if not is_state_error(state_meta):
                            continue

                        if not utils.is_requisite_error(state_meta):
                            err, recoverable = utils.state_error(state_str, state_meta)
                            if not recoverable:
                                unrecoverable_error = True
                            errors.setdefault(host, []).append(err)

                if errors:
                    # write the errors to the err_file
                    with open(err_file, 'a') as f:
                        f.write(yaml.safe_dump(errors))

                    if not unrecoverable_error and current_try <= max_retries:
                        continue

                    err_msg = 'Core provisioning errors on hosts: ' \
                              '{0}. Please see the provisioning errors API ' \
                              'or the log file for more details: {1}'.format(
                                  ', '.join(errors.keys()),
                                  os.path.basename(log_file))
                    stack.set_status(highstate.name,
                                     Stack.ERROR,
                                     err_msg,
                                     Level.ERROR)
                    raise StackTaskException(err_msg)

                # Everything worked?
                break

        stack.set_status(highstate.name, Stack.PROVISIONING,
                         'Finished core provisioning all hosts.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(highstate.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.propagate_ssh')
def propagate_ssh(stack_id, max_retries=2):
    """
    Similar to stacks.highstate, except we only run `core.stackdio_users`
    instead of `core.*`.  This is useful so that ssh keys can be added to
    hosts without having to completely re run provisioning.
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        target = [h.hostname for h in stack.get_hosts()]
        # Regenerate the stack pillar file
        stack.generate_pillar_file(update_formulas=True)
        num_hosts = len(stack.get_hosts())
        logger.info('Propagating ssh keys on stack: {0!r}'.format(stack))

        # Make sure the pillar is properly set
        change_pillar(stack, stack.pillar_file.path)

        # Set up logging for this task
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()

        # we'll break out of the loop based on the given number of retries
        current_try, unrecoverable_error = 0, False
        while True:
            current_try += 1
            logger.info('Task {0} try #{1} for stack {2!r}'.format(
                propagate_ssh.name,
                current_try,
                stack))

            # Update status
            stack.set_status(propagate_ssh.name, Stack.PROVISIONING,
                             'Propagating ssh try {0} of {1}. '
                             'This may take a while.'.format(
                                 current_try,
                                 max_retries + 1))

            now = datetime.now().strftime('%Y%m%d-%H%M%S')
            log_file = os.path.join(log_dir,
                                    '{0}.provisioning.log'.format(now))
            err_file = os.path.join(log_dir,
                                    '{0}.provisioning.err'.format(now))
            log_symlink = os.path.join(root_dir, 'provisioning.log.latest')
            err_symlink = os.path.join(root_dir, 'provisioning.err.latest')

            # "touch" the log file and symlink it to the latest
            for l in (log_file, err_file):
                with open(l, 'w') as _:
                    pass
            symlink(log_file, log_symlink)
            symlink(err_file, err_symlink)

            file_log_handler = utils.setup_logfile_logger(log_file)

            # Remove the other handlers, but save them so we can put them back later
            old_handlers = []
            for handler in root_logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    old_handlers.append(handler)
                    root_logger.removeHandler(handler)

            try:
                salt_client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

                ret = salt_client.cmd_iter(
                    target,
                    'state.sls',
                    ['core.stackdio_users'],
                    expr_form='list'
                )

                result = {}
                # cmd_iter returns a generator that blocks until jobs finish, so
                # we want to loop through it until the jobs are done
                for i in ret:
                    for k, v in i.items():
                        result[k] = v['ret']

            finally:
                root_logger.removeHandler(file_log_handler)
                for handler in old_handlers:
                    root_logger.addHandler(handler)

            with open(log_file, 'a') as f:
                f.write(yaml.safe_dump(result))

            if len(result) != num_hosts:
                logger.debug('salt did not propagate ssh keys to all hosts')
                if current_try <= max_retries:
                    continue
                err_msg = 'Salt errored and did not propagate ssh keys to all hosts'
                stack.set_status(propagate_ssh.name, Stack.ERROR,
                                 err_msg, Level.ERROR)
                raise StackTaskException('Error propagating ssh keys: '
                                         '{0!r}'.format(err_msg))

            else:
                # each key in the dict is a host, and the value of the host
                # is either a list or dict. Those that are lists we can
                # assume to be a list of errors
                errors = {}
                for host, states in result.items():
                    if type(states) is list:
                        errors[host] = states
                        continue

                    # iterate over the individual states in the host
                    # looking for state failures
                    for state_str, state_meta in states.items():
                        if not is_state_error(state_meta):
                            continue

                        if not utils.is_requisite_error(state_meta):
                            err, recoverable = utils.state_error(state_str, state_meta)
                            if not recoverable:
                                unrecoverable_error = True
                            errors.setdefault(host, []).append(err)

                if errors:
                    # write the errors to the err_file
                    with open(err_file, 'a') as f:
                        f.write(yaml.safe_dump(errors))

                    if not unrecoverable_error and current_try <= max_retries:
                        continue

                    err_msg = 'SSH key propagation errors on hosts: ' \
                              '{0}. Please see the provisioning errors API ' \
                              'or the log file for more details: {1}'.format(
                                  ', '.join(errors.keys()),
                                  os.path.basename(log_file))
                    stack.set_status(propagate_ssh.name,
                                     Stack.ERROR,
                                     err_msg,
                                     Level.ERROR)
                    raise StackTaskException(err_msg)

                # Everything worked?
                break

        stack.set_status(propagate_ssh.name, Stack.FINISHED,
                         'Finished propagating ssh keys to all hosts.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(propagate_ssh.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


# TODO: Ignoring code complexity issues
@shared_task(name='stacks.global_orchestrate')
def global_orchestrate(stack_id, max_retries=2):
    """
    Executes the runners.state.over function with the custom orchestrate
    file  generated via the stacks.models._generate_global_orchestrate_file. This
    will target the __stackdio__ user's environment and provision the hosts with
    the formulas defined in the global orchestration.
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Executing global orchestration for stack: {0!r}'.format(stack))

        accounts = set()

        for host_definition in stack.blueprint.host_definitions.all():
            account = host_definition.cloud_image.account
            copy_formulas(account)
            accounts.add(account)

        accounts = list(accounts)

        # Set the pillar file to the global pillar data file
        change_pillar(stack, stack.global_pillar_file.path)

        # Copy the global orchestrate file into the cloud directory
        copy_global_orchestrate(stack)

        # Set up logging for this task
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()

        role_host_nums = {}
        # Get the number of hosts for each role
        for bhd in stack.blueprint.host_definitions.all():
            for fc in bhd.formula_components.all():
                role_host_nums.setdefault(fc.sls_path, 0)
                role_host_nums[fc.sls_path] += bhd.count

        # we'll break out of the loop based on the given number of retries
        current_try = 0
        while True:
            current_try += 1
            logger.info('Task {0} try #{1} for stack {2!r}'.format(
                global_orchestrate.name,
                current_try,
                stack))

            # Update status
            stack.set_status(orchestrate.name, Stack.ORCHESTRATING,
                             'Executing global orchestration try {0} of {1}. This '
                             'may take a while.'.format(current_try,
                                                        max_retries + 1))

            now = datetime.now().strftime('%Y%m%d-%H%M%S')
            log_file = os.path.join(log_dir,
                                    '{0}.global_orchestration.log'.format(now))
            err_file = os.path.join(log_dir,
                                    '{0}.global_orchestration.err'.format(now))
            log_symlink = os.path.join(root_dir, 'global_orchestration.log.latest')
            err_symlink = os.path.join(root_dir, 'global_orchestration.err.latest')

            for l in (log_file, err_file):
                with open(l, 'w') as _:
                    pass
            symlink(log_file, log_symlink)
            symlink(err_file, err_symlink)

            # Set up logging
            file_log_handler = utils.setup_logfile_logger(log_file)

            try:
                opts = salt.config.client_config(settings.STACKDIO_CONFIG.salt_master_config)

                salt_runner = salt.runner.RunnerClient(opts)

                # This might be kind of scary - but it'll work while we only have one account per
                # stack
                result = salt_runner.cmd(
                    'stackdio.orchestrate',
                    [
                        'stack_{0}_global_orchestrate'.format(stack_id),
                        'cloud.{0}'.format(accounts[0].slug),
                    ]
                )

                failed, failed_hosts = utils.process_orchestrate_result(result, stack,
                                                                        log_file, err_file)

            finally:
                root_logger.removeHandler(file_log_handler)

            if failed:
                if current_try <= max_retries:  # NOQA
                    continue

                err_msg = 'Global Orchestration errors on hosts: ' \
                          '{0}. Please see the global orchestration errors ' \
                          'API or the global orchestration log file for more ' \
                          'details: {1}'.format(
                              ', '.join(failed_hosts),
                              os.path.basename(log_file))
                stack.set_status(global_orchestrate.name,
                                 Stack.ERROR,
                                 err_msg,
                                 Level.ERROR)
                raise StackTaskException(err_msg)

            # it worked?
            break

        stack.set_status(global_orchestrate.name, Stack.FINALIZING,
                         'Finished executing global orchestration all hosts.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(global_orchestrate.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


# TODO: Ignoring code complexity issues
@shared_task(name='stacks.orchestrate')
def orchestrate(stack_id, max_retries=2):
    """
    Executes the runners.state.over function with the custom orchestrate
    file  generated via the stacks.models._generate_orchestrate_file. This
    will only target the user's environment and provision the hosts with
    the formulas defined in the blueprint and in the order specified.

    TODO: We aren't allowing users to provision from formulas owned by
    others at the moment, but if we do want to support that without
    forcing them to clone those formulas into their own account, we
    will need to support executing multiple orchestrate files in different
    environments.
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Executing orchestration for stack: {0!r}'.format(stack))

        # Copy the formulas to somewhere useful
        copy_formulas(stack)

        # Set the pillar file back to the regular pillar
        change_pillar(stack, stack.pillar_file.path)

        # Set up logging for this task
        root_dir = stack.get_root_directory()
        log_dir = stack.get_log_directory()

        role_host_nums = {}
        # Get the number of hosts for each role
        for bhd in stack.blueprint.host_definitions.all():
            for fc in bhd.formula_components.all():
                role_host_nums.setdefault(fc.sls_path, 0)
                role_host_nums[fc.sls_path] += bhd.count

        # we'll break out of the loop based on the given number of retries
        current_try = 0
        while True:
            current_try += 1
            logger.info('Task {0} try #{1} for stack {2!r}'.format(
                orchestrate.name,
                current_try,
                stack))

            # Update status
            stack.set_status(orchestrate.name, Stack.ORCHESTRATING,
                             'Executing orchestration try {0} of {1}. This '
                             'may take a while.'.format(current_try,
                                                        max_retries + 1))

            now = datetime.now().strftime('%Y%m%d-%H%M%S')
            log_file = os.path.join(log_dir,
                                    '{0}.orchestration.log'.format(now))
            err_file = os.path.join(log_dir,
                                    '{0}.orchestration.err'.format(now))
            log_symlink = os.path.join(root_dir, 'orchestration.log.latest')
            err_symlink = os.path.join(root_dir, 'orchestration.err.latest')

            for l in (log_file, err_file):
                with open(l, 'w') as _:
                    pass
            symlink(log_file, log_symlink)
            symlink(err_file, err_symlink)

            # Set up logging
            file_log_handler = utils.setup_logfile_logger(log_file)

            try:
                opts = salt.config.client_config(settings.STACKDIO_CONFIG.salt_master_config)

                salt_runner = salt.runner.RunnerClient(opts)

                result = salt_runner.cmd(
                    'stackdio.orchestrate',
                    [
                        'orchestrate',
                        'stacks.{0}-{1}'.format(stack.pk, stack.slug),
                    ]
                )

                failed, failed_hosts = utils.process_orchestrate_result(result, stack,
                                                                        log_file, err_file)

            finally:
                # Stop logging
                root_logger.removeHandler(file_log_handler)

            if failed:
                if current_try <= max_retries:
                    continue

                err_msg = 'Orchestration errors on hosts: ' \
                          '{0}. Please see the orchestration errors ' \
                          'API or the orchestration log file for more ' \
                          'details: {1}'.format(
                              ', '.join(failed_hosts),
                              os.path.basename(log_file))
                stack.set_status(orchestrate.name,
                                 Stack.ERROR,
                                 err_msg,
                                 Level.ERROR)
                raise StackTaskException(err_msg)

            # it worked?
            break

        stack.set_status(orchestrate.name, Stack.FINALIZING,
                         'Finished executing orchestration all hosts.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(orchestrate.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.finish_stack')
def finish_stack(stack_id):
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Finishing stack: {0!r}'.format(stack))

        # Update status
        stack.set_status(finish_stack.name, Stack.FINALIZING,
                         'Performing final updates to Stack.')

        # TODO: Are there any last minute updates and checks?

        # Update status
        stack.set_status(finish_stack.name, Stack.FINISHED,
                         'Finished executing tasks.')

        for host in stack.get_hosts():
            host.set_status(Host.OK, 'Host ready.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(finish_stack.name, Stack.ERROR, err_msg, Level.ERROR)
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.register_volume_delete')
def register_volume_delete(stack_id, host_ids=None):
    """
    Modifies the instance attributes for the volumes in a stack (or host_ids)
    that will automatically delete the volumes when the machines are
    terminated.
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        stack.set_status(finish_stack.name, Stack.DESTROYING,
                         'Registering volumes for deletion.')

        # use the stack driver to register all volumes on the hosts to
        # automatically delete after the host is terminated
        driver_hosts = stack.get_driver_hosts_map(host_ids)
        for driver, hosts in driver_hosts.items():
            logger.debug('Deleting volumes for hosts {0}'.format(hosts))
            driver.register_volumes_for_delete(hosts)

            # Forget the old volume IDs
            for host in hosts:
                for volume in host.volumes.all():
                    volume.volume_id = ''
                    volume.save()

        stack.set_status(finish_stack.name, Stack.DESTROYING,
                         'Finished registering volumes for deletion.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(Stack.ERROR, Stack.ERROR, err_msg)
        logger.exception(err_msg)
        raise


# TODO: Ignoring code complexity issues for now
@shared_task(name='stacks.destroy_hosts')
def destroy_hosts(stack_id, host_ids=None, delete_hosts=True, delete_security_groups=True,
                  parallel=True):
    """
    Destroy the given stack id or a subset of the stack if host_ids
    is set. After all hosts have been destroyed we must also clean
    up any managed security groups on the stack.
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        stack.set_status(destroy_hosts.name, Stack.TERMINATING,
                         'Destroying stack infrastructure. This may '
                         'take a while.')
        hosts = stack.get_hosts(host_ids)

        if hosts:
            salt_cloud = utils.StackdioSaltCloudClient(settings.STACKDIO_CONFIG.salt_cloud_config)

            # if host ids are given, we're going to terminate only those hosts
            if host_ids:
                logger.info('Destroying hosts {0!r} on stack {1!r}'.format(
                    hosts,
                    stack
                ))

            # or we'll destroy the entire stack by giving the map file with all
            # hosts defined
            else:
                logger.info('Destroying complete stack: {0!r}'.format(stack))

            result = salt_cloud.destroy_map(stack.generate_cloud_map(), hosts, parallel=parallel)

            # Error checking?
            for profile, provider in result.items():
                for name, hosts in provider.items():
                    for host, data in hosts.items():
                        if data.get('currentState', {}).get('name') != 'shutting-down':
                            logger.info('Host {0} does not appear to be '
                                        'shutting down.'.format(host))

        # wait for all hosts to finish terminating so we can
        # destroy security groups
        driver_hosts = stack.get_driver_hosts_map(host_ids)
        security_groups = set()
        for driver, hosts in driver_hosts.items():
            security_groups.update(SecurityGroup.objects.filter(
                hosts__in=hosts).exclude(is_default=True))

            known_hosts = hosts.exclude(instance_id='')
            if known_hosts:
                ok, result = driver.wait_for_state(known_hosts,
                                                   driver.STATE_TERMINATED,
                                                   timeout=10 * 60)
                if not ok:
                    stack.set_status(destroy_hosts.name, Stack.ERROR,
                                     result, Stack.ERROR)
                    raise StackTaskException(result)
                known_hosts.update(instance_id='', state='terminated')

            if delete_security_groups:
                time.sleep(5)
                for security_group in security_groups:
                    try:
                        driver.delete_security_group(security_group.name)
                        logger.debug('Managed security group {0} '
                                     'deleted...'.format(security_group.name))
                    except DeleteGroupException as e:
                        if 'does not exist' in e.message:
                            # The group didn't exist in the first place - just throw out a warning
                            logger.warn(e.message)
                        elif 'instances using security group' in e.message:
                            # The group has running instances in it - we can't delete it
                            instances = driver.get_instances_for_group(security_group.group_id)
                            err_msg = (
                                'There are active instances using security group \'{0}\': {1}.  '
                                'Please remove these instances before attempting to delete this '
                                'stack again.'.format(security_group.name,
                                                      ', '.join([i['id'] for i in instances]))
                            )

                            stack.set_status(destroy_hosts.name, Stack.ERROR,
                                             err_msg, level='ERROR')
                            logger.error(err_msg)

                            raise StackTaskException(err_msg)
                        else:
                            raise
                    security_group.delete()

        # delete hosts
        if delete_hosts and hosts:
            hosts.delete()

        stack.set_status(destroy_hosts.name, Stack.FINALIZING,
                         'Finished destroying stack infrastructure.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(destroy_hosts.name, Stack.ERROR,
                         err_msg, level='ERROR')
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.destroy_stack')
def destroy_stack(stack_id):
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        stack.set_status(destroy_stack.name, Stack.DESTROYING,
                         'Performing final cleanup of stack.')
        hosts = stack.get_hosts()

        if hosts.count() > 0:
            stack.set_status(destroy_stack.name, Stack.DESTROYING,
                             'Stack appears to have hosts attached and '
                             'can\'t be completely destroyed.',
                             level=Stack.ERROR)
        else:
            # delete the stack storage directory
            if os.path.exists(stack.get_root_directory()):
                shutil.rmtree(stack.get_root_directory())
            stack.delete()

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(Stack.ERROR, Stack.ERROR, err_msg)
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.unregister_dns')
def unregister_dns(stack_id, host_ids=None):
    """
    Removes all host information from DNS. Intended to be used just before a
    stack is terminated or stopped or put into some state where DNS no longer
    applies.
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Unregistering DNS for stack: {0!r}'.format(stack))

        stack.set_status(Stack.CONFIGURING, Stack.CONFIGURING,
                         'Unregistering hosts with DNS provider.')

        # Use the provider implementation to register a set of hosts
        # with the appropriate cloud's DNS service
        driver_hosts = stack.get_driver_hosts_map(host_ids)
        for driver, hosts in driver_hosts.items():
            logger.debug('Unregistering DNS for hosts: {0}'.format(hosts))
            driver.unregister_dns(hosts)

        stack.set_status(Stack.CONFIGURING, Stack.DESTROYING,
                         'Finished unregistering hosts with DNS provider.')

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(Stack.ERROR, Stack.ERROR, err_msg)
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.execute_action')
def execute_action(stack_id, action, *args, **kwargs):
    """
    Executes a defined action using the stack's cloud provider implementation.
    Actions are defined on the implementation class (e.g, _action_{action})
    """
    stack = None
    try:
        stack = Stack.objects.get(id=stack_id)
        logger.info('Executing action \'{0}\' on stack: {1!r}'.format(
            action,
            stack)
        )

        driver_hosts_map = stack.get_driver_hosts_map()
        for driver, hosts in driver_hosts_map.items():
            fun = getattr(driver, '_action_{0}'.format(action))
            fun(stack=stack, *args, **kwargs)

    except Stack.DoesNotExist:
        err_msg = 'Unknown Stack with id {0}'.format(stack_id)
        raise StackTaskException(err_msg)
    except StackTaskException:
        raise
    except Exception as e:
        err_msg = 'Unhandled exception: {0}'.format(str(e))
        stack.set_status(Stack.ERROR, Stack.ERROR, err_msg)
        logger.exception(err_msg)
        raise


@shared_task(name='stacks.run_command')
def run_command(command_id):
    command = StackCommand.objects.get(id=command_id)
    stack = command.stack

    # Create a salt client
    salt_client = salt.client.LocalClient(os.path.join(
        settings.STACKDIO_CONFIG.salt_config_root, 'master'))

    command.status = StackCommand.RUNNING
    command.start = datetime.now()
    command.save()

    try:
        res = salt_client.cmd_iter(
            '{0} and G@stack_id:{1}'.format(command.host_target, stack.id),
            'cmd.run',
            [command.command],
            expr_form='compound',
        )

        result = {}
        for ret in res:
            for k, v in ret.items():
                result[k] = v

        # Convert to an easier format for javascript
        ret = []
        for host, output in result.items():
            ret.append({'host': host, 'output': output['ret']})

        command.std_out_storage = json.dumps(ret)
        command.status = StackCommand.FINISHED

        command.save()

        stack.set_status(run_command.name, Stack.FINISHED,
                         'Finished running command: {0}'.format(command))

    except salt.client.SaltInvocationError:
        command.status = StackCommand.ERROR
        command.save()
        stack.set_status(run_command.name, Stack.FINISHED, 'Salt error')

    except salt.client.SaltReqTimeoutError:
        command.status = StackCommand.ERROR
        command.save()
        stack.set_status(run_command.name, Stack.FINISHED, 'Salt error')

    except Exception:
        command.status = StackCommand.ERROR
        command.save()
        stack.set_status(run_command.name, Stack.FINISHED, 'Unhandled exception')
        raise
