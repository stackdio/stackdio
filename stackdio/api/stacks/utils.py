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

from __future__ import print_function, unicode_literals

import logging
import os
import random
import re
from datetime import datetime

import salt.client
import salt.cloud
import salt.config as config
import salt.key
import salt.syspaths
import salt.utils
import salt.utils.cloud
import six
import yaml
from django.conf import settings

from stackdio.api.stacks.exceptions import StackTaskException
from stackdio.core.constants import Action, ComponentStatus
from stackdio.salt.utils.cloud import StackdioSaltCloudMap, catch_salt_cloud_map_failures


logger = logging.getLogger(__name__)

ERROR_REQUISITE = 'One or more requisite failed'

COLOR_REGEX = re.compile(r'\[0;[\d]+m')


def state_to_dict(state_string):
    """
    Takes the state string and transforms it into a dict of key/value
    pairs that are a bit easier to handle.

    Before: group_|-stackdio_group_|-abe_|-present

    After: {
        'module': 'group',
        'function': 'present',
        'name': 'abe',
        'declaration_id': 'stackdio_group'
    }
    """
    state_labels = settings.STATE_EXECUTION_FIELDS
    state_fields = state_string.split(settings.STATE_EXECUTION_DELIMITER)
    return dict(zip(state_labels, state_fields))


def is_requisite_error(state_meta):
    """
    Is the state error because of a requisite state failure?
    """
    return ERROR_REQUISITE in state_meta['comment']


def is_recoverable(err):
    """
    Checks the provided error against a blacklist of errors
    determined to be unrecoverable. This should be used to
    prevent retrying of provisioning or orchestration because
    the error will continue to occur.
    """
    # TODO: determine the blacklist of errors that
    # will trigger a return of False here
    return True


def state_error(state_str, state_meta):
    """
    Takes the given state result string and the metadata
    of the state execution result and returns a consistent
    dict for the error along with whether or not the error
    is recoverable.
    """
    state = state_to_dict(state_str)
    func = '{module}.{func}'.format(**state)
    decl_id = state['declaration_id']
    err = {
        'error': state_meta['comment'],
        'function': func,
        'declaration_id': decl_id,
    }
    if 'stderr' in state_meta['changes']:
        err['stderr'] = state_meta['changes']['stderr']
    if 'stdout' in state_meta['changes']:
        err['stdout'] = state_meta['changes']['stdout']
    return err, is_recoverable(err)


def process_sls_result(sls_result, err_file):
    if 'out' in sls_result and sls_result['out'] != 'highstate':
        logger.debug('This isn\'t highstate data... it may not process correctly.')

        raise StackTaskException('Missing highstate data from the orchestrate runner.')

    if 'ret' not in sls_result:
        return True, set()

    failed = False
    failed_hosts = set()

    for host, state_results in sls_result['ret'].items():
        sorted_result = sorted(state_results.values(), key=lambda x: x['__run_num__'])
        for stage_result in sorted_result:

            if stage_result.get('result', False):
                continue

            # We have failed
            failed = True

            # Check to see if it's a requisite error - if so, we don't want to clutter the
            # logs, so we'll continue on.
            if is_requisite_error(stage_result):
                continue

            failed_hosts.add(host)

            # Write to the error log
            with open(err_file, 'a') as f:
                f.write(yaml.safe_dump(stage_result))

    return failed, failed_hosts


def process_times(sls_result):
    if 'ret' not in sls_result:
        return

    max_time_map = {}

    for state_results in sls_result['ret'].values():
        for stage_label, stage_result in state_results.items():

            # Pull out the duration
            if 'duration' in stage_result:
                current = max_time_map.get(stage_label, 0)
                duration = stage_result['duration']
                try:
                    if isinstance(duration, six.string_types):
                        new_time = float(duration.split()[0])
                    else:
                        new_time = float(duration)
                except ValueError:
                    # Make sure we never fail
                    new_time = 0

                # Only set the duration if it's higher than what we already have
                # This should be all we care about - since everything is running in parallel,
                # the bottleneck is the max time
                max_time_map[stage_label] = max(current, new_time)

    time_map = {}

    # aggregate into modules
    for stage_label, max_time in max_time_map.items():
        info_dict = state_to_dict(stage_label)

        current = time_map.get(info_dict['module'], 0)

        # Now we want the sum since these are NOT running in parallel.
        time_map[info_dict['module']] = current + max_time

    for module, time in sorted(time_map.items()):
        logger.info('Module {0} took {1} total seconds to run'.format(module, time / 1000))


def process_orchestrate_result(result, stack, log_file, err_file):
    # The actual info we want is nested in the 'data' key
    result = result['data']

    opts = salt.config.client_config(settings.STACKDIO_CONFIG.salt_master_config)

    if not isinstance(result, dict):
        with open(err_file, 'a') as f:
            f.write('Orchestration failed.  See below.\n\n')
            f.write(six.text_type(result))
        return True, set()

    if opts['id'] not in result:
        with open(err_file, 'a') as f:
            f.write('Orchestration result is missing information:\n\n')
            f.write(six.text_type(result))
        return True, set()

    result = result[opts['id']]

    if not isinstance(result, dict):
        with open(err_file, 'a') as f:
            f.write(six.text_type(result))

        raise StackTaskException(result)

    failed = False
    failed_hosts = set()

    for sls, sls_result in sorted(result.items(), key=lambda x: x[1]['__run_num__']):
        sls_dict = state_to_dict(sls)

        logger.info('Processing stage {0} for stack {1}'.format(sls_dict['name'], stack.title))

        if 'changes' in sls_result:
            process_times(sls_result['changes'])

        logger.info('')

        status_set = False

        with open(err_file, 'a') as f:
            if 'changes' in sls_result and 'ret' in sls_result['changes']:
                f.write(
                    'Stage {0} returned {1} host info object(s)\n\n'.format(
                        sls_dict['name'],
                        len(sls_result['changes']['ret'])
                    )
                )
            elif sls_result.get('result', False):
                f.write('Stage {0} appears to have no changes, and it succeeded.\n\n'.format(
                    sls_dict['name']
                ))
            else:
                f.write(
                    'Stage {0} appears to have no changes, but it failed.  See below.\n'.format(
                        sls_dict['name']
                    )
                )
                # No changes, so set based on the comment
                if ERROR_REQUISITE in sls_result['comment']:
                    stack.set_component_status(sls_dict['name'], ComponentStatus.CANCELLED)
                else:
                    stack.set_component_status(sls_dict['name'], ComponentStatus.FAILED)
                status_set = True

        if sls_result.get('result', False):
            # This whole sls is good!  Just continue on with the next one.
            if not status_set:
                stack.set_component_status(sls_dict['name'], ComponentStatus.SUCCEEDED)
            continue

        # Process the data for this sls
        with open(err_file, 'a') as f:
            comment = sls_result['comment']
            if isinstance(comment, six.string_types):
                f.write('{0}\n\n'.format(COLOR_REGEX.sub('', comment)))
            else:
                f.write('{0}\n\n'.format(yaml.safe_dump(comment)))
        local_failed, local_failed_hosts = process_sls_result(sls_result['changes'], err_file)

        if not status_set:
            # Set the status to FAILED on everything that failed
            stack.set_component_status(sls_dict['name'],
                                       ComponentStatus.FAILED,
                                       local_failed_hosts)

            if local_failed and local_failed_hosts:
                # Set the status to SUCCEEDED on everything that didn't fail
                stack.set_component_status(sls_dict['name'],
                                           ComponentStatus.SUCCEEDED,
                                           [],
                                           local_failed_hosts)

        if local_failed:
            # Do it this way to ensure we don't set it BACK to false after a failure.
            failed = True
        failed_hosts.update(local_failed_hosts)

    return failed, failed_hosts


def filter_actions(user, stack, actions):
    ret = []
    for action in actions:
        the_action = action
        if action == 'command':
            the_action = 'execute'
        elif action == Action.PROPAGATE_SSH:
            the_action = 'admin'
        if user.has_perm('stacks.{0}_stack'.format(the_action.lower()), stack):
            ret.append(action)

    return ret


def process_host_info(host_info, host):
    """
    Process the host info object received from salt cloud.
    This *DOES NOT* save the host, it only updates fields on the host.
    :param host_info: the salt-cloud host dict
    :param host: the stackdio host object
    """
    # The instance id of the host
    host.instance_id = host_info.get('instanceId') or ''

    # Get the host's public IP/host set by the cloud provider. This
    # is used later when we tie the machine to DNS
    host.provider_public_dns = host_info.get('dnsName')
    host.provider_private_dns = host_info.get('privateDnsName')

    # If the instance is stopped, 'privateIpAddress' isn't in the returned dict, so this
    # throws an exception if we don't use host_data.get().  I changed the above two
    # keys to do the same for robustness
    host.provider_public_ip = host_info.get('ipAddress')
    host.provider_private_ip = host_info.get('privateIpAddress')

    # update volume information
    block_device_mappings_parent = host_info.get('blockDeviceMapping') or {}
    block_device_mappings = block_device_mappings_parent.get('item') or []

    if not isinstance(block_device_mappings, list):
        block_device_mappings = [block_device_mappings]

    # Build up a map of device name -> device mapping
    bdm_map = {bdm['deviceName']: bdm for bdm in block_device_mappings}

    # For each volume we allegedly have, make sure it is attached to the host.
    # If we can't find it, forget the volume_id
    # Otherwise update the volume_id
    for volume in host.volumes.all():
        if volume.device in bdm_map:
            # update the volume_id info
            volume.volume_id = bdm_map[volume.device]['ebs']['volumeId']
        else:
            # The volume is gone - reflect this on the volume model
            volume.volume_id = ''

        volume.save()

    # Update spot instance metadata
    if 'spotInstanceRequestId' in host_info:
        host.sir_id = host_info['spotInstanceRequestId']
    else:
        host.sir_id = ''


def get_salt_cloud_log_file(stack, suffix):
    """
    suffix is a string (e.g, launch, overstate, highstate, error, etc)
    """
    # Set up logging for this launch
    root_dir = stack.get_root_directory()
    log_dir = stack.get_log_directory()

    now = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_file = os.path.join(log_dir, '{0}.{1}.log'.format(now, suffix))
    log_symlink = os.path.join(root_dir, '{0}.log.latest'.format(suffix))

    # "touch" the log file and symlink it to the latest
    with open(log_file, 'w') as _:
        pass

    if os.path.islink(log_symlink):
        os.remove(log_symlink)
    os.symlink(log_file, log_symlink)

    return log_file


def get_salt_cloud_opts():
    return config.cloud_config(
        settings.STACKDIO_CONFIG.salt_cloud_config
    )


@catch_salt_cloud_map_failures(retry_times=5)
def terminate_hosts(stack, cloud_map, hostnames):
    """
    Uses salt-cloud to terminate the given list of hosts.

    @param (list[stacks.models.Host]) - the hosts to terminate.
    @returns None
    """

    hosts = stack.hosts.filter(hostname__in=hostnames)

    # Set the volume_id to null for all the hosts we're deleting
    for host in hosts:
        for vol in host.volumes.all():
            vol.volume_id = ''
            vol.save()

    opts = get_salt_cloud_opts()
    opts.update({
        'parallel': True
    })

    mapper = StackdioSaltCloudMap(opts)
    mapper.rendered_map = cloud_map

    map_data = mapper.map_data()

    missing_hosts = map_data.get('create', [])

    terminate_list = set(hostnames)

    # We don't want to try to terminate missing hosts, salt doesn't like that.
    # This should remove them from the set
    terminate_list -= missing_hosts

    # Only call destroy if the list is non-empty
    if terminate_list:
        logger.debug('Terminating hosts: {0}'.format(terminate_list))
        mapper.destroy(terminate_list)


def mod_hosts_map(cloud_map, n, **kwargs):
    """
    Selects n random hosts for the given stack and modifies/adds
    the map entry for those hosts with the kwargs.
    """
    population = cloud_map.keys()

    # randomly select n hosts
    hosts = random.sample(population, n)

    # modify the hosts
    for host in hosts:
        cloud_map[host].update(kwargs)

    return cloud_map
