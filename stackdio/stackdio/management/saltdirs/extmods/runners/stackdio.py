# Import std libs
import logging

# Import salt libs
import salt.overstate
import salt.output
from salt.exceptions import SaltInvocationError

logger = logging.getLogger(__name__)

if '__opts__' not in globals():
    __opts__ = {}


class StackdioOverState(salt.overstate.OverState):

    def _stage_list(self, match):
        '''
        Return a list of ids cleared for a given stage
        Use cmd_iter instead so that we always get all the
        '''
        raw = {}
        if isinstance(match, list):
            match = ' or '.join(match)
        ping_iter = self.local.cmd_iter(match, 'test.ping', expr_form='compound')
        for minion in ping_iter:
            for k, v in minion.items():
                raw[k] = v
        return raw.keys()


def orchestrate(saltenv='base', os_fn=None):
    '''
    Borrowed and adpated from slat.runners.state::over()

    Modifying this to provide output more suitable to automating our
    orchestration in stackd.io

    CLI Examples:

    .. code-block:: bash

        salt-run stackdio.orchestrate <env> </path/to/orchestration.file>
    '''
    try:
        overstate = StackdioOverState(__opts__, saltenv, os_fn)
    except IOError as exc:
        raise SaltInvocationError(
            '{0}: {1!r}'.format(exc.strerror, exc.filename)
        )
    # ret = {}
    for stage in overstate.stages_iter():
        if isinstance(stage, dict):
            # This is highstate data
            yield stage
            # for host, result in stage.items():
            #     if '_|-' in host:
            #         ret.setdefault('__stage__error__', []).append(result)
            #     else:
            #         ret.setdefault(host, []).append(result)
        elif isinstance(stage, list):
            # we don't care about output from stage executions
            continue
    # salt.output.display_output(ret, 'yaml', opts=__opts__)
    # return overstate.over_run
