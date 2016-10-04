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

    @classmethod
    def aggregate(cls, health_list):
        # Make sure everything in the list is a valid health
        assert len([h for h in health_list if h not in vars(cls)]) == 0

        if len(health_list) == 0:
            # We can get an empty list sometimes when we're deleting a stack, so we'll
            # just aggregate that to unknown
            return cls.UNKNOWN
        elif cls.UNHEALTHY in health_list:
            return cls.UNHEALTHY
        elif cls.UNSTABLE in health_list:
            return cls.UNSTABLE
        elif cls.UNKNOWN in health_list:
            return cls.UNKNOWN
        elif cls.HEALTHY in health_list:
            return cls.HEALTHY

        raise ValueError('This state should never be reached...  Make sure you are '
                         'assigning proper health values')


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


class Action(object):
    """
    Define valid actions that can be performed on stacks
    """
    LAUNCH = 'launch'
    TERMINATE = 'terminate'

    PAUSE = 'pause'
    RESUME = 'resume'

    ORCHESTRATE = 'orchestrate'
    PROVISION = 'provision'
    PROPAGATE_SSH = 'propagate-ssh'

    ALL = [LAUNCH, TERMINATE, PAUSE, RESUME, ORCHESTRATE, PROVISION, PROPAGATE_SSH]


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
               Action.PROPAGATE_SSH, Action.PROVISION, Action.ORCHESTRATE],
        PAUSED: [Action.RESUME, Action.TERMINATE],
        TERMINATED: [Action.LAUNCH],
        DEAD: [Action.LAUNCH],
    }

    # states when deleting a stack is valid
    can_delete = [IDLE, PAUSED, TERMINATED, DEAD]
