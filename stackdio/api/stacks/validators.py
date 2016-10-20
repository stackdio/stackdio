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

from __future__ import unicode_literals

import collections

from rest_framework.serializers import ValidationError
from stackdio.core.constants import Health


def can_run_component_on_stack(component, stack):
    host_list = []

    component_order = None

    # Find all the hosts that contain the component
    for host in stack.hosts.all():

        # Maintain a map of order -> unhealthy components
        unhealthy_components = collections.defaultdict(list)

        # Order them by their order here, so that we're guaranteed to get all of a component's
        # dependencies before we arrive at the component
        for fc in host.formula_components.order_by('order'):
            if fc.sls_path == component:
                # This host contains the component we're looking for, so add it to the
                # list of hosts to orchestrate
                host_list.append(host)

                # Keey track of it's order so we can validate all of it's dependencies
                if component_order is None:
                    component_order = fc.order
                elif component_order != fc.order:
                    raise ValidationError('Invalid component ordering!! '
                                          'This error should have been caught before now...')

                # Check to make sure all orders less than the current order are healthy
                errors = []
                for i in range(component_order):
                    for c in unhealthy_components[i]:
                        errors.append(c.sls_path)

                if errors:
                    # We've got some unhealthy dependencies, so raise an exception
                    err_msg = ('Components {0} are not healthy, cannot run {1} '
                               'because it depends on them'.format(', '.join(errors), component))
                    raise ValidationError(err_msg)

                # Should be done validating here
                break

            else:
                # This is NOT the component we're looking for, so check it's health and add
                # it to the unhealthy list if it's not healthy
                metadata = host.get_metadata_for_component(fc)

                # Check the health
                if metadata.health != Health.HEALTHY:
                    unhealthy_components[fc.order].append(fc)

    if not host_list:
        raise ValidationError('No hosts matched the given component.')

    return host_list
