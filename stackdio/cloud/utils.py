import logging
import yaml
import os
import re
from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import importlib

from core import exceptions as core_exceptions

import models

logger = logging.getLogger(__name__)

STACKDIO_CONFIG = settings.STACKDIO_CONFIG

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

def write_cloud_providers_file():

    with open(settings.SALT_CLOUD_PROVIDERS_CONFIG, 'w') as f:
        # get all the providers yaml information
        for provider in models.CloudProvider.objects.all():
            f.write(provider.yaml)

def write_cloud_profiles_file():

    profile_yaml = {}

    # Get all the profiles and add the relevant data to the dict
    # that we'll use to generate the yaml data from
    for profile in models.CloudProfile.objects.all():

        profile_yaml[profile.slug] = {
            'provider': profile.cloud_provider.slug,
            'image': profile.image_id,
            'size': profile.default_instance_size.title,
            'ssh_username': profile.ssh_user,
            'script': 'bootstrap-salt',
            'script_args': STACKDIO_CONFIG['SALT_CLOUD_BOOTSTRAP_ARGS'],
        }

    with open(settings.SALT_CLOUDVM_CONFIG, 'w') as f:
        f.write(yaml.safe_dump(profile_yaml,
                               default_flow_style=False))


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
