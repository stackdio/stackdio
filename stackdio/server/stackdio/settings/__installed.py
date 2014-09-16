# Grab the base settings
from .base import *  # NOQA

DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ['*']
WSGI_APPLICATION = 'stackdio.server.stackdio.wsgi.application'

try:
    from stackdio import urls
    ROOT_URLCONF = 'stackdio.urls'
except ImportError:
    from stackdio.server.stackdio import urls
    ROOT_URLCONF = 'stackdio.server.stackdio.urls'
