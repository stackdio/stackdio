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

"""
Django settings for stackdio project.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import logging
import os

from django.contrib.messages import constants as messages
import dj_database_url

from stackdio.core.config import StackdioConfig


logger = logging.getLogger(__name__)

STACKDIO_CONFIG = StackdioConfig()

# The delimiter used in state execution results
STATE_EXECUTION_DELIMITER = '_|-'

# The fields packed into the state execution result
STATE_EXECUTION_FIELDS = ('module', 'declaration_id', 'name', 'func')

##
# The Django local storage directory for storing its data
##
FILE_STORAGE_DIRECTORY = os.path.join(
    STACKDIO_CONFIG['storage_root'],
    'storage'
)

LOG_DIRECTORY = os.path.join(
    STACKDIO_CONFIG['storage_root'],
    'var',
    'log',
    'stackdio'
)

if not os.path.isdir(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)

##
# Some convenience variables
##
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))

# Set DEBUG things to False here, override to True in the development.py settings
DEBUG = False
JAVASCRIPT_DEBUG = False

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.8/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']


SECRET_KEY = STACKDIO_CONFIG['django_secret_key']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'guardian',
    'stackdio.core',
    'stackdio.api.users',
    'stackdio.api.cloud',
    'stackdio.api.stacks',
    'stackdio.api.volumes',
    'stackdio.api.blueprints',
    'stackdio.api.formulas',
    'stackdio.ui',
    'rest_framework',
    'rest_framework.authtoken',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# For guardian
ANONYMOUS_USER_ID = -1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.csrf',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'stackdio.server.wsgi.application'

ROOT_URLCONF = 'stackdio.server.urls'


##
# Define your admin tuples like ('full name', 'email@address.com')
##
ADMINS = ()
MANAGERS = ADMINS

##
# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
#
# We're using dj-database-url to simplify
# the required settings and instead of pulling the DSN from an
# environment variable, we're loading it from the stackdio config
##
DATABASES = {
    'default': dj_database_url.parse(STACKDIO_CONFIG['db_dsn'])
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Chicago'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Login settings
LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/'

LOGOUT_URL = '/logout/'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = '/static/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '%s/static/' % STACKDIO_CONFIG.storage_root

# Additional locations of static files
STATICFILES_DIRS = ()

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = '%s/media/' % STACKDIO_CONFIG.storage_root

# Override message tags for bootstrap
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# Caching - only do 1 minute
CACHE_MIDDLEWARE_SECONDS = 60

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
        'file': {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIRECTORY, 'django.log'),
            'maxBytes': 5242880,
            'backupCount': 5,
        },
    },
    'loggers': {
        'django.db.backends': {
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
        'amqp': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    }
}

##
# Django REST Framework configuration
##
REST_FRAMEWORK = {
    'PAGE_SIZE': 50,

    # Filtering
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
    ),

    # Authentication
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),

    # All endpoints require authentication
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    # Parsers - enable FormParser to get nice forms in the browsable API
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
    ),

    # Enable the browsable API - comment out the BrowsableAPIRenderer line to only return json
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
}

##
# Available cloud providers
##
CLOUD_PROVIDERS = (
    'stackdio.api.cloud.providers.aws.AWSCloudProvider',
    # 'stackdio.api.cloud.providers.rackspace.RackspaceCloudProvider',
)

##
# Celery & RabbitMQ
##
BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_REDIRECT_STDOUTS = False
CELERY_DEFAULT_QUEUE = 'default'

# Serializer settings
# We'll use json since pickle can sometimes be insecure
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Configure queues
CELERY_ROUTES = {
    'formulas.import_formula': {'queue': 'formulas'},
    'formulas.update_formula': {'queue': 'formulas'},
    'stacks.cure_zombies': {'queue': 'stacks'},
    'stacks.destroy_hosts': {'queue': 'stacks'},
    'stacks.destroy_stack': {'queue': 'stacks'},
    'stacks.execute_action': {'queue': 'stacks'},
    'stacks.finish_stack': {'queue': 'stacks'},
    'stacks.global_orchestrate': {'queue': 'stacks'},
    'stacks.handle_error': {'queue': 'stacks'},
    'stacks.highstate': {'queue': 'stacks'},
    'stacks.launch_hosts': {'queue': 'stacks'},
    'stacks.orchestrate': {'queue': 'stacks'},
    'stacks.ping': {'queue': 'stacks'},
    'stacks.propagate_ssh': {'queue': 'stacks'},
    'stacks.register_dns': {'queue': 'stacks'},
    'stacks.register_volume_delete': {'queue': 'stacks'},
    'stacks.run_command': {'queue': 'stacks'},
    'stacks.sync_all': {'queue': 'stacks'},
    'stacks.tag_infrastructure': {'queue': 'stacks'},
    'stacks.unregister_dns': {'queue': 'stacks'},
    'stacks.update_metadata': {'queue': 'stacks'},
}

##
# LDAP configuration. To enable this, you should copy ldap_settings.py.template
# to ldap_settings.py and modify the settings there.
##
try:
    # pylint: disable=wildcard-import, unused-wildcard-import, no-name-in-module, import-error
    from stackdio.server.settings.ldap_settings import *
    LDAP_ENABLED = True
    AUTHENTICATION_BACKENDS += ('django_auth_ldap.backend.LDAPBackend',)
except ImportError:
    LDAP_ENABLED = False
