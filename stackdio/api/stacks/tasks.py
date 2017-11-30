# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
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

# pylint: disable=too-many-lines

from __future__ import unicode_literals

import collections
import json
import os
import shutil
import subprocess
import time
import types
from datetime import datetime
from fnmatch import fnmatch
from functools import wraps
from inspect import getcallargs

import salt.client
import salt.cloud
import salt.config
import salt.runner
import six
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from stackdio.api.cloud.models import SecurityGroup
from stackdio.api.cloud.providers.base import DeleteGroupException
from stackdio.api.stacks import utils, validators
from stackdio.api.stacks.exceptions import StackTaskException
from stackdio.api.stacks.models import Stack, StackCommand, StackHistory
from stackdio.core.constants import Activity, ComponentStatus, Health
from stackdio.core.events import trigger_event
from stackdio.core.utils import auto_retry
from stackdio.salt.utils.client import (
    StackdioLocalClient,
    StackdioRunnerClient,
    StackdioSaltClientException,
)
from stackdio.salt.utils.cloud import StackdioSaltCloudClient

logger = get_task_logger(__name__)


def stack_task(*args, **kwargs):
    """
    Create a stack celery task that performs some common functionality and handles errors
    """
    final_task = kwargs.pop('final_task', False)

    def wrapped(func):

        # Pass the args from stack_task to shared_task
        @shared_task(*args, **kwargs)
        @wraps(func)
        def task(stack_id, *task_args, **task_kwargs):
            # getcallargs() is deprecated in python3.5+
            # pylint: disable=deprecated-method

            # Get what locals() would return directly after calling
            # 'func' with the given task_args and task_kwargs
            task_called_args = getcallargs(func, *((stack_id,) + task_args), **task_kwargs)
            host_ids = task_called_args.get('host_ids')
            sls_path = task_called_args.get('component')

            try:
                stack = Stack.objects.get(id=stack_id)
            except Stack.DoesNotExist:
                raise ValueError('No stack found with id {}'.format(stack_id))

            try:
                # Call our actual task function and catch some common errors
                func(stack, *task_args, **task_kwargs)

                if not final_task:
                    # Everything went OK, set back to queued
                    stack.set_activity(Activity.QUEUED, [])

            except StackTaskException as e:
                stack.log_history(six.text_type(e), Activity.IDLE)
                stack.set_all_component_statuses(ComponentStatus.CANCELLED,
                                                 Health.UNHEALTHY,
                                                 sls_path,
                                                 host_ids)
                logger.exception(e)
                raise
            except Exception as e:
                err_msg = 'Unhandled exception: {0}'.format(e)
                stack.log_history(err_msg, Activity.IDLE)
                stack.set_all_component_statuses(ComponentStatus.CANCELLED,
                                                 Health.UNHEALTHY,
                                                 sls_path,
                                                 host_ids)
                logger.exception(e)
                raise

        return task

    return wrapped


def copy_global_orchestrate(stack):
    stack.generate_global_orchestrate_file()

    src_file = stack.get_global_orchestrate_file_path()

    accounts = set([host.cloud_image.account for host in stack.hosts.all()])

    for account in accounts:
        dest_dir = os.path.join(account.get_root_directory(), 'salt_files')

        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir, 0o755)

        shutil.copyfile(src_file, os.path.join(dest_dir,
                                               'stack_{0}_global_orchestrate.sls'.format(stack.id)))


def change_pillar(stack, global_orch):
    salt_client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

    target = [h.hostname for h in stack.get_hosts()]

    # From the testing I've done, this also automatically refreshes the pillar
    ret = salt_client.cmd_iter(
        target,
        'grains.setval',
        [
            'global_orchestration',
            global_orch,
        ],
        expr_form='list',
    )

    # TODO Want to do error checking, but don't know what errors look
    result = {}

    for res in ret:
        for minion, state_ret in res.items():
            result[minion] = state_ret


# Tasks that directly operate on stacks

@stack_task(name='stacks.launch_hosts')
def launch_hosts(stack, max_attempts=3,
                 parallel=True, simulate_launch_failures=False,
                 simulate_ssh_failures=False, failure_percent=0.3):
    """
    Uses salt cloud to launch machines using the given Stack's map_file
    that was generated when the Stack was created. Salt cloud will
    handle launching machines, provisioning them as salt minions,
    connecting to the master, etc. Downstream tasks will
    handle the rest of the operational details.

    @param stack (Stack) - the primary key of the stack to launch
    @param parallel (bool) - if True, salt-cloud will launch the stack
        in parallel using multiprocessing.
    @param max_attempts (int) - the number of attempts to launch the stack

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
    @param failure_percent (float) - percentage of the Stack's hosts to be
        flagged to fail during launch. This param
        is ignored if all of the above failure flags are set to False.
        Defaults to 0.3 (30%).
    """
    # Set the activity right away
    stack.set_activity(Activity.LAUNCHING)

    hosts = stack.get_hosts()
    num_hosts = len(hosts)
    log_file = utils.get_salt_cloud_log_file(stack, 'launch')

    logger.info('Launching hosts for stack: {0!r}'.format(stack))
    logger.info('Log file: {0}'.format(log_file))

    # Build up our launch function
    @auto_retry('launch_hosts', max_attempts, StackTaskException)
    def do_launch(attempt=None):

        salt_cloud = StackdioSaltCloudClient(settings.STACKDIO_CONFIG.salt_cloud_config)
        query = salt_cloud.query()

        # Check each host to make sure it is running
        for host in hosts:
            account = host.cloud_account
            provider = account.provider.name

            # Grab the details
            host_details = query.get(account.slug, {}).get(provider, {}).get(host.hostname)

            if host_details:
                state = host_details.get('state')

                # Only re-tag if the state exists and it is not running
                if state and state not in ('running',):
                    salt_cloud.action(
                        'set_tags',
                        names=[host.hostname],
                        kwargs={
                            'Name': '{0}-DEL_BY_STACKDIO'.format(host.hostname)
                        }
                    )

                    # Delete the volume IDs on these
                    for vol in host.volumes.all():
                        vol.volume_id = ''
                        vol.save()

        logger.info('Task {0} try {1} of {2} for stack {3!r}'.format(
            launch_hosts.name,
            attempt,
            max_attempts,
            stack,
        ))

        if num_hosts == 1:
            label = '1 host is'
        else:
            label = '{0} hosts are'.format(num_hosts)

        stack.log_history(
            '{0} being launched. Try {1} of {2}. '
            'This may take a while.'.format(
                label,
                attempt,
                max_attempts,
            )
        )

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
            log_file=log_file,
        )

        # Look for launch errors
        errors = set()
        terminate_list = []
        for host_name, results in launch_result.items():
            logger.debug('Checking host {0} for errors.'.format(host_name))

            # Error format #1
            if 'Errors' in results and 'Error' in results['Errors']:
                err_msg = results['Errors']['Error']['Message']
                logger.debug('Error on host {0}: {1}'.format(host_name, err_msg))
                errors.add(err_msg)
                # Add to the list of hosts to terminate
                terminate_list.append(host_name)

            # Error format #2
            elif 'Error' in results:
                err_msg = results['Error']
                logger.debug('Error on host {0}: {1}'.format(host_name, err_msg))
                errors.add(err_msg)
                terminate_list.append(host_name)

        if terminate_list:
            # terminate the errored hosts
            utils.terminate_hosts(stack, cloud_map, terminate_list)

            logger.debug('Errors found, terminating hosts for retry: {0!r}'.format(errors))

            for err_msg in errors:
                stack.log_history(err_msg)
            raise StackTaskException('Error(s) found while launching stack.')

    # Now call our launch function
    do_launch()


@stack_task(name='stacks.update_metadata', final_task=True)
def update_metadata(stack, activity=None, host_ids=None):
    if activity is not None:
        # Update activity
        stack.log_history('Collecting host metadata from cloud provider.', activity, host_ids)

    # All hosts are running (we hope!) so now we can pull the various
    # metadata and store what we want to keep track of.
    logger.info('Updating metadata for stack: {0!r}'.format(stack))

    # Use salt-cloud to look up host information we need now that
    # the machines are running
    query_results = stack.query_hosts(force=True)

    bad_states = ('terminated', 'shutting-down')

    for host in stack.get_hosts(host_ids):
        logger.debug('Updating metadata for host {0}'.format(host))

        # FIXME: This is cloud provider specific. Should farm it out to
        # the right implementation
        host_data = query_results.get(host.hostname)
        is_absent = host_data is None

        if not isinstance(host_data, (types.NoneType, collections.Mapping)):
            raise TypeError('Expected a dict from salt cloud, received {0}'.format(type(host_data)))

        # Check for terminated host state
        if is_absent or ('state' in host_data and host_data['state'] in bad_states):
            # update relevant metadata
            host.instance_id = ''
            host.sir_id = 'NA'

            host.state = 'Absent' if is_absent else host_data['state']

        else:
            # Process the host info
            utils.process_host_info(host_data, host)

        # save the host
        host.save()

    if activity is not None:
        stack.set_activity(Activity.QUEUED, host_ids)


@stack_task(name='stacks.tag_infrastructure', final_task=True)
def tag_infrastructure(stack, activity=None, host_ids=None):
    """
    Tags hosts and volumes with certain metadata that should prove useful
    to anyone using the AWS console.

    ORDER MATTERS! Make sure that tagging only comes after you've executed
    the `update_metadata` task as that task actually pulls in information
    we need to use the tagging API effectively.
    """
    logger.info('Tagging infrastructure for stack: {0!r}'.format(stack))

    if activity is not None:
        # Log some history
        stack.log_history('Tagging stack infrastructure.', activity, host_ids)

    # for each set of hosts on an account, use the driver implementation
    # to tag the various infrastructure
    driver_hosts = stack.get_driver_hosts_map(host_ids)

    for driver, hosts in driver_hosts.items():
        volumes = stack.volumes.filter(host__in=hosts)
        driver.tag_resources(stack, hosts, volumes)

    if activity is not None:
        stack.set_activity(Activity.QUEUED, host_ids)


@stack_task(name='stacks.register_dns')
def register_dns(stack, activity, host_ids=None):
    """
    Must be ran after a Stack is up and running and all host information has
    been pulled and stored in the database.
    """
    stack.log_history('Registering hosts with DNS provider.', activity, host_ids)

    logger.info('Registering DNS for stack: {0!r}'.format(stack))

    # Use the provider implementation to register a set of hosts
    # with the appropriate cloud's DNS service
    driver_hosts = stack.get_driver_hosts_map(host_ids)
    for driver, hosts in driver_hosts.items():
        driver.register_dns(hosts)


@stack_task(name='stacks.ping')
def ping(stack, activity, interval=5, max_failures=10):
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
    stack.log_history('Attempting to ping all hosts.', activity)
    required_hosts = [h.hostname for h in stack.get_hosts()]

    client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

    # Execute until successful, failing after a few attempts
    failures = 0

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
            err_msg = 'Max failures ({0}) reached while pinging hosts.'.format(max_failures)
            raise StackTaskException(err_msg)

        time.sleep(interval)

    if false_hosts:
        err_msg = 'Unable to ping hosts: {0}'.format(', '.join(false_hosts))
        raise StackTaskException(err_msg)

    stack.log_history('All hosts pinged successfully.')


@stack_task(name='stacks.sync_all')
def sync_all(stack):
    # Update status
    stack.log_history('Synchronizing salt systems on all hosts.', Activity.PROVISIONING)

    logger.info('Syncing all salt systems for stack: {0!r}'.format(stack))

    # Generate all the files before we sync
    stack.generate_orchestrate_file()
    stack.generate_global_orchestrate_file()

    target = [h.hostname for h in stack.get_hosts()]
    client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

    ret = client.cmd_iter(target, 'saltutil.sync_all', kwarg={'saltenv': 'base'}, expr_form='list')

    result = {}
    for res in ret:
        for host, data in res.items():
            result[host] = data

    for host, data in result.items():
        if 'retcode' not in data:
            logger.warning('Host {0} missing a retcode... assuming failure'.format(host))

        if data.get('retcode', 1) != 0:
            err_msg = six.text_type(data['ret'])
            raise StackTaskException('Error syncing salt data: {0!r}'.format(err_msg))

    stack.log_history('Finished synchronizing salt systems on all hosts.')


@stack_task(name='stacks.highstate')
def highstate(stack, max_attempts=3):
    """
    Executes the state.highstate function on the stack using the default
    stackdio top file. That top tile will only target the 'base'
    environment and core states for the stack. These core states are
    purposely separate from others to provision hosts with things that
    stackdio needs.
    """
    stack.set_activity(Activity.PROVISIONING)

    num_hosts = len(stack.get_hosts())
    target = [h.hostname for h in stack.get_hosts()]
    logger.info('Running core provisioning for stack: {0!r}'.format(stack))

    # Make sure the pillar is properly set
    change_pillar(stack, global_orch=False)

    # Set up logging for this task
    root_dir = stack.get_root_directory()
    log_dir = stack.get_log_directory()

    # Build up our highstate function
    @auto_retry('highstate', max_attempts, StackTaskException)
    def do_highstate(attempt=None):

        logger.info('Task {0} try #{1} for stack {2!r}'.format(
            highstate.name,
            attempt,
            stack))

        # Update status
        stack.log_history(
            'Executing core provisioning try {0} of {1}. '
            'This may take a while.'.format(
                attempt,
                max_attempts,
            )
        )

        # Use our fancy context manager that handles logging for us
        with StackdioLocalClient(run_type='provisioning',
                                 root_dir=root_dir,
                                 log_dir=log_dir) as client:

            results = client.run(target, 'state.highstate', expr_form='list')

            if results['failed']:
                raise StackTaskException(
                    'Core provisioning errors on hosts: '
                    '{0}. Please see the provisioning errors API '
                    'or the log file for more details.'.format(', '.join(results['failed_hosts']))
                )

            if num_hosts != results['num_hosts']:
                logger.debug('salt did not provision all hosts')
                err_msg = 'Salt errored and did not provision all the hosts'
                raise StackTaskException('Error executing core provisioning: {0!r}'.format(err_msg))

    # Call our highstate.  Will raise the appropriate exception if it fails.
    do_highstate()

    stack.log_history('Finished core provisioning all hosts.')


@stack_task(name='stacks.propagate_ssh')
def propagate_ssh(stack, max_attempts=3):
    """
    Similar to stacks.highstate, except we only run `core.stackdio_users`
    instead of `core.*`.  This is useful so that ssh keys can be added to
    hosts without having to completely re run provisioning.
    """
    stack.set_activity(Activity.PROVISIONING)

    target = [h.hostname for h in stack.get_hosts()]
    num_hosts = len(stack.get_hosts())
    logger.info('Propagating ssh keys on stack: {0!r}'.format(stack))

    # Make sure the pillar is properly set
    change_pillar(stack, global_orch=False)

    # Set up logging for this task
    root_dir = stack.get_root_directory()
    log_dir = stack.get_log_directory()

    @auto_retry('propagate_ssh', max_attempts, StackTaskException)
    def do_propagate_ssh(attempt=None):
        logger.info('Task {0} try #{1} for stack {2!r}'.format(
            propagate_ssh.name,
            attempt,
            stack))

        # Update status
        stack.log_history(
            'Propagating ssh try {0} of {1}. This may take a while.'.format(
                attempt,
                max_attempts,
            )
        )

        # Use our fancy context manager that handles logging for us
        with StackdioLocalClient(run_type='propagate-ssh',
                                 root_dir=root_dir,
                                 log_dir=log_dir) as client:

            results = client.run(target, 'state.sls', arg=['core.stackdio_users'], expr_form='list')

            if results['failed']:
                raise StackTaskException(
                    'SSH key propagation errors on hosts: '
                    '{0}. Please see the provisioning errors API '
                    'or the log file for more details.'.format(', '.join(results['failed_hosts']))
                )

            if num_hosts != results['num_hosts']:
                logger.debug('salt did not propagate ssh keys to all hosts')
                err_msg = 'Salt errored and did not propagate ssh keys to all hosts'
                raise StackTaskException('Error propagating ssh keys: {0!r}'.format(err_msg))

    # Call our function
    do_propagate_ssh()

    stack.log_history('Finished propagating ssh keys to all hosts.')


@stack_task(name='stacks.global_orchestrate')
def global_orchestrate(stack, max_attempts=3):
    """
    Executes the runners.state.over function with the custom orchestrate
    file  generated via the stacks.models._generate_global_orchestrate_file. This
    will target the __stackdio__ user's environment and provision the hosts with
    the formulas defined in the global orchestration.
    """
    stack.set_activity(Activity.ORCHESTRATING)

    logger.info('Executing global orchestration for stack: {0!r}'.format(stack))

    accounts = set()

    for host_definition in stack.blueprint.host_definitions.all():
        account = host_definition.cloud_image.account
        accounts.add(account)

    accounts = list(accounts)

    # Set the pillar file to the global pillar data file
    stack.generate_global_orchestrate_file()
    change_pillar(stack, global_orch=True)

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

    @auto_retry('global_orchestrate', max_attempts, StackTaskException)
    def do_global_orchestrate(attempt=None):
        logger.info('Task {0} try #{1} for stack {2!r}'.format(
            global_orchestrate.name,
            attempt,
            stack,
        ))

        # Update status
        stack.log_history(
            'Executing global orchestration try {0} of {1}. This '
            'may take a while.'.format(
                attempt,
                max_attempts,
            )
        )

        with StackdioRunnerClient(run_type='global_orchestration',
                                  root_dir=root_dir,
                                  log_dir=log_dir) as client:

            # This might be kind of scary - but it'll work while we only have one account per
            # stack
            try:
                result = client.orchestrate(arg=[
                    'stack_{0}_global_orchestrate'.format(stack.id),
                    'cloud.{0}'.format(accounts[0].slug),
                ])
            except StackdioSaltClientException as e:
                raise StackTaskException('Global orchestration failed: {}'.format(six.text_type(e)))

            if result['failed']:
                err_msg = 'Global Orchestration errors on components: ' \
                          '{0}. Please see the global orchestration errors ' \
                          'API or the global orchestration log file for more ' \
                          'details.'.format(', '.join(result['failed_sls']))
                raise StackTaskException(err_msg)

    # Call our function
    do_global_orchestrate()

    stack.log_history('Finished executing global orchestration all hosts.')


@stack_task(name='stacks.orchestrate')
def orchestrate(stack, max_attempts=3):
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
    stack.set_activity(Activity.ORCHESTRATING)

    logger.info('Executing orchestration for stack: {0!r}'.format(stack))

    # Set the pillar back to the regular pillar
    stack.generate_orchestrate_file()
    change_pillar(stack, global_orch=False)

    # Set up logging for this task
    root_dir = stack.get_root_directory()
    log_dir = stack.get_log_directory()

    role_host_nums = {}
    # Get the number of hosts for each role
    for bhd in stack.blueprint.host_definitions.all():
        for fc in bhd.formula_components.all():
            role_host_nums.setdefault(fc.sls_path, 0)
            role_host_nums[fc.sls_path] += bhd.count

    @auto_retry('orchestrate', max_attempts, StackTaskException)
    def do_orchestrate(attempt=None):
        logger.info('Task {0} try #{1} for stack {2!r}'.format(
            orchestrate.name,
            attempt,
            stack))

        # Update status
        stack.log_history(
            'Executing orchestration try {0} of {1}. This '
            'may take a while.'.format(
                attempt,
                max_attempts,
            )
        )

        with StackdioRunnerClient(run_type='orchestration',
                                  root_dir=root_dir,
                                  log_dir=log_dir) as client:

            # Set us to RUNNING
            stack.set_all_component_statuses(ComponentStatus.RUNNING)

            try:
                result = client.orchestrate(arg=[
                    'orchestrate',
                    'stacks.{0}'.format(stack.pk),
                ])
            except StackdioSaltClientException as e:
                raise StackTaskException('Orchestration failed: {}'.format(six.text_type(e)))

            utils.set_component_statuses(stack, result)

            if result['failed']:
                err_msg = 'Orchestration errors on components: ' \
                          '{0}. Please see the orchestration errors ' \
                          'API or the orchestration log file for more ' \
                          'details.'.format(', '.join(result['failed_sls']))
                raise StackTaskException(err_msg)

    # Call our function
    do_orchestrate()

    stack.log_history('Finished executing orchestration all hosts.')


@stack_task(name='stacks.single_sls')
def single_sls(stack, component, host_target, max_attempts=3):
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
    # Grab all the hosts that match
    if host_target:
        host_ids = []
        included_hostnames = []
        for host in stack.hosts.all():
            if fnmatch(host.hostname, host_target):
                host_ids.append(host.id)
                included_hostnames.append(host.hostname)
    else:
        host_ids = None
        included_hostnames = None

    stack.set_activity(Activity.ORCHESTRATING, host_ids)

    logger.info('Executing single sls {0} for stack: {1!r}'.format(component, stack))

    # Set the pillar file back to the regular pillar
    change_pillar(stack, global_orch=False)

    # Set up logging for this task
    root_dir = stack.get_root_directory()
    log_dir = stack.get_log_directory()

    try:
        host_list = validators.can_run_component_on_stack(component, stack)
    except validators.ValidationError as e:
        raise StackTaskException(e.detail)

    list_target = [h.hostname for h in host_list]

    if host_target:
        target = '{0} and L@{1}'.format(host_target, ','.join(list_target))
        expr_form = 'compound'
    else:
        target = list_target
        expr_form = 'list'

    @auto_retry('single_sls', max_attempts, StackTaskException)
    def do_single_sls(attempt=None):
        logger.info('Task {0} try #{1} for stack {2!r}'.format(
            single_sls.name,
            attempt,
            stack,
        ))

        # Update status
        stack.log_history(
            'Executing sls {0} try {1} of {2}. This '
            'may take a while.'.format(
                component,
                attempt,
                max_attempts,
            )
        )

        with StackdioLocalClient(run_type='single-sls',
                                 root_dir=root_dir,
                                 log_dir=log_dir) as client:

            stack.set_component_status(component, ComponentStatus.RUNNING,
                                       include_list=included_hostnames)

            results = client.run(
                target,
                'state.sls',
                arg=[
                    component,
                    'stacks.{0}'.format(stack.pk),
                ],
                expr_form=expr_form,
            )

            if results['failed']:
                raise StackTaskException(
                    'Single SLS {} errors on hosts: '
                    '{}. Please see the provisioning errors API '
                    'or the log file for more details.'.format(
                        component,
                        ', '.join(results['failed_hosts']),
                    )
                )

            if results['succeeded_hosts']:
                stack.set_component_status(component, ComponentStatus.SUCCEEDED,
                                           results['succeeded_hosts'])

            if results['failed_hosts']:
                stack.set_component_status(component, ComponentStatus.FAILED,
                                           results['failed_hosts'])

    # Call our function
    do_single_sls()

    stack.log_history('Finished executing single sls {} on all hosts.'.format(component))


@stack_task(name='stacks.finish_stack', final_task=True)
def finish_stack(stack, activity=Activity.IDLE):
    logger.info('Finishing stack: {0!r}'.format(stack))

    # Update activity
    stack.set_activity(activity)

    # Trigger our event
    trigger_event('stack-finished', stack)


@stack_task(name='stacks.register_volume_delete')
def register_volume_delete(stack, host_ids=None):
    """
    Modifies the instance attributes for the volumes in a stack (or host_ids)
    that will automatically delete the volumes when the machines are
    terminated.
    """
    stack.log_history('Registering volumes for deletion.', Activity.TERMINATING, host_ids)

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

    stack.log_history('Finished registering volumes for deletion.')


@stack_task(name='stacks.destroy_hosts')
def destroy_hosts(stack, host_ids=None, delete_hosts=True, delete_security_groups=True,
                  parallel=True):
    """
    Destroy the given stack id or a subset of the stack if host_ids
    is set. After all hosts have been destroyed we must also clean
    up any managed security groups on the stack.
    """
    stack.log_history('Terminating stack infrastructure. This may take a while.',
                      Activity.TERMINATING, host_ids)
    hosts = stack.get_hosts(host_ids)

    if hosts:
        salt_cloud = StackdioSaltCloudClient(settings.STACKDIO_CONFIG.salt_cloud_config)

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
        for provider in result.values():
            for hosts in provider.values():
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
                                               'terminated',
                                               timeout=10 * 60)
            if not ok:
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
                    if 'does not exist' in six.text_type(e):
                        # The group didn't exist in the first place - just throw out a warning
                        logger.warning(six.text_type(e))
                    elif 'instances using security group' in six.text_type(e):
                        # The group has running instances in it - we can't delete it
                        instances = driver.get_instances_for_group(security_group.group_id)
                        err_msg = (
                            'There are active instances using security group \'{0}\': {1}.  '
                            'Please remove these instances before attempting to delete this '
                            'stack again.'.format(security_group.name,
                                                  ', '.join([i['id'] for i in instances]))
                        )
                        raise StackTaskException(err_msg)
                    else:
                        raise
                security_group.delete()

    # delete hosts
    if delete_hosts and hosts:
        hosts.delete()

    stack.log_history('Finished terminating hosts.')


@stack_task(name='stacks.destroy_stack', final_task=True)
def destroy_stack(stack):
    stack.log_history('Performing final cleanup of stack.', Activity.TERMINATING)
    hosts = stack.get_hosts()

    if hosts.count() > 0:
        raise StackTaskException(
            'Stack appears to have hosts attached and can\'t be completely destroyed.'
        )
    else:
        stack.delete()


@stack_task(name='stacks.unregister_dns')
def unregister_dns(stack, activity, host_ids=None):
    """
    Removes all host information from DNS. Intended to be used just before a
    stack is terminated or stopped or put into some state where DNS no longer
    applies.
    """
    stack.log_history('Unregistering hosts with DNS provider.', activity, host_ids)

    logger.info('Unregistering DNS for stack: {0!r}'.format(stack))

    # Use the provider implementation to register a set of hosts
    # with the appropriate cloud's DNS service
    driver_hosts = stack.get_driver_hosts_map(host_ids)
    for driver, hosts in driver_hosts.items():
        logger.debug('Unregistering DNS for hosts: {0}'.format(hosts))
        driver.unregister_dns(hosts)


@stack_task(name='stacks.execute_action')
def execute_action(stack, action, activity, *args, **kwargs):
    """
    Executes a defined action using the stack's cloud provider implementation.
    Actions are defined on the implementation class (e.g, _action_{action})
    """
    stack.set_activity(activity)

    logger.info('Executing action \'{0}\' on stack: {1!r}'.format(action, stack))

    driver_hosts_map = stack.get_driver_hosts_map()
    for driver in driver_hosts_map:
        fun = getattr(driver, '_action_{0}'.format(action))
        fun(stack=stack, *args, **kwargs)


# Other tasks that don't directly operate on stacks

@shared_task(name='stacks.run_command')
def run_command(command_id):
    command = StackCommand.objects.get(id=command_id)
    stack = command.stack

    stack.log_history('Running command: {}'.format(command.command), Activity.EXECUTING)

    # Create a salt client
    salt_client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)

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

        stack.log_history('Finished running command: {0}'.format(command.command), Activity.IDLE)

    except (salt.client.SaltInvocationError, salt.client.SaltReqTimeoutError):
        command.status = StackCommand.ERROR
        command.save()
        stack.log_history('Encountered Salt error while running command.', Activity.IDLE)

    except Exception:
        command.status = StackCommand.ERROR
        command.save()
        stack.log_history('Unhandled exception while running command.', Activity.IDLE)
        raise


@shared_task(name='stacks.update_host_info')
def update_host_info():
    """
    Update all the host info
    """
    # get our salt cloud object & query the cloud providers
    salt_cloud = salt.cloud.CloudClient(settings.STACKDIO_CONFIG.salt_cloud_config)
    query_results = salt_cloud.full_query()

    if not isinstance(query_results, collections.Mapping):
        raise TypeError('Expected a dict from salt-cloud, received {}'.format(type(query_results)))

    if not query_results:
        logger.warning('salt-cloud didn\'t return anything, this usually means '
                       'there was an error querying the provider API and we '
                       'shouldn\'t base any statuses off this response.')
        return

    logger.info('Received host info from salt cloud.')

    # Iterate through all the stacks & hosts and check their state / activity
    with transaction.atomic(using=Stack.objects.db):

        # Use select_for_update so that we don't have an issue where a stack gets deleted
        # then re-saved during this task
        for stack in Stack.objects.select_for_update():

            newly_dead_hosts = []

            new_host_activities = []

            for host in stack.hosts.all():
                account = host.cloud_account

                if account.slug not in query_results:
                    # If the account is missing, then we shouldn't do anything.
                    continue

                account_info = query_results[account.slug].get(account.provider.name, {})
                host_info = account_info.get(host.hostname)

                old_state = host.state
                old_activity = host.activity

                # Check for terminated host state
                if not host_info:
                    # If we're queued or launching, we may have just not been launched yet,
                    # so we don't want to be terminated in that case
                    if host.activity not in (Activity.QUEUED, Activity.LAUNCHING):
                        host.state = 'terminated'
                else:
                    host.state = host_info['state']

                    # Process the info
                    utils.process_host_info(host_info, host)

                if host.state != old_state:
                    logger.info('Host {0} state changed from {1} to {2}'.format(host.hostname,
                                                                                old_state,
                                                                                host.state))

                # Only change the host activity if the state is terminated and we are
                # not currently terminated or terminating
                if host.state in ('terminated',):
                    if host.activity not in (Activity.TERMINATING, Activity.TERMINATED):
                        host.activity = Activity.DEAD

                # Change the activity back to idle if we're no longer dead
                if host.activity == Activity.DEAD and host.state not in ('terminated',):
                    host.activity = Activity.IDLE

                new_host_activities.append(host.activity)

                if old_activity != Activity.DEAD and host.activity == Activity.DEAD:
                    newly_dead_hosts.append(host.hostname)

                # save the host
                host.save()

            # Log some history if we've marked hosts as DEAD
            if newly_dead_hosts:
                err_msg = ('The following hosts have now been marked '
                           '\'{}\': {}'.format(Activity.DEAD, ', '.join(newly_dead_hosts)))
                if len(err_msg) > StackHistory._meta.get_field('message').max_length:
                    err_msg = 'Several hosts have been marked \'{}\'.'.format(Activity.DEAD)
                stack.log_history(err_msg)

            all_dead = all([a == Activity.DEAD for a in new_host_activities])

            # If all the hosts are dead, set the stack to dead also
            if all_dead and new_host_activities:
                stack.activity = Activity.DEAD

            # If the stack is currently marked dead and all the hosts are NOT dead, then set the
            # activity to idle.
            if stack.activity == Activity.DEAD and not all_dead:
                stack.activity = Activity.IDLE

            stack.save(update_fields=['activity'])
