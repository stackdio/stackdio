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

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stackdio.server.settings.production')

# pylint: disable=wrong-import-position

from django.conf import settings  # nopep8

app = Celery('stackdio')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


# Add opbeat for celery if it's enabled
if settings.OPBEAT_ENABLED:
    from opbeat.contrib.django.models import client, logger, register_handlers
    from opbeat.contrib.celery import register_signal

    try:
        register_signal(client)
    except Exception as e:
        logger.exception('Failed installing celery hook: %s', e)

    if 'opbeat.contrib.django' in settings.INSTALLED_APPS:
        register_handlers()
