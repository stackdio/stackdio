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


"""
Extension of the built-in mount module to add a few methods we need for
when operating with ebs volumes.
"""

import salt.utils
import os.path

__virtualname__ = 'mount'


def __virtual__():
    """
    Only work on POSIX-like systems
    """
    # win_file takes care of windows
    if salt.utils.is_windows():
        return False
    return 'mount'


def find_ebs_device(device):
    """
    Tests to see if `device` exists or the xvd derivative. Returns
    None if no device could be found.

    CLI Example::

        salt '*' mount.find_ebs_device /dev/sdj
        salt '*' mount.find_ebs_device /dev/xvdj

    """
    if os.path.exists(device):
        return device

    if device.startswith('/dev/sd'):
        if os.path.exists('/dev/xvda'):
            new_device_letter = device[7]
            device_pattern = '/dev/xvd{}{}'
        elif os.path.exists('/dev/xvde'):
            # Some systems start with /dev/xvde instead of /dev/xvda,
            # so we need to add 4 to the current letter
            new_device_letter = chr(ord(device[7]) + 4)
            device_pattern = '/dev/xvd{}{}'
        elif os.path.exists('/dev/nvme0n1'):
            # Some devices use the NVMe naming scheme, so we need to convert the letter to a number
            new_device_letter = ord(device[7]) - ord('a')
            device_pattern = '/dev/nvme{}n1{}'
        else:
            return None

        device_partition = device[8:]

        new_device = device_pattern.format(new_device_letter, device_partition)
        if os.path.exists(new_device):
            return new_device

    return None
