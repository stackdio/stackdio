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
        """
        Return a list of ids cleared for a given stage
        Use cmd_iter instead of cmd so that large clusters don't have timeout issues
        """
        if isinstance(match, list):
            match = ' or '.join(match)
        raw = self.local.cmd_iter(match, 'test.ping', expr_form='compound')
        fret = []
        for ret in raw:
            for minion in ret:
                fret.append(minion)
        return sorted(fret)

    def call_stage(self, name, stage):
        """
        Check if a stage has any requisites and run them first

        Re write this to have the stage just get matched directly rather than
        using test.ping
        """
        fun = 'state.highstate'
        arg = ()
        req_fail = {name: {}}

        if 'sls' in stage:
            fun = 'state.sls'
            arg = (','.join(stage['sls']), self.saltenv)

        elif 'function' in stage or 'fun' in stage:
            fun_d = stage.get('function', stage.get('fun'))
            if not fun_d:
                # Function dict is empty
                yield {name: {}}
            if isinstance(fun_d, str):
                fun = fun_d
            elif isinstance(fun_d, dict):
                fun = fun_d.keys()[0]
                arg = fun_d[fun]
            else:
                yield {name: {}}

        reqs = stage.get('require') or []
        for req in reqs:

            if req in self.over_run:
                # The req has been called, check it
                self.over_run, req_fail = self._check_results(req,
                    name, self.over_run, req_fail)

            elif req not in self.names:
                # Req does not exist
                tag_name = 'No_|-Req_|-fail_|-None'
                failure = {
                    tag_name: {
                        'ret': {
                            'result': False,
                            'comment': 'Requisite {0} not found'.format(req),
                            'name': 'Requisite Failure',
                            'changes': {},
                            '__run_num__': 0,
                        },
                        'retcode': 253,
                        'success': False,
                        'fun': 'req.fail',
                    }
                }
                self.over_run[name] = failure
                req_fail[name].update(failure)

            else:
                # Req has not be called
                for comp in self.over:
                    rname = comp.keys()[0]
                    if req == rname:
                        rstage = comp[rname]
                        v_stage = self.verify_stage(rstage)
                        if isinstance(v_stage, list):
                            yield {rname: v_stage}
                        else:
                            yield self.call_stage(rname, rstage)
                            # Verify that the previous yield returned
                            # successfully and update req_fail
                            self.over_run, req_fail = self._check_results(req,
                                name, self.over_run, req_fail)

        # endfor
        if req_fail[name]:
            yield req_fail
        else:
            ret = {}
            tgt = stage['match']
            cmd_kwargs = {
                'tgt': tgt,
                'fun': fun,
                'arg': arg,
                'expr_form': 'compound',
                'raw': True,
            }

            for minion in self.local.cmd_iter(**cmd_kwargs):
                if all(key not in minion for key in ('id', 'return', 'fun')):
                    continue
                ret.update({
                    minion['id']: {
                        'ret': minion['return'],
                        'fun': minion['fun'],
                        'retcode': minion.get('retcode', 0),
                        'success': minion.get('success', True),
                    }
                })
            self.over_run[name] = ret
            yield {name: ret}


def orchestrate(saltenv='base', os_fn=None):
    """
    Borrowed and adapted from salt.runners.state::over()

    Modifying this to return a generator instead of all the data at once

    CLI Examples:

    .. code-block:: bash

        salt-run stackdio.orchestrate <env> </path/to/orchestration.file>
    """
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

        # We don't care about anything but the highstate data
    # salt.output.display_output(ret, 'yaml', opts=__opts__)
    # return overstate.over_run
