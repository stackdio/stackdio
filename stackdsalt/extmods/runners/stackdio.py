# Import std libs
import logging

# Import salt libs
import salt.overstate
import salt.output

logger = logging.getLogger(__name__)


def orchestrate(saltenv='base', os_fn=None):
    '''
    Execute an overstate sequence to orchestrate the executing of states
    over a group of systems

    CLI Examples:

    .. code-block:: bash

        salt-run state.over base /path/to/myoverstate.sls
    '''
    ret = {}
    overstate = salt.overstate.OverState(__opts__, saltenv, os_fn) # NOQA
    for stage in overstate.stages_iter():
        if not isinstance(stage, dict):
            continue
        for key, val in stage.items():
            if '_|-' in key:
                ret.setdefault('__stage__error__', []) \
                    .append(val)
            elif isinstance(val, list):
                ret.setdefault(key, []) \
                    .extend(val)
            else:
                ret.setdefault(key, []) \
                    .append(val)
    salt.output.display_output(ret, 'yaml', opts=__opts__) # NOQA
    return overstate.over_run
