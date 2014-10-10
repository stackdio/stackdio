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


# Django settings for stackdio project.

import os

import djcelery
import dj_database_url

from core.config import StackdioConfig


djcelery.setup_loader()

STACKDIO_CONFIG = StackdioConfig()

# The delimiter used in state execution results
STATE_EXECUTION_DELIMITER = '_|-'

# The fields packed into the state execution result
STATE_EXECUTION_FIELDS = ('module', 'declaration_id', 'name', 'func')

##
# The Django local storage directory for storing its data
##
FILE_STORAGE_DIRECTORY = os.path.join(STACKDIO_CONFIG['storage_root'],
                                      'storage')

LOG_DIRECTORY = os.path.join(STACKDIO_CONFIG['storage_root'],
                             'var',
                             'log',
                             'stackdio')
if not os.path.isdir(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)

##
#
##
DEBUG = True
TEMPLATE_DEBUG = DEBUG

##
# Database configuration. We're using dj-database-url to simplify
# the required settings and instead of pulling the DSN from an
# environment variable, we're loading it from the stackdio config
##
DATABASES = {
    'default': dj_database_url.parse(STACKDIO_CONFIG['db_dsn'])
}

##
# Some convenience variables
##
SITE_ROOT = '/'.join(os.path.dirname(__file__).split('/')[0:-2])
PROJECT_ROOT = SITE_ROOT + '/stackdio'

##
# Define your admin tuples like ('full name', 'email@address.com')
##
ADMINS = (
    ('Abe Music', 'abe.music@digitalreasoning.com'),
    ('Charlie Penner', 'charlie.penner@digitalreasoning.com'),
    ('Steve Brownlee', 'steve.brownlee@digitalreasoning.com'),
)
MANAGERS = ADMINS

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = '%s/static/media/' % SITE_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '%s/static/' % SITE_ROOT

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = ()

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS  #NOQA
FIXTURE_DIRS = (
    os.path.normpath(os.path.join(SITE_ROOT, 'stackdio', 'fixtures')),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'rest_framework',
    'rest_framework.authtoken',
    #'rest_framework_swagger',
    'django_nose',
    'south',
    'djcelery',
    'core',
    'cloud',
    'stacks',
    'volumes',
    'blueprints',
    'formulas',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

##
# Additional "global" template directories you might like to use.
# App templates should go in that app.
##
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates". Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '%s/templates' % PROJECT_ROOT,
)

##
# THE REST OF THIS JUNK IS PROVIDED BY DJANGO. IT COULD BE CHANGED
# IF YOU FEEL THE NEED, BUT YOU SHOULD PROBABLY LEAVE IT ALONE
# UNLESS YOU HAVE A BURNING DESIRE OR YOU KNOW WHAT YOU'RE DOING
##

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Make this unique, and don't share it with anybody.
# e.g, '!&-bq%17z_osv3a)ziny$k7auc8rwv@^r*alo*e@wt#z^g(x6v'
SECRET_KEY = STACKDIO_CONFIG['django_secret_key']

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

ROOT_URLCONF = 'stackdio.urls'


# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'stackdio.wsgi.application'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'default': {
            'format': '[%(levelname)s] %(asctime)s %(name)s: %(message)s',
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
        },
        "file": {
            "level": "DEBUG",
            "formatter": "default",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIRECTORY, 'django.log'),
            "maxBytes": 5242880,
            "backupCount": 5
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django_auth_ldap': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'boto': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'south': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'amqp': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

##
# Django REST Framework configuration
##
REST_FRAMEWORK = {
    'PAGINATE_BY': 50,
    'PAGINATE_BY_PARAM': 'page_size',
    'FILTER_BACKEND': 'rest_framework.filters.DjangoFilterBackend',

    'DEFAULT_AUTHENTICATION_CLASSES': (
        #'api.authentication.APIKeyAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),

}

##
# Swagger configuration
##
SWAGGER_SETTINGS = {
    'exclude_namespaces': ['django'],
    'api_version': '1.0 alpha',
    'is_authenticated': True,
    'is_superuser': False
}

##
# Available cloud providers
##
CLOUD_PROVIDERS = [
    'cloud.providers.aws.AWSCloudProvider',
    # 'cloud.providers.rackspace.RackspaceCloudProvider',
]

##
# Celery & RabbitMQ
##
BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_REDIRECT_STDOUTS = False
CELERY_DEFAULT_QUEUE = 'default'
CELERY_ROUTES = {
    'formulas.import_formula': {'queue': 'formulas'},
    'formulas.update_formula': {'queue': 'formulas'},
    'stacks.cure_zombies': {'queue': 'stacks'},
    'stacks.custom_action': {'queue': 'stacks'},
    'stacks.destroy_hosts': {'queue': 'stacks'},
    'stacks.destroy_stack': {'queue': 'stacks'},
    'stacks.execute_action': {'queue': 'stacks'},
    'stacks.finish_stack': {'queue': 'stacks'},
    'stacks.handle_error': {'queue': 'stacks'},
    'stacks.highstate': {'queue': 'stacks'},
    'stacks.launch_hosts': {'queue': 'stacks'},
    'stacks.orchestrate': {'queue': 'stacks'},
    'stacks.ping': {'queue': 'stacks'},
    'stacks.register_dns': {'queue': 'stacks'},
    'stacks.register_volume_delete': {'queue': 'stacks'},
    'stacks.sync_all': {'queue': 'stacks'},
    'stacks.tag_infrastructure': {'queue': 'stacks'},
    'stacks.unregister_dns': {'queue': 'stacks'},
    'stacks.update_metadata': {'queue': 'stacks'},
}

##
# LDAP configuration. To enable this, you should copy ldap_settings.py.template
# to ldap_settings.py and modify the settings there.
##
if os.path.isfile(os.path.join(PROJECT_ROOT, 'settings', 'ldap_settings.py')):
    from ldap_settings import *  # NOQA
