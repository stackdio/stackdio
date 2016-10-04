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


"""
Extension of the built-in extfs module to add a few methods we need for
when operating with ebs volumes.
"""

import salt.utils

__virtualname__ = 'extfs'


def __virtual__():
    """
    Only work on POSIX-like systems
    """
    # win_file takes care of windows
    if salt.utils.is_windows():
        return False
    return 'extfs'


def fs_exists(device):
    """
    Check to see if there is already a filesystem on the device

    CLI Example::

        salt '*' extfs.fs_exists /dev/sdj
        salt '*' extfs.fs_exists /dev/xvdj
    """
    cmd = 'dumpe2fs {0}'.format(device)
    out = __salt__['cmd.run'](cmd, python_shell=False)

    return 'Couldn\'t find valid filesystem superblock' not in out
