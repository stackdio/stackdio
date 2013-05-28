import logging
import yaml

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import importlib

from .models import CloudProvider

logger = logging.getLogger(__name__)

def get_cloud_providers():
    
    if not hasattr(settings, 'CLOUD_PROVIDERS'):
        raise ImproperlyConfigured('settings.CLOUD_PROVIDERS must set with a list of supported cloud providers.')

    providers = []
    try:
        for class_path in settings.CLOUD_PROVIDERS:
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            providers.append(getattr(module, class_name))

    except ImportError as e:
        msg = 'Could not import {0} from settings.CLOUD_PROVIDERS'.format(class_path)
        raise ImportError(msg)

    logger.debug('get_cloud_providers: {0!r}'.format(providers))
    return providers

def write_cloud_providers_file():

    with open(settings.SALT_CLOUD_PROVIDERS_CONFIG, 'w') as f:
        # get all the providers yaml information
        for provider in CloudProvider.objects.all():
            f.write(provider.yaml)
