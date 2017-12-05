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

from __future__ import print_function, unicode_literals

import logging
import os
import random
from datetime import datetime

import salt.config as config
from django.conf import settings
from stackdio.core.constants import Action, ComponentStatus
from stackdio.salt.utils.cloud import StackdioSaltCloudMap, catch_salt_cloud_map_failures

logger = logging.getLogger(__name__)


def set_component_statuses(stack, orch_result):

    for sls_path, sls_result in orch_result['succeeded_sls'].items():
        stack.set_component_status(sls_path, ComponentStatus.SUCCEEDED)

    for sls_path, sls_result in orch_result['cancelled_sls'].items():
        stack.set_component_status(sls_path, ComponentStatus.CANCELLED)

    for sls_path, sls_result in orch_result['failed_sls'].items():
        # Set the status to succeeded on the hosts that succeeded
        # but only if the list is non-empty
        if sls_result['succeeded_hosts']:
            stack.set_component_status(sls_path, ComponentStatus.SUCCEEDED,
                                       sls_result['succeeded_hosts'])

        # Set the status to failed on everything else
        stack.set_component_status(sls_path, ComponentStatus.FAILED, sls_result['failed_hosts'])


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
    # Set the host state
    host.state = host_info.get('state') or 'unknown'

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

    missing_hosts = set(map_data.get('create', []))

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
