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

import dj_database_url
from celery.schedules import crontab
from django.contrib.messages import constants as messages

from stackdio.core.config import StackdioConfig, StackdioConfigException

logger = logging.getLogger(__name__)

# Grab a stackdio config object
STACKDIO_CONFIG = StackdioConfig()

# The delimiter used in state execution results
STATE_EXECUTION_DELIMITER = '_|-'

# The fields packed into the state execution result
STATE_EXECUTION_FIELDS = ('module', 'declaration_id', 'name', 'func')

##
# The Django local storage directory for storing its data
##
FILE_STORAGE_DIRECTORY = STACKDIO_CONFIG.storage_dir

LDAP_CONFIG = STACKDIO_CONFIG.get('ldap', {})

LDAP_ENABLED = LDAP_CONFIG.get('enabled', False)

OPBEAT_CONFIG = STACKDIO_CONFIG.get('opbeat', {})

OPBEAT_ENABLED = OPBEAT_CONFIG.get('enabled', False)

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

SECRET_KEY = STACKDIO_CONFIG.django_secret_key

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'actstream',
    'guardian',
    'stackdio.core',
    'stackdio.core.notifications',
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
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'stackdio.core.middleware.LoginRedirectMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# Add the LDAP backend if we're enabled
if LDAP_ENABLED:
    AUTHENTICATION_BACKENDS += ('django_auth_ldap.backend.LDAPBackend',)

# For guardian - we don't need the anonymous user
ANONYMOUS_USER_NAME = None

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.csrf',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.tz',
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
    'default': dj_database_url.parse(STACKDIO_CONFIG.database_url, conn_max_age=600)
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

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
STATIC_ROOT = '%s/static/' % FILE_STORAGE_DIRECTORY

# Additional locations of static files
STATICFILES_DIRS = ()

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = '%s/media/' % FILE_STORAGE_DIRECTORY

# Override message tags for bootstrap
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# Caching - only do 1 minute
CACHE_MIDDLEWARE_SECONDS = 60

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': STACKDIO_CONFIG.redis_url,
    }
}

# Use the cache session engine
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

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
            'class': 'logging.NullHandler',
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
            'filename': os.path.join(STACKDIO_CONFIG.log_dir, 'django.log'),
            'maxBytes': 5242880,
            'backupCount': 5,
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['null'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django_auth_ldap': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'MARKDOWN': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'pip': {
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
        'stackdio.core.permissions': {
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
        'rest_framework.renderers.AdminRenderer',
    ),
}

##
# Available cloud providers - pull from config file
##
CLOUD_PROVIDERS = STACKDIO_CONFIG.cloud_providers

##
# Celery & RabbitMQ
##
BROKER_URL = STACKDIO_CONFIG.celery_broker_url
CELERY_REDIRECT_STDOUTS = False
CELERY_DEFAULT_QUEUE = 'default'

# Serializer settings
# We'll use json since pickle can sometimes be insecure
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Configure queues
CELERY_ROUTES = {
    'formulas.import_formula': {'queue': 'short'},
    'formulas.update_formula': {'queue': 'short'},
    'notifications.generate_notifications': {'queue': 'short'},
    'notifications.resend_failed_notifications': {'queue': 'short'},
    'notifications.send_notification': {'queue': 'short'},
    'notifications.send_bulk_notifications': {'queue': 'short'},
    'stacks.cure_zombies': {'queue': 'stacks'},
    'stacks.destroy_hosts': {'queue': 'stacks'},
    'stacks.destroy_stack': {'queue': 'stacks'},
    'stacks.execute_action': {'queue': 'short'},
    'stacks.finish_stack': {'queue': 'stacks'},
    'stacks.global_orchestrate': {'queue': 'stacks'},
    'stacks.highstate': {'queue': 'stacks'},
    'stacks.launch_hosts': {'queue': 'stacks'},
    'stacks.orchestrate': {'queue': 'stacks'},
    'stacks.ping': {'queue': 'stacks'},
    'stacks.propagate_ssh': {'queue': 'stacks'},
    'stacks.register_dns': {'queue': 'stacks'},
    'stacks.register_volume_delete': {'queue': 'stacks'},
    'stacks.run_command': {'queue': 'short'},
    'stacks.sync_all': {'queue': 'stacks'},
    'stacks.tag_infrastructure': {'queue': 'stacks'},
    'stacks.unregister_dns': {'queue': 'stacks'},
    'stacks.update_host_info': {'queue': 'short'},
    'stacks.update_metadata': {'queue': 'stacks'},
}

CELERYBEAT_SCHEDULE = {
    'update-host-info': {
        'task': 'stacks.update_host_info',
        'schedule': crontab(minute='*/5'),  # Execute every 5 minutes
        'args': (),
    },
    'resend-failed-notifications': {
        'task': 'notifications.resend_failed_notifications',
        'schedule': crontab(minute='*/10'),  # Execute every 10 minutes
        'args': (),
    }
}


# opbeat things
if OPBEAT_ENABLED:
    INSTALLED_APPS += ('opbeat.contrib.django',)

    MIDDLEWARE_CLASSES = (
        'opbeat.contrib.django.middleware.OpbeatAPMMiddleware',
    ) + MIDDLEWARE_CLASSES

    OPBEAT = {
        'ORGANIZATION_ID': OPBEAT_CONFIG.get('organization_id'),
        'APP_ID': OPBEAT_CONFIG.get('app_id'),
        'SECRET_TOKEN': OPBEAT_CONFIG.get('secret_token'),
    }

    # Set up the logging
    LOGGING['handlers']['opbeat'] = {
        'level': 'WARNING',
        'class': 'opbeat.contrib.django.handlers.OpbeatHandler',
    }

    LOGGING['loggers']['opbeat.errors'] = {
        'level': 'ERROR',
        'handlers': ['console'],
        'propagate': False,
    }

    LOGGING['loggers']['opbeat.instrumentation.packages.base'] = {
        'level': 'WARNING',
        'handlers': ['console'],
        'propagate': False,
    }

##
# LDAP configuration. To enable this, you should set ldap: enabled: true in your config file.
##

# Throw in the rest of our LDAP config if ldap is enabled
if LDAP_ENABLED:
    try:
        import ldap
        import django_auth_ldap.config
        from django_auth_ldap.config import LDAPSearch
    except ImportError:
        raise StackdioConfigException('LDAP is enabled, but django_auth_ldap is missing.  '
                                      'Please install django_auth_ldap.')

    auth_ldap_search = ('group_type',)
    call_value = ('group_type',)

    def get_from_ldap_module(attr, module=ldap, fail_on_error=False):
        try:
            return getattr(module, attr)
        except (AttributeError, TypeError):
            if fail_on_error:
                raise StackdioConfigException('Invalid config value: {}'.format(attr))
            else:
                # if we get an exception, just return the raw attribute
                return attr

    def get_search_object(user_or_group):
        search_base = LDAP_CONFIG.get('{}_search_base'.format(user_or_group))
        if not search_base:
            raise StackdioConfigException('Missing ldap.{}_search_base '
                                          'config parameter'.format(user_or_group))

        search_scope_str = LDAP_CONFIG.get('{}_search_scope'.format(user_or_group), 'SCOPE_SUBTREE')
        search_scope = get_from_ldap_module(search_scope_str, fail_on_error=True)
        search_filter = LDAP_CONFIG.get('{}_search_filter'.format(user_or_group))

        if search_filter is None:
            return LDAPSearch(search_base, search_scope)
        else:
            return LDAPSearch(search_base, search_scope, search_filter)

    # Set the search objects
    AUTH_LDAP_USER_SEARCH = get_search_object('user')
    AUTH_LDAP_GROUP_SEARCH = get_search_object('group')

    for key, value in LDAP_CONFIG.items():
        if key == 'enabled':
            continue

        settings_key = 'AUTH_LDAP_{}'.format(key.upper())

        if key in auth_ldap_search:
            search_module = django_auth_ldap.config
        else:
            search_module = ldap

        if isinstance(value, dict):
            settings_value = {}
            for k, v in value.items():
                sub_key = get_from_ldap_module(k, search_module)
                sub_value = get_from_ldap_module(v, search_module)
                settings_value[sub_key] = sub_value
        else:
            settings_value = get_from_ldap_module(value, search_module)

        if key in call_value:
            settings_value = settings_value()

        # Set the attribute on this settings module
        vars()[settings_key] = settings_value
