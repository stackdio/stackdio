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

import imp

import stackdio

# Grab the base settings
from .base import *  # NOQA


WSGI_APPLICATION = 'stackdio.server.stackdio.wsgi.application'

try:
    # If stackdio.urls exists, just set the URLCONF directly
    imp.find_module('urls', stackdio.__path__)
    ROOT_URLCONF = 'stackdio.urls'
except ImportError:
    # It doesn't exist, so the URLCONF needs to be the full path
    ROOT_URLCONF = 'stackdio.server.stackdio.urls'
