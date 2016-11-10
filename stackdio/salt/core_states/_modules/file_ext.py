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
Extension of the built-in file module to support an arbitrary `exists` method
for knowing if a file, directory, device, symlink, etc exists or not. The
existing methods `file_exists` and `directory_exists` only look at those
types, so there's not a convenient way of checking if /dev/xvdj exists for
example.
"""

import salt.utils
import os.path

__virtualname__ = 'file'


def __virtual__():
    """
    Only work on POSIX-like systems
    """
    # win_file takes care of windows
    if salt.utils.is_windows():
        return False
    return 'file'


def exists(path):
    """
    Tests to see if a path exists.  Returns True/False.

    CLI Example::

        salt '*' file.exists /dev/xvdj

    """
    return os.path.exists(path)
