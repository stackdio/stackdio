import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

logger = logging.getLogger(__name__)

def get_cloud_providers():
    
    if not hasattr(settings, 'CLOUD_PROVIDERS'):
        raise ImproperlyConfigured('settings.CLOUD_PROVIDERS must set with a list of supported cloud providers.')

    providers = []
    for class_path in settings.CLOUD_PROVIDERS:
        module_path, class_name = class_path.rsplit('.', 1)
        providers.append(getattr(import_module(module_path), class_name))

    logger.debug('get_cloud_providers: {0!r}'.format(providers))
    return providers
