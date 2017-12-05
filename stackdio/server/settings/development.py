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

# pylint: disable=wildcard-import, unused-wildcard-import

from __future__ import unicode_literals

# Grab the base settings
from stackdio.server.settings.testing import *

DEBUG = True
JAVASCRIPT_DEBUG = True

# Set the log level to DEBUG - it's WARNING by default
LOGGING['loggers']['']['level'] = 'DEBUG'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

DATABASES['default']['CONN_MAX_AGE'] = 0

# Add in the secure proxy header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'ssl')

##
# Add in additional applications
##
# INSTALLED_APPS += ('',)
