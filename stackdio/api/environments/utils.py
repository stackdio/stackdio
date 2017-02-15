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

from stackdio.core.constants import Action, ComponentStatus

logger = logging.getLogger(__name__)


def filter_actions(user, stack, actions):
    ret = []
    for action in actions:
        the_action = action
        if action == Action.PROPAGATE_SSH:
            the_action = 'admin'
        if user.has_perm('stacks.{0}_stack'.format(the_action.lower()), stack):
            ret.append(action)

    return ret


def set_component_statuses(environment, orch_result):

    for sls_path, sls_result in orch_result['succeeded_sls'].items():
        environment.set_component_status(sls_path,
                                         ComponentStatus.SUCCEEDED,
                                         sls_result['succeeded_hosts'])

    for sls_path, sls_result in orch_result['failed_sls'].items():
        # Set the status to succeeded on the hosts that succeeded
        environment.set_component_status(sls_path,
                                         ComponentStatus.SUCCEEDED,
                                         sls_result['succeeded_hosts'])

        # Set the status to failed on the hosts that failed
        environment.set_component_status(sls_path,
                                         ComponentStatus.FAILED,
                                         sls_result['failed_hosts'])

    # Just ignoring the cancelled SLS for now
    # (since we don't have a way of knowing what hosts to set to cancelled)
