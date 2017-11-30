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

from __future__ import absolute_import, unicode_literals

import logging

from celery import chain
from stackdio.api.environments import tasks
from stackdio.core.constants import Action

logger = logging.getLogger(__name__)


class WorkflowOptions(object):
    DEFAULTS = {
        'max_attempts': 3,
    }

    def __init__(self, opts):
        self.user_opts = opts

    def __getattr__(self, item):
        if item in self.user_opts:
            return self.user_opts[item]
        elif item in self.DEFAULTS:
            return self.DEFAULTS[item]
        else:
            raise AttributeError(item)


class BaseWorkflow(object):
    _options_class = WorkflowOptions

    def __init__(self, environment, opts=None):
        if opts is None:
            opts = {}
        self.environment = environment
        self.opts = self._options_class(opts)

    def task_list(self):
        return []

    def execute(self):
        task_chain = chain(*self.task_list())
        task_chain.apply_async()


class ActionWorkflow(BaseWorkflow):
    """
    Runs an action
    """

    def __init__(self, environment, action, args):
        super(ActionWorkflow, self).__init__(environment)
        self.action = action
        self.args = args

    def task_list(self):
        base_tasks = {
            Action.PROPAGATE_SSH: [
                tasks.propagate_ssh.si(self.environment.name),
            ],
            Action.SINGLE_SLS: [
                tasks.single_sls.si(self.environment.name, arg['component'], arg.get('host_target'))
                for arg in self.args
            ],
        }

        # Start off with the base
        task_list = base_tasks.get(self.action, [])

        # reprovisioning requires us to execute the provisioning tasks
        if self.action in (Action.PROVISION, Action.ORCHESTRATE):
            task_list.append(tasks.sync_all.si(self.environment.name))

        if self.action in (Action.PROVISION,):
            task_list.append(tasks.highstate.si(self.environment.name))

        if self.action in (Action.PROVISION, Action.ORCHESTRATE):
            task_list.append(tasks.orchestrate.si(self.environment.name, self.opts.max_attempts))

        # Always finish the environment
        task_list.append(tasks.finish_environment.si(self.environment.name))

        return task_list
