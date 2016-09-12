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


import logging
import re
import importlib

from django.conf import settings
from stackdio.core.config import StackdioConfigException

logger = logging.getLogger(__name__)


def get_provider_driver_class(provider):
    provider_classes = get_cloud_providers()
    for provider_class in provider_classes:
        if provider_class.SHORT_NAME == provider.name:
            return provider_class

    return None


def check_cloud_provider_settings():
    if not hasattr(settings, 'CLOUD_PROVIDERS'):
        raise StackdioConfigException(
            'settings.CLOUD_PROVIDERS must set with a list of supported cloud providers.'
        )


def get_cloud_provider_choices():
    check_cloud_provider_settings()

    choices = []
    for provider in get_cloud_providers():
        choices.append(provider.get_provider_choice())

    return choices


def get_cloud_providers():
    check_cloud_provider_settings()

    providers = []
    for class_path in settings.CLOUD_PROVIDERS:
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            providers.append(getattr(module, class_name))
        except ImportError as e:
            msg = 'Could not import {0} from settings.CLOUD_PROVIDERS'.format(class_path)
            logger.error(e)
            raise StackdioConfigException(msg)

    return providers


def find_roles(filename, pattern):
    with open(filename) as f:
        recording = False
        for line in f:
            # if line.startswith(pattern):
            # re.match('^(\s)+-\s(?!match\:)', line)
            if re.match(pattern, line):
                yield line
                recording = not recording
            elif recording:
                yield line
