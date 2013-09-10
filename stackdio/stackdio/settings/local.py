# Grab the base settings
from .base import *

# Override at will!

##
# stackd.io overrides
## 
STACKDIO_CONFIG.update({
    # Don't pull the develop branch until salt-cloud/#700 is fixed. Stick
    # with the stabile build.
    'SALT_CLOUD_BOOTSTRAP_ARGS': '-D git 8f588a088108bfa345136032d264b6bfa90f94ba',
})

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
#MIDDLEWARE_CLASSES += ('',)

##
# Add in additional applications
##
#INSTALLED_APPS += ('',)

##
# The local storage directory for storing file data
##
FILE_STORAGE_DIRECTORY = normpath(join(SITE_ROOT, 'storage'))

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'corsheaders.middleware.CorsMiddleware',
)

CORS_ORIGIN_WHITELIST = (
   'localhost:3000',
)
