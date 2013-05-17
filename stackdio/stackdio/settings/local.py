# Grab the base settings
from .base import *

# Override at will!

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

##
#
##
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.mysql',
        'NAME':     'stackdio',
        'HOST':     'localhost',
        'PORT':     '3306',
        'USER':     getenv('MYSQL_USER'),
        'PASSWORD': getenv('MYSQL_PASS'),
    }
}

##
# Celery & RabbitMQ
##
BROKER_URL = 'amqp://guest:guest@localhost:5672/'

##
# Add in additional middleware
##
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)

##
# Add in additional applications
##
INSTALLED_APPS += ('debug_toolbar',)

##
# For debug_toolbar to load
##
INTERNAL_IPS = ('127.0.0.1',)

##
# The local storage directory for storing file data
##
FILE_STORAGE_DIRECTORY = normpath(join(SITE_ROOT, 'storage'))
