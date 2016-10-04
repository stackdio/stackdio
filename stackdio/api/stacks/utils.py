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

from __future__ import print_function

import logging
import multiprocessing
import os
import random
import re
from datetime import datetime
from logging.handlers import WatchedFileHandler

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
from msgpack.exceptions import ExtraData
from salt.log.setup import LOG_LEVELS

from stackdio.api.volumes.models import Volume
from stackdio.core.constants import Action, ComponentStatus

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()

ERROR_REQUISITE = 'One or more requisite failed'

COLOR_REGEX = re.compile(r'\[0;[\d]+m')

SALT_CLOUD_CACHE_DIR = os.path.join(salt.syspaths.CACHE_DIR, 'cloud')


class StackdioSaltCloudMap(salt.cloud.Map):

    def interpolated_map(self, query='list_nodes', cached=False):
        """
        Override this to use the in-memory map instead of on disk.
        Also we'll change it so that having multiple providers on the same cloud
        account doesn't break things
        """
        rendered_map = self.rendered_map.copy()
        interpolated_map = {}

        for profile, mapped_vms in rendered_map.items():
            names = set(mapped_vms)
            if profile not in self.opts['profiles']:
                if 'Errors' not in interpolated_map:
                    interpolated_map['Errors'] = {}
                msg = (
                    'No provider for the mapped {0!r} profile was found. '
                    'Skipped VMS: {1}'.format(
                        profile, ', '.join(names)
                    )
                )
                logger.info(msg)
                interpolated_map['Errors'][profile] = msg
                continue

            # Grab the provider name
            provider_info = self.opts['profiles'][profile]['provider'].split(':')

            provider = provider_info[0]
            driver_name = provider_info[1]

            matching = self.get_running_by_names(names, query, cached)

            for alias, drivers in matching.items():
                if alias != provider:
                    # If the alias doesn't match the provider of the profile we're looking at,
                    # skip it.
                    continue

                for driver, vms in drivers.items():
                    if driver != driver_name:
                        logger.warning(
                            'The driver in the matching info doesn\'t match the provider '
                            'specified in the config... Something fishy is going on'
                        )

                    for vm_name, vm_details in vms.items():
                        if alias not in interpolated_map:
                            interpolated_map[alias] = {}
                        if driver not in interpolated_map[alias]:
                            interpolated_map[alias][driver] = {}
                        interpolated_map[alias][driver][vm_name] = vm_details
                        names.remove(vm_name)

            if not names:
                continue

            profile_details = self.opts['profiles'][profile]
            alias, driver = profile_details['provider'].split(':')
            for vm_name in names:
                if alias not in interpolated_map:
                    interpolated_map[alias] = {}
                if driver not in interpolated_map[alias]:
                    interpolated_map[alias][driver] = {}
                interpolated_map[alias][driver][vm_name] = 'Absent'

        return interpolated_map

    def delete_map(self, query='list_nodes'):
        """
        Change the default value to something reasonable.
        """
        return super(StackdioSaltCloudMap, self).delete_map(query)

    def get_running_by_names(self, names, query='list_nodes', cached=False, profile=None):
        """
        Override this so we only get appropriate things for our map
        """
        if isinstance(names, six.string_types):
            names = [names]

        matches = {}
        handled_drivers = {}
        mapped_providers = self.map_providers_parallel(query, cached=cached)
        for alias, drivers in mapped_providers.items():
            for driver, vms in drivers.items():
                if driver not in handled_drivers:
                    handled_drivers[driver] = alias
                # When a profile is specified, only return an instance
                # that matches the provider specified in the profile.
                # This solves the issues when many providers return the
                # same instance. For example there may be one provider for
                # each availability zone in amazon in the same region, but
                # the search returns the same instance for each provider
                # because amazon returns all instances in a region, not
                # availability zone.
                if profile:
                    if alias not in self.opts['profiles'][profile]['provider'].split(':')[0]:
                        continue

                for vm_name, details in vms.items():
                    # XXX: The logic below can be removed once the aws driver
                    # is removed
                    if vm_name not in names:
                        continue

                    elif (driver == 'ec2' and
                          'aws' in handled_drivers and
                          'aws' in matches[handled_drivers['aws']] and
                          vm_name in matches[handled_drivers['aws']]['aws']):
                        continue
                    elif (driver == 'aws' and
                          'ec2' in handled_drivers and
                          'ec2' in matches[handled_drivers['ec2']] and
                          vm_name in matches[handled_drivers['ec2']]['ec2']):
                        continue

                    # This little addition makes everything not break :)
                    # Without this, if you have 2 providers attaching to the same AWS account,
                    # salt-cloud will try to kill / rename instances twice.  This snippet below
                    # removes those duplicates, and only kills the ones you actually want killed.
                    should_continue = False
                    for profile, data in self.rendered_map.items():
                        provider = self.opts['profiles'][profile]['provider'].split(':')[0]
                        if vm_name in data and alias != provider:
                            should_continue = True
                            break

                    if should_continue:
                        continue

                    # End inserted snippet #

                    if alias not in matches:
                        matches[alias] = {}
                    if driver not in matches[alias]:
                        matches[alias][driver] = {}
                    matches[alias][driver][vm_name] = details

        return matches


class StackdioSaltCloudClient(salt.cloud.CloudClient):

    def launch_map(self, cloud_map, **kwargs):
        """
        Runs a map from an already in-memory representation rather than an file on disk.
        """
        opts = self._opts_defaults(**kwargs)

        handler = setup_logfile_logger(
            opts['log_file'],
            opts['log_level_logfile'],
            log_format=opts['log_fmt_logfile'],
            date_format=opts['log_datefmt_logfile'],
        )

        ret = None

        try:
            mapper = StackdioSaltCloudMap(opts)
            mapper.rendered_map = cloud_map

            launched = False
            num_errors = 0
            while not launched:
                if num_errors >= 5:
                    raise salt.cloud.SaltCloudSystemExit(
                        'Maximum number of errors reached while launching stack.'
                    )

                try:
                    # Do the launch
                    dmap = mapper.map_data()
                    ret = mapper.run_map(dmap)
                    # It worked
                    launched = True
                except ExtraData as e:
                    logger.info('Received ExtraData, retrying: {0}'.format(e))
                    # Blow away the salt cloud cache and try again
                    os.remove(os.path.join(SALT_CLOUD_CACHE_DIR, 'index.p'))
                    num_errors += 1
                except salt.cloud.SaltCloudSystemExit as e:
                    if 'extra data' in e.message:
                        logger.info('Received ExtraData, retrying: {0}'.format(e))
                        # Blow away the salt cloud cache and try again
                        os.remove(os.path.join(SALT_CLOUD_CACHE_DIR, 'index.p'))
                        num_errors += 1
                    else:
                        raise
                except TypeError as e:
                    if 'NoneType' in e.message:
                        logger.info('Received TypeError, retrying: {0}'.format(e))
                        # Blow away the salt cloud cache and try again
                        os.remove(os.path.join(SALT_CLOUD_CACHE_DIR, 'index.p'))
                        num_errors += 1
                    else:
                        raise
        finally:
            # Cancel the logging, but make sure it still gets cancelled if an exception is thrown
            root_logger.removeHandler(handler)

        return salt.utils.cloud.simple_types_filter(ret)

    def destroy_map(self, cloud_map, hosts, **kwargs):
        """
        Destroy the named VMs
        """
        kwarg = kwargs.copy()
        kwarg['destroy'] = True
        mapper = StackdioSaltCloudMap(self._opts_defaults(**kwarg))
        mapper.rendered_map = cloud_map

        ret = None

        destroyed = False
        num_errors = 0
        while not destroyed:
            if num_errors >= 5:
                raise salt.cloud.SaltCloudSystemExit(
                    'Maximum number of errors reached while destroying stack.'
                )

            try:
                ret = self._do_destroy(mapper, hosts)
                # It worked
                destroyed = True
            except ExtraData as e:
                logger.info('Received ExtraData, retrying: {0}'.format(e))
                # Blow away the salt cloud cache and try again
                os.remove(os.path.join(SALT_CLOUD_CACHE_DIR, 'index.p'))
                num_errors += 1
            except salt.cloud.SaltCloudSystemExit as e:
                if 'extra data' in e.message:
                    logger.info('Received ExtraData, retrying: {0}'.format(e))
                    # Blow away the salt cloud cache and try again
                    os.remove(os.path.join(SALT_CLOUD_CACHE_DIR, 'index.p'))
                    num_errors += 1
                else:
                    raise
            except TypeError as e:
                if 'NoneType' in e.message:
                    logger.info('Received TypeError, retrying: {0}'.format(e))
                    num_errors += 1
                else:
                    raise

        return ret

    def _do_destroy(self, mapper, hosts):
        """
        Here's where the destroying actually happens
        """
        dmap = mapper.delete_map()

        hostnames = [host.hostname for host in hosts]

        # This is pulled from the salt-cloud ec2 driver code.
        msg = 'The following VMs are set to be destroyed:\n'
        names = set()
        for alias, drivers in dmap.items():
            msg += '  {0}:\n'.format(alias)
            for driver, vms in drivers.items():
                msg += '    {0}:\n'.format(driver)
                for name in vms:
                    if name in hostnames:
                        msg += '      {0}\n'.format(name)
                        names.add(name)

        if names:
            logger.info(msg)
            return salt.utils.cloud.simple_types_filter(mapper.destroy(names))
        else:
            logger.info('There are no VMs to be destroyed.')
            return {}


def setup_logfile_logger(log_path, log_level=None, log_format=None, date_format=None):
    """
    Set up logging to a file.
    """
    # Create the handler
    handler = WatchedFileHandler(log_path)

    if log_level:
        # Grab and set the level
        level = LOG_LEVELS.get(log_level.lower(), logging.ERROR)
        handler.setLevel(level)

    # Set the default console formatter config
    if not log_format:
        log_format = '%(asctime)s [%(name)-15s][%(levelname)-8s] %(message)s'
    if not date_format:
        date_format = '%Y-%m-%d %H:%M:%S'

    formatter = logging.Formatter(log_format, datefmt=date_format)

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    return handler


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

        from .tasks import StackTaskException
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
    opts = salt.config.client_config(settings.STACKDIO_CONFIG.salt_master_config)

    if not isinstance(result, dict):
        with open(err_file, 'a') as f:
            f.write('Orchestration failed.  See below.\n\n')
            f.write(str(result))
        return True, set()

    if opts['id'] not in result:
        with open(err_file, 'a') as f:
            f.write('Orchestration result is missing information:\n\n')
            f.write(str(result))
        return True, set()

    result = result[opts['id']]

    if not isinstance(result, dict):
        with open(err_file, 'a') as f:
            f.write(str(result))

        from .tasks import StackTaskException
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


def get_salt_master_opts():
    return config.cloud_config(
        settings.STACKDIO_CONFIG.salt_master_config
    )


def get_stack_mapper(cloud_map):
    opts = get_salt_cloud_opts()
    opts.update({
        'hard': False,
    })
    ret = salt.cloud.Map(opts)
    ret.rendered_map = cloud_map
    return ret


def get_stack_map_data(cloud_map):
    mapper = get_stack_mapper(cloud_map)
    return mapper.map_data()


def get_stack_vm_map(cloud_map):
    dmap = get_stack_map_data(cloud_map)
    vms = {}
    for k in ('create', 'existing',):
        if k in dmap:
            vms.update(dmap[k])
    return vms


def get_ssh_kwargs(host, vm_, __opts__):
    return {
        'host': host.provider_private_dns,
        'hostname': host.provider_private_dns,
        'timeout': 3,
        'display_ssh_output': False,
        'key_filename': config.get_cloud_config_value(
            'private_key', vm_, __opts__, search_global=False, default=None
        ),
        'username': config.get_cloud_config_value(
            'ssh_username', vm_, __opts__, search_global=False, default=None
        )

    }


def regenerate_minion_keys(host, vm_, __opts__):
    logger.info('Regenerating minion keys for: {0}'.format(vm_['name']))

    # Kill existing master keys
    key_cli = salt.key.KeyCLI(__opts__)
    matches = key_cli.key.name_match(vm_['name'])
    if matches:
        key_cli.key.delete_key(match_dict=matches)

    # Kill remote master keys
    kwargs = get_ssh_kwargs(host, vm_, __opts__)
    tty = config.get_cloud_config_value(
        'tty', vm_, __opts__, default=True
    )
    sudo = config.get_cloud_config_value(
        'sudo', vm_, __opts__, default=True
    )
    salt.utils.cloud.root_cmd('rm -rf /etc/salt/pki', tty, sudo, **kwargs)

    # Generate new keys for the minion
    minion_pem, minion_pub = salt.utils.cloud.gen_keys(
        config.get_cloud_config_value('keysize', vm_, __opts__)
    )

    # Preauthorize the minion
    logger.info('Accepting key for {0}'.format(vm_['name']))
    key_id = vm_.get('id', vm_['name'])
    salt.utils.cloud.accept_key(
        __opts__['pki_dir'], minion_pub, key_id
    )

    return minion_pem, minion_pub


def ping_stack_hosts(stack):
    """
    Returns a set of hostnames in the stack that were reachable via
    a ping request.

    NOTE: This specifically targets the hosts in a stack instead of
    pinging all available hosts that salt is managing.
    """
    client = salt.client.LocalClient(settings.STACKDIO_CONFIG.salt_master_config)
    target = [host.hostname for host in stack.hosts.all()]

    ret = set()
    for val in client.cmd_iter(target, 'test.ping', expr_form='list'):
        ret.update(val.keys())
    return ret


def find_zombie_hosts(stack):
    """
    Returns a QuerySet of host objects in the given stack that were not
    reachable via a ping request.
    """
    pinged_hosts = ping_stack_hosts(stack)
    hostnames = set([host.hostname for host in stack.hosts.all()])
    zombies = hostnames - pinged_hosts
    if not zombies:
        return None
    return stack.hosts.filter(hostname__in=zombies)


def check_for_ssh(cloud_map, hosts):
    """
    Attempts to SSH to the given hosts.

    @param (stacks.models.Stack) - the stack the hosts belong to
    @param (list[stacks.models.Host]) - hosts to check for SSH
    @returns (list) - list of tuples (bool, Host) where the bool value is
    True if we could connect to Host over SSH, False otherwise
    """
    opts = get_salt_cloud_opts()
    vms = get_stack_vm_map(cloud_map)
    mapper = get_stack_mapper(cloud_map)
    result = []

    # Iterate over the given hosts. If the host hasn't been assigned a
    # hostname or is not physically running, there's nothing we can do
    # so we skip them
    for host in hosts:
        if host.hostname not in vms:
            continue

        # Build the standard vm_ object and inject some additional stuff
        # we'll need
        vm_ = vms[host.hostname]
        vm_provider_metadata = mapper.get_running_by_names(host.hostname)
        if not vm_provider_metadata:
            # host is not actually running so skip it
            continue

        provider, provider_type = vm_['provider'].split(':')
        vm_.update(
            vm_provider_metadata[provider][provider_type][vm_['name']]
        )

        # Pull some values we need to test for SSH
        key_filename = config.get_cloud_config_value(
            'private_key', vm_, opts, search_global=False, default=None
        )
        username = config.get_cloud_config_value(
            'ssh_username', vm_, opts, search_global=False, default=None
        )
        hostname = config.get_cloud_config_value(
            'private_ips', vm_, opts, search_global=False, default=None
        )

        # Test SSH connection
        ok = salt.utils.cloud.wait_for_passwd(
            hostname,
            key_filename=key_filename,
            username=username,
            ssh_timeout=1,  # 1 second timeout
            maxtries=3,     # 3 max tries per host
            trysleep=0.5,   # half second between tries
            display_ssh_output=False)

        result.append((ok, host))
    return result


def terminate_hosts(stack, hosts):
    """
    Uses salt-cloud to terminate the given list of hosts.

    @param (list[stacks.models.Host]) - the hosts to terminate.
    @returns None
    """

    opts = get_salt_cloud_opts()
    opts.update({
        'parallel': True
    })
    mapper = salt.cloud.Map(opts)
    hostnames = [h.hostname for h in hosts]
    logger.debug('Terminating hosts: {0}'.format(hostnames))
    mapper.destroy(hostnames)


def bootstrap_hosts(stack, hosts, parallel=True):
    """
    Iterates over the given `hosts` and executes the bootstrapping process
    via salt cloud.

    @param stack (stacks.models.Stack) - Stack object (should be the stack that
        owns the given `hosts`.
    @param hosts (QuerySet) - QuerySet of stacks.models.Host objects
    @param parallel (bool) - if True, we'll bootstrap in parallel using a
        multiprocessing Pool with a size determined by salt-cloud's config
        Defaults to True

    WARNING: This is not parallelized. My only hope is that the list is
    relatively small (e.g, only bootstrap hosts that were unsuccessful...see
    the `find_zombie_hosts` method)
    """
    __opts__ = get_salt_cloud_opts()
    dmap = get_stack_map_data(stack.generate_cloud_map())

    # Params list holds the dict objects that will be used during
    # the deploy process; this will be handed off to the multiprocessing
    # Pool as the "iterable" argument
    params = []
    for host in hosts:
        vm_ = dmap['existing'].get(host.hostname)
        if vm_ is None:
            continue

        # Regenerate minion keys which will kill the keys for this host
        # on the master as well as the pki directory on the minion to
        # ensure we have the same keys in use or else the automatic
        # key acceptance will fail and the minion will still be in limbo
        minion_pem, minion_pub = regenerate_minion_keys(host, vm_, __opts__)

        # Add the keys
        vm_['priv_key'] = minion_pem
        vm_['pub_key'] = minion_pub

        d = {
            'host_obj': host,
            'vm_': vm_,
            '__opts__': __opts__,
        }

        # if we're not deploying in parallel, simply pass the dict
        # in, else we'll shove the dict into the params list
        if not parallel:
            deploy_vm(d)
        else:
            params.append(d)

    # Parallel deployment using multiprocessing Pool. The size of the
    # Pool object is either pulled from salt-cloud's config file or
    # the length of `params` is used. Note, it's highly recommended to
    # set the `pool_size` parameter in the salt-cloud config file to
    # prevent issues with larger pool sizes
    if parallel and len(params) > 0:
        pool_size = __opts__.get('pool_size', len(params))
        multiprocessing.Pool(pool_size).map(
            func=deploy_vm,
            iterable=params
        )


def deploy_vm(params):
    """
    Basically duplicating the deploy logic from `salt.cloud.clouds.ec2::create`
    so we can bootstrap minions whenever needed. Ideally, this would be handled
    in salt-cloud directly, but for now it's easier to handle this on our end.

    @param params (dict) - a dictionary containing all the necessary
        params we need and are defined below:

    @params[host_obj] (stacks.models.Host) - a Django ORM Host object
    @params[vm_] (dict) - the vm data structure that salt likes to use
    @params[__opts__] (dict) - the big config object that salt passes
        around to all of its modules. See `get_salt_cloud_opts`
    """

    host_obj = params['host_obj']
    vm_ = params['vm_']
    __opts__ = params['__opts__']

    logger.info('Deploying minion on VM: {0}'.format(vm_['name']))

    # Start gathering the information we need to build up the deploy kwargs
    # object that will be handed to `salt.utils.cloud.deploy_script`

    # The SSH username we'll use for pushing files and remote execution. This
    # should already be defined in the cloud image this host is using.
    username = config.get_cloud_config_value(
        'ssh_username', vm_, __opts__, search_global=False, default=None
    )

    # The private key, along with ssh_username above, is necessary for SSH
    key_filename = config.get_cloud_config_value(
        'private_key', vm_, __opts__, search_global=False, default=None
    )

    # Which deploy script will be run to bootstrap the minions. This is pre-
    # defined in the cloud image/profile for the host.
    deploy_script = salt.utils.cloud.os_script(
        config.get_cloud_config_value('script', vm_, __opts__),
        vm_,
        __opts__,
        salt.utils.cloud.salt_config_to_yaml(
            salt.utils.cloud.minion_config(__opts__, vm_)
        )
    )

    # Generate the master's public fingerprint
    master_finger = salt.utils.pem_finger(os.path.join(
        __opts__['pki_dir'], 'master.pub'
    ))
    vm_['master_finger'] = master_finger

    # The big deploy kwargs object. This is roughly the exact same as that
    # in the salt.cloud.clouds.ec2::create method.
    deploy_kwargs = {
        'host': host_obj.provider_private_dns,
        'hostname': host_obj.provider_private_dns,
        'username': username,
        'key_filename': key_filename,
        'tmp_dir': config.get_cloud_config_value(
            'tmp_dir', vm_, __opts__, default='/tmp/.saltcloud'
        ),
        'deploy_command': config.get_cloud_config_value(
            'deploy_command', vm_, __opts__,
            default='/tmp/.saltcloud/deploy.sh',
        ),
        'tty': config.get_cloud_config_value(
            'tty', vm_, __opts__, default=True
        ),
        'script': deploy_script,
        'name': vm_['name'],
        'sudo': config.get_cloud_config_value(
            'sudo', vm_, __opts__, default=(username != 'root')
        ),
        'sudo_password': config.get_cloud_config_value(
            'sudo_password', vm_, __opts__, default=None
        ),
        'start_action': __opts__['start_action'],
        'parallel': False,
        'conf_file': __opts__['conf_file'],
        'sock_dir': __opts__['sock_dir'],
        'keep_tmp': True,
        'preseed_minion_keys': vm_.get('preseed_minion_keys', None),
        'display_ssh_output': False,
        'minion_conf': salt.utils.cloud.minion_config(__opts__, vm_),
        'script_args': config.get_cloud_config_value(
            'script_args', vm_, __opts__
        ),
        'script_env': config.get_cloud_config_value(
            'script_env', vm_, __opts__
        ),
        'make_minion': config.get_cloud_config_value(
            'make_minion', vm_, __opts__, default=True
        ),
        'minion_pem': vm_['priv_key'],
        'minion_pub': vm_['pub_key'],
    }

    # TODO(abemusic): log this to a file instead of dumping to celery
    logger.info('Executing deploy_script for {0}'.format(vm_['name']))
    try:
        deployed = salt.utils.cloud.deploy_script(**deploy_kwargs)
        if deployed:
            logger.info('Salt installed on {name}'.format(**vm_))
        else:
            logger.error('Failed to start Salt on Cloud VM '
                         '{name}'.format(**vm_))
    except Exception:
        logger.exception('Unhandled exception while deploying minion')
        deployed = False

    # TODO(abemusic): the create method in the EC2 driver currently handles
    # the creation logic for EBS volumes. We should be checking for those
    # volumes and creating them if necessary here.

    return deployed


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


def unmod_hosts_map(cloud_map, *args):
    """
    For debug method purpose only
    """
    for host_data in cloud_map.values():
        for k in args:
            if k in host_data:
                del host_data[k]

    return cloud_map


def create_zombies(stack, n):
    """
    For the given stack, will randomly select `n` hosts and kill the
    salt-minion service that should already be running on the host.

    @param (stacks.models.Stack) stack - the stack we're targeting
    @param (int) n - the number of randomly selected hosts to zombify
    @returns (None)
    """

    # Random sampling of n hosts
    hosts = random.sample(stack.hosts.all(), n)
    if not hosts:
        return

    client = salt.client.LocalClient(
        settings.STACKDIO_CONFIG.salt_master_config
    )
    result = list(client.cmd_iter(
        [h.hostname for h in hosts],
        'service.stop',
        arg=('salt-minion',),
        expr_form='list'
    ))
    logger.info(result)
