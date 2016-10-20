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


class Health(object):
    """
    Define valid values for the health of stacks / hosts / components
    """
    HEALTHY = 'healthy'  # green
    UNSTABLE = 'unstable'  # yellow
    UNHEALTHY = 'unhealthy'  # red
    UNKNOWN = 'unknown'  # grey

    priority = {
        UNHEALTHY: 3,
        UNSTABLE: 2,
        UNKNOWN: 1,
        HEALTHY: 0,
    }

    @classmethod
    def aggregate(cls, health_list):
        # Make sure everything in the list is a valid health
        if len([h for h in health_list if h not in cls.priority]) != 0:
            raise ValueError('An invalid health was passed in.')

        if len(health_list) == 0:
            # We can get an empty list sometimes when we're deleting a stack, so we'll
            # just aggregate that to unknown
            return cls.UNKNOWN

        sorted_healths = sorted(health_list, key=lambda x: cls.priority[x], reverse=True)

        return sorted_healths[0]


class ComponentStatus(object):
    """
    Define valid values for the status of a component
    """
    # Unstable statuses
    QUEUED = 'queued'
    RUNNING = 'running'

    # Stable statuses
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    UNKNOWN = 'unknown'

    priority = {
        FAILED: 5,
        CANCELLED: 4,
        RUNNING: 3,
        UNKNOWN: 2,
        QUEUED: 1,
        SUCCEEDED: 0,
    }

    @classmethod
    def aggregate(cls, status_list):
        # Make sure everything in the list is a valid status
        if len([s for s in status_list if s not in cls.priority]) != 0:
            raise ValueError('An invalid status was passed in.')

        if len(status_list) == 0:
            # We can get an empty list sometimes when we're deleting a stack, so we'll
            # just aggregate that to unknown
            return cls.UNKNOWN

        sorted_statuses = sorted(status_list, key=lambda x: cls.priority[x], reverse=True)

        return sorted_statuses[0]


class Action(object):
    """
    Define valid actions that can be performed on stacks
    """
    LAUNCH = 'launch'
    TERMINATE = 'terminate'

    PAUSE = 'pause'
    RESUME = 'resume'

    ORCHESTRATE = 'orchestrate'
    SINGLE_SLS = 'single-sls'
    PROVISION = 'provision'
    PROPAGATE_SSH = 'propagate-ssh'

    ALL = [LAUNCH, TERMINATE, PAUSE, RESUME, ORCHESTRATE, PROVISION, SINGLE_SLS, PROPAGATE_SSH]


class Activity(object):
    """
    Define valid states for the activity field on stacks / hosts
    """
    # Ephemeral states
    UNKNOWN = 'unknown'
    QUEUED = 'queued'

    # Normal workflow
    LAUNCHING = 'launching'
    PROVISIONING = 'provisioning'
    ORCHESTRATING = 'orchestrating'
    IDLE = ''

    # Pausing workflow
    PAUSING = 'pausing'
    PAUSED = 'paused'
    RESUMING = 'resuming'

    # Terminating workflow
    TERMINATING = 'terminating'
    TERMINATED = 'terminated'

    # Command workflow
    EXECUTING = 'executing'

    # Dead
    DEAD = 'dead'

    ALL = (
        (UNKNOWN, UNKNOWN),
        (QUEUED, QUEUED),
        (LAUNCHING, LAUNCHING),
        (PROVISIONING, PROVISIONING),
        (ORCHESTRATING, ORCHESTRATING),
        (IDLE, IDLE),
        (PAUSING, PAUSING),
        (PAUSED, PAUSED),
        (RESUMING, RESUMING),
        (TERMINATING, TERMINATING),
        (TERMINATED, TERMINATED),
        (EXECUTING, EXECUTING),
        (DEAD, DEAD),
    )

    # For stacks
    action_map = {
        IDLE: [Action.LAUNCH, Action.TERMINATE, Action.PAUSE,
               Action.PROPAGATE_SSH, Action.PROVISION, Action.ORCHESTRATE,
               Action.SINGLE_SLS],
        PAUSED: [Action.RESUME, Action.TERMINATE],
        TERMINATED: [Action.LAUNCH],
        DEAD: [Action.LAUNCH],
    }

    # states when deleting a stack is valid
    can_delete = [IDLE, PAUSED, TERMINATED, DEAD]
