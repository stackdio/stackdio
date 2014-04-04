# Grab the base settings
from .base import *  # NOQA

DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ['*']
WSGI_APPLICATION = 'stackdio.stackdio.wsgi.application'

try:
    from stackdio import urls
    ROOT_URLCONF = 'stackdio.urls'
except ImportError:
    from stackdio.stackdio import urls
    ROOT_URLCONF = 'stackdio.stackdio.urls'
