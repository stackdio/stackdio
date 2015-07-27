# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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


import logging
from operator import or_

from . import tasks

logger = logging.getLogger(__name__)


class WorkflowOptions(object):
    DEFAULTS = {}

    def __init__(self, opts):
        self.user_opts = opts

    def __getattr__(self, item):
        if item in self.user_opts:
            return self.user_opts[item]
        elif item in self.DEFAULTS:
            return self.DEFAULTS[item]
        else:
            raise AttributeError(item)


class LaunchWorkflowOptions(WorkflowOptions):
    DEFAULTS = {
        'max_retries': 2,
        # Skips launching if set to False
        'launch': True,
        'provision': True,

        # Launches in parallel mode if set to True
        'parallel': True,

        # See stacks.tasks::launch_hosts for information on these params
        'simulate_launch_failures': False,
        'simulate_ssh_failures': False,
        'simulate_zombies': False,
        'failure_percent': 0.3,
    }


class DestroyWorkflowOptions(WorkflowOptions):
    DEFAULTS = {
        'parallel': True,
    }


class BaseWorkflow(object):
    _options_class = WorkflowOptions

    def __init__(self, stack, host_ids=None, opts=None):
        if opts is None:
            opts = {}
        self.stack = stack
        self.host_ids = host_ids
        self.opts = self._options_class(opts)

    def task_list(self):
        return []

    def execute(self):
        task_chain = reduce(or_, self.task_list())
        task_chain()


class LaunchWorkflow(BaseWorkflow):
    """
    Encapsulates all tasks required to launch a new stack or new hosts into
    a stack.
    """
    _options_class = LaunchWorkflowOptions

    def task_list(self):
        stack_id = self.stack.id
        host_ids = self.host_ids
        opts = self.opts

        if not opts.launch:
            return []

        l = [
            tasks.launch_hosts.si(
                stack_id,
                parallel=opts.parallel,
                max_retries=opts.max_retries,
                simulate_launch_failures=opts.simulate_launch_failures,
                simulate_ssh_failures=opts.simulate_ssh_failures,
                simulate_zombies=opts.simulate_zombies,
                failure_percent=opts.failure_percent
            ),
            tasks.update_metadata.si(stack_id, host_ids=host_ids),
            tasks.cure_zombies.si(stack_id, max_retries=opts.max_retries),
            tasks.update_metadata.si(stack_id, host_ids=host_ids),
            tasks.tag_infrastructure.si(stack_id, host_ids=self.host_ids),
            tasks.register_dns.si(stack_id, host_ids=self.host_ids),
            tasks.ping.si(stack_id),
            tasks.sync_all.si(stack_id),
            tasks.highstate.si(stack_id, max_retries=opts.max_retries),
            tasks.global_orchestrate.si(stack_id,
                                        max_retries=opts.max_retries)
        ]
        if opts.provision:
            l.append(tasks.orchestrate.si(stack_id,
                                          max_retries=opts.max_retries))
        l.append(tasks.finish_stack.si(stack_id))

        self.stack.set_status('queued', tasks.Stack.PENDING,
                              'Stack has been submitted to launch queue.')

        return l


class DestroyHostsWorkflow(BaseWorkflow):
    """
    Encapsulates all tasks required to destroy a set of hosts on a stack.
    """
    _options_class = DestroyWorkflowOptions

    def task_list(self):
        stack_id = self.stack.pk
        host_ids = self.host_ids

        return [
            tasks.update_metadata.si(stack_id, host_ids=host_ids),
            tasks.register_volume_delete.si(stack_id, host_ids=host_ids),
            tasks.unregister_dns.si(stack_id, host_ids=host_ids),
            tasks.destroy_hosts.si(stack_id,
                                   host_ids=host_ids,
                                   delete_security_groups=False,
                                   parallel=self.opts.parallel),
        ]


class DestroyStackWorkflow(BaseWorkflow):
    """
    Encapsulates all tasks required to destroy an entire stack.
    """
    _options_class = DestroyWorkflowOptions

    def __init__(self, stack, opts=None):
        super(DestroyStackWorkflow, self).__init__(stack, opts=opts)

        # Force host_ids to None since we're destroying the entire stack
        self.host_ids = None

    def task_list(self):
        stack_id = self.stack.pk
        return [
            tasks.update_metadata.si(stack_id, remove_absent=False),
            tasks.register_volume_delete.si(stack_id),
            tasks.unregister_dns.si(stack_id),
            tasks.destroy_hosts.si(stack_id, parallel=self.opts.parallel),
            tasks.destroy_stack.si(stack_id),
        ]
