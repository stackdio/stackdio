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
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '%s/dev.db' % SITE_ROOT,
    }
}

# Local settings overrides...should not be committed.
try:
    from .local_settings import *
except:
    pass
