# Grab the base settings
from .base import *  # NOQA

DEBUG = False
TEMPLATE_DEBUG = False
WSGI_APPLICATION = 'stackdio.stackdio.wsgi.application'
ROOT_URLCONF = 'stackdio.stackdio.urls'
