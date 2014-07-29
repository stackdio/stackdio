import logging
from operator import or_

from . import tasks

logger = logging.getLogger(__name__)


class WorkflowOptions(object):

    def __init__(self):
        pass


class BaseWorkflow(object):
    _options_class = WorkflowOptions

    def __init__(self, stack, host_ids=None, opts=None):
        self.stack = stack
        self.host_ids = host_ids
        self.opts = self._options_class()

    def task_list(self):
        return []

    def execute(self):
        task_chain = reduce(or_, self.task_list())
        task_chain()


class LaunchWorkflowOptions(WorkflowOptions):
    def __init__(self):
        super(LaunchWorkflowOptions, self).__init__()
        self.provision = True
        self.max_retries = 2
        self.parallel = True
        self.simulate_launch_failures = False
        self.simulate_ssh_failures = False
        self.simulate_zombies = False
        self.failure_percent = 0.3


class LaunchWorkflow(BaseWorkflow):
    '''
    Encapsulates all tasks required to launch a new stack or new hosts into
    a stack.
    '''
    _options_class = LaunchWorkflowOptions

    def task_list(self):
        stack_id = self.stack.pk
        host_ids = self.host_ids
        opts = self.opts

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
            tasks.cure_zombies.si(stack_id, max_retries=opts.max_retries),
            tasks.update_metadata.si(stack_id, host_ids=host_ids),
            tasks.tag_infrastructure.si(stack_id, host_ids=self.host_ids),
            tasks.register_dns.si(stack_id, host_ids=self.host_ids),
            tasks.ping.si(stack_id),
            tasks.sync_all.si(stack_id),
            tasks.highstate.si(stack_id, max_retries=opts.max_retries)
        ]
        if opts.provision:
            l.append(tasks.orchestrate.si(stack_id,
                                          max_retries=opts.max_retries))
        l.append(tasks.finish_stack.si(stack_id))
        return l


class DestroyWorkflowOptions(WorkflowOptions):
    def __init__(self):
        super(DestroyWorkflowOptions, self).__init__()
        self.parallel = True


class DestroyHostsWorkflow(BaseWorkflow):
    '''
    Encapsulates all tasks required to destroy a set of hosts on a stack.
    '''
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
    '''
    Encapsulates all tasks required to destroy an entire stack.
    '''
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
