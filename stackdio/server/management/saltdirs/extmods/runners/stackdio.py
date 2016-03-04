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


# Import std libs
import logging

# Import salt libs
import salt.minion
import salt.output
from salt.exceptions import SaltInvocationError

logger = logging.getLogger(__name__)

if '__opts__' not in globals():
    __opts__ = {}


class StackdioMasterMinion(salt.minion.MasterMinion):
    pass


def orchestrate(mods, saltenv='base', test=None, exclude=None, pillar=None):
    """
    Borrowed and adapted from salt.runners.state::orchestrate()

    Modifying this to return a generator instead of all the data at once

    CLI Examples:

    .. code-block:: bash

        salt-run stackdio.orchestrate </path/to/orchestration.file> <env>
    """
    if pillar is not None and not isinstance(pillar, dict):
        raise SaltInvocationError(
            'Pillar data must be formatted as a dictionary'
        )
    __opts__['file_client'] = 'local'
    minion = StackdioMasterMinion(__opts__)
    running = minion.functions['state.sls'](
            mods,
            saltenv,
            test,
            exclude,
            pillar=pillar)
    ret = {minion.opts['id']: running, 'outputter': 'highstate'}
    return ret
