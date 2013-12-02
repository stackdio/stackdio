# Grab the base settings
from .base import *

# Override at will!

##
# stackd.io overrides
## 
STACKDIO_CONFIG.update({
    'SALT_CLOUD_BOOTSTRAP_ARGS': '-D git 3cd5efe521e7f5f935957b5056791860910cce89',
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
