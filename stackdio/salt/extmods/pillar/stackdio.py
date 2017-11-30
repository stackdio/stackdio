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
Loads a stack-specific pillar file. stack_pillar_file must be set in the grains
or this module will not be available to pillar.
"""

from __future__ import absolute_import

import logging
import os

import yaml
from stackdio.core.utils import recursive_update

# Set up logging
logger = logging.getLogger(__name__)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stackdio.server.settings.production')


def django_setup():
    """
    Our version of django.setup() that doesn't configure logging
    """
    from django.apps import apps
    from django.conf import settings

    apps.populate(settings.INSTALLED_APPS)


# setup django (without logging)
django_setup()

# These must be imported AFTER django is set up
from stackdio.api.cloud.models import CloudAccount  # NOQA
from stackdio.api.stacks.models import Stack  # NOQA
from stackdio.api.environments.models import Environment  # NOQA


def __virtual__():
    return True


def ext_pillar(minion_id, pillar, *args, **kwargs):
    """
    Basically, we need to provide additional pillar data to our states
    but only the pillar data defined for a stack. The user should have
    the ability to do this from the UI and the pillar file used will
    be located in the grains.
    """

    new_pillar = {}

    # First try the environment
    # (always do this regardless of whether there's we're in global orchestration or not)
    if 'env' in __grains__:
        _, _, env_name = __grains__['env'].partition('.')
        try:
            environment = Environment.objects.get(name=env_name)
            recursive_update(new_pillar, environment.get_full_pillar())
        except Environment.DoesNotExist:
            logger.info('Environment {} was specified in the grains '
                        'but was not found.'.format(env_name))

    global_orch = __grains__.get('global_orchestration', False)

    # Then the cloud account (but only if we ARE in global orchestration)
    if global_orch and 'cloud_account' in __grains__:
        try:
            account = CloudAccount.objects.get(slug=__grains__['cloud_account'])
            recursive_update(new_pillar, account.get_full_pillar())
        except CloudAccount.DoesNotExist:
            logger.info('Cloud account {} not found'.format(__grains__['cloud_account']))

    # Then the stack (but only if we ARE NOT in global orchestration)
    if not global_orch and 'stack_id' in __grains__ and isinstance(__grains__['stack_id'], int):
        try:
            stack = Stack.objects.get(id=__grains__['stack_id'])
            recursive_update(new_pillar, stack.get_full_pillar())
        except Stack.DoesNotExist:
            logger.info('Stack {} not found'.format(__grains__['stack_id']))

    # This is the old way, try it too for compatibility purposes.
    # Make it last so it has the highest precedence.
    if 'stack_pillar_file' in __grains__:
        # load the stack_pillar_file, rendered as yaml, and add it into the return dict
        try:
            with open(__grains__['stack_pillar_file'], 'r') as f:
                loaded_pillar = yaml.safe_load(f)
                recursive_update(new_pillar, loaded_pillar)
        except Exception as e:
            logger.exception(e)
            logger.critical('Unable to load/render stack_pillar_file. Is the YAML '
                            'properly formatted?')

    return new_pillar
