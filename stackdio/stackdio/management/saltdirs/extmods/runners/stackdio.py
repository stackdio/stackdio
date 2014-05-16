# Import std libs
import logging

# Import salt libs
import salt.overstate
import salt.output
from salt.exceptions import SaltInvocationError

logger = logging.getLogger(__name__)

if '__opts__' not in globals():
    __opts__ = {}


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
        overstate = salt.overstate.OverState(__opts__, saltenv, os_fn)
    except IOError as exc:
        raise SaltInvocationError(
            '{0}: {1!r}'.format(exc.strerror, exc.filename)
        )
    ret = {}
    for stage in overstate.stages_iter():
        if isinstance(stage, dict):
            # This is highstate data
            for host, result in stage.items():
                if '_|-' in host:
                    ret.setdefault('__stage__error__', []).append(result)
                else:
                    ret.setdefault(host, []).append(result)
        elif isinstance(stage, list):
            # we don't care about output from stage executions
            continue
    salt.output.display_output(ret, 'yaml', opts=__opts__)
    return overstate.over_run
