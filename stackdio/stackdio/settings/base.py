# Django settings for stackdio project.

import os
from os.path import dirname, normpath, join

from django.core.exceptions import ImproperlyConfigured

import djcelery

djcelery.setup_loader()

def getenv(var):
    try:
        return os.environ[var]
    except KeyError, e:
        msg = 'Missing environment variable {0}.'.format(var)
        raise ImproperlyConfigured(msg)

##
# Required base-level environment variables. The salt and salt-cloud
# environment variables usually don't need to be set for salt and
# salt-cloud to work correctly, however, the stackd.io installation
# must have them set and available for things to function correctly.
##

# This is the salt root
SALT_ROOT = getenv('SALT_ROOT')

# Where salt states live (e.g., /srv/salt)
SALT_STATE_ROOT = getenv('SALT_STATE_ROOT')

# This is the salt-master configuration
SALT_MASTER_CONFIG = getenv('SALT_MASTER_CONFIG')

# This is the salt-cloud configuration file.
SALT_CLOUD_CONFIG = getenv('SALT_CLOUD_CONFIG')

# This is typically in the cloud.profiles.d directory located in 
# salt's configuration root directory. Each *.conf file is an
# individual profile configuration
SALT_CLOUD_PROFILES_DIR = getenv('SALT_CLOUD_PROFILES_DIR')

# This is typically in the cloud.providers.d directory located in 
# salt's configuration root directory. Each *.conf file is an
# individual cloud provider configuration
SALT_CLOUD_PROVIDERS_DIR = getenv('SALT_CLOUD_PROVIDERS_DIR')

##
# stackd.io settings
##
STACKDIO_CONFIG = {
    # Adds additional args to the boostrap-salt script. See:
    # http://bootstrap.saltstack.org
    'SALT_CLOUD_BOOTSTRAP_ARGS': '',
}

##
#
##
DEBUG = True
TEMPLATE_DEBUG = DEBUG

##
# Some convenience variables
##
SITE_ROOT = '/'.join(dirname(__file__).split('/')[0:-2])
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
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    normpath(join(SITE_ROOT, 'stackdio', 'fixtures')),
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
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

## 
# Additional "global" template directories you might like to use.
# App templates should go in that app.
## 
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
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
SECRET_KEY = getenv('DJANGO_SECRET_KEY')

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
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
	    'level': 'DEBUG',
        },
        'core': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'cloud': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'stacks': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

##
# Django REST Framework configuration
##
REST_FRAMEWORK = {
    'PAGINATE_BY': 25,
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
