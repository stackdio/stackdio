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

VERSION = (0, 7, 0, 'dev', 0)


def get_version(version=None):
    """
    Returns a PEP 440-compliant version number from VERSION.

    Created by modifying django.utils.version.get_version
    """

    # Now build the two parts of the version number:
    # major = X.Y[.Z]
    # sub = .devN - for development releases
    #     | {a|b|rc}N - for alpha, beta and rc releases
    #     | .postN - for post-release releases

    major = get_major_version(version)

    if len(VERSION) <= 3:
        return major

    if version[3] in ('dev', 'post'):
        sub = '.%s%i' % version[3:5]
    elif version[3] in ('a', 'b', 'rc'):
        sub = '%s%i' % version[3:5]
    else:
        raise ValueError('Invalid VERSION: %s' % str(VERSION))

    return str(major + sub)


def get_major_version(version):
    """
    Returns major version from VERSION.
    """
    major = '.'.join(str(x) for x in version[:3])
    return major


__version__ = get_version(VERSION)
