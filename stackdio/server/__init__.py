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

from __future__ import absolute_import
import sys

from .version import __version__

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
try:
    from stackdio.server.celery import app as celery_app
except ImportError:
    sys.stderr.write("Not importing celery... "
                     "Ignore if this if you're currently running setup.py.\n")

__copyright__ = "Copyright 2016,  Digital Reasoning"
__license__ = "Apache License Version 2.0, January 2004"
__maintainer__ = "https://github.com/stackdio/stackdio"
