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

from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
from functools import wraps

import salt.client
import salt.cloud
import salt.key
import salt.syspaths
import salt.utils
import salt.utils.cloud
import six
from msgpack.exceptions import ExtraData

from stackdio.salt.utils.logging import setup_logfile_logger

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()


SALT_CLOUD_CACHE_DIR = os.path.join(salt.syspaths.CACHE_DIR, 'cloud')


def catch_salt_cloud_map_failures(retry_times):
    """
    Decorator to catch common salt errors and automatically retry
    """
    if retry_times <= 0:
        raise ValueError('retry_times must be a positive integer')

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            num_errors = 0

            # Only loop until we've failed too many times
            while num_errors < retry_times:
                try:
                    # Call our function & return it's return val
                    return func(*args, **kwargs)
                except ExtraData as e:
                    logger.info('Received ExtraData, retrying: {0}'.format(e))
                    # Blow away the salt cloud cache and try again
                    os.remove(os.path.join(SALT_CLOUD_CACHE_DIR, 'index.p'))
                    num_errors += 1
                except salt.cloud.SaltCloudSystemExit as e:
                    if 'extra data' in six.text_type(e):
                        logger.info('Received ExtraData, retrying: {0}'.format(e))
                        # Blow away the salt cloud cache and try again
                        os.remove(os.path.join(SALT_CLOUD_CACHE_DIR, 'index.p'))
                        num_errors += 1
                    else:
                        raise
                except TypeError as e:
                    if 'NoneType' in six.text_type(e):
                        logger.info('Received TypeError, retrying: {0}'.format(e))
                        # Blow away the salt cloud cache and try again
                        os.remove(os.path.join(SALT_CLOUD_CACHE_DIR, 'index.p'))
                        num_errors += 1
                    else:
                        raise

            # If we make it out of the loop, we failed
            raise salt.cloud.SaltCloudSystemExit(
                'Maximum number of errors reached while launching stack.'
            )

        return wrapper

    return decorator


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

    def delete_map(self, query='list_nodes'):  # pylint: disable=useless-super-delegation
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
                    for rendered_profile, data in self.rendered_map.items():
                        provider = self.opts['profiles'][rendered_profile]['provider'].split(':')[0]
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

        try:
            mapper = StackdioSaltCloudMap(opts)
            mapper.rendered_map = cloud_map

            @catch_salt_cloud_map_failures(retry_times=5)
            def do_launch():
                # Do the launch
                dmap = mapper.map_data()
                return mapper.run_map(dmap)

            # This should catch our failures and retry
            return salt.utils.cloud.simple_types_filter(do_launch())

        finally:
            # Cancel the logging, but make sure it still gets cancelled if an exception is thrown
            root_logger.removeHandler(handler)

    def destroy_map(self, cloud_map, hosts, **kwargs):
        """
        Destroy the named VMs
        """
        kwarg = kwargs.copy()
        kwarg['destroy'] = True
        mapper = StackdioSaltCloudMap(self._opts_defaults(**kwarg))
        mapper.rendered_map = cloud_map

        # This should catch our failures and retry
        return self._do_destroy(mapper, hosts)

    @catch_salt_cloud_map_failures(retry_times=5)
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
