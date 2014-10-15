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


import logging
import yaml
import os
import re
import boto.ec2
from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import importlib

from core import exceptions as core_exceptions

import models

logger = logging.getLogger(__name__)

def get_provider_type_and_class(provider_type_id):

    try:
        provider_type = models.CloudProviderType.objects.get(id=provider_type_id)
    except models.CloudProviderType.DoesNotExist:
        raise core_exceptions.BadRequest('Provider types does not exist.')

    provider_classes = get_cloud_providers()
    for provider_class in provider_classes:
        if provider_class.SHORT_NAME == provider_type.type_name:
            return provider_type, provider_class

    return None, None

def check_cloud_provider_settings():

    if not hasattr(settings, 'CLOUD_PROVIDERS'):
        raise ImproperlyConfigured('settings.CLOUD_PROVIDERS must set with a list of supported cloud providers.')

def get_cloud_provider_choices():

    check_cloud_provider_settings()

    choices = []
    for provider in get_cloud_providers():
        choices.append(provider.get_provider_choice())

    return choices

def get_cloud_providers():

    check_cloud_provider_settings()
    
    providers = []
    try:
        for class_path in settings.CLOUD_PROVIDERS:
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            providers.append(getattr(module, class_name))

    except ImportError as e:
        # msg = 'Could not import {0} from settings.CLOUD_PROVIDERS'.format(class_path)
        # logger.error(e)
        # raise ImportError(msg)
        raise

    return providers

def findRoles(filename, pattern):
    with open(filename) as file:
        recording = False
        for line in file:
            # if line.startswith(pattern):
            # re.match('^(\s)+-\s(?!match\:)', line)
            if re.match(pattern, line):
                yield line
                recording = not recording
            elif recording:
                yield line
