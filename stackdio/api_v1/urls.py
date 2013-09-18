from django.conf.urls import patterns, include, url

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

@api_view(['GET'])
def api_root(request, format=None):
    '''
    Root of the stackd.io API. Below are all of the API endpoints that
    are currently accessible. Each API will have its own documentation
    and particular parameters that may discoverable by browsing directly
    to them.

    '''
    api = { 
        'core': {
            'settings': reverse('usersettings-detail', request=request, format=format),
            'change_password': reverse('change_password', request=request, format=format),
        },
        'cloud': {
            'instance_sizes': reverse('cloudinstancesize-list', request=request, format=format),
            'zones': reverse('cloudzone-list', request=request, format=format),
            'profiles': reverse('cloudprofile-list', request=request, format=format),
            'providers': reverse('cloudprovider-list', request=request, format=format),
            'provider_types': reverse('cloudprovidertype-list', request=request, format=format),
            'security_groups': reverse('securitygroup-list', request=request, format=format),
        },
        'stacks': {
            'hosts': reverse('host-list', request=request, format=format),
            'roles': reverse('saltrole-list', request=request, format=format),
            'snapshots': reverse('snapshot-list', request=request, format=format),
            'stacks': reverse('stack-list', request=request, format=format),
            'volumes': reverse('volume-list', request=request, format=format),
        },
    }

    if request.user.is_superuser:
        api['core'] = {
            'users': reverse('user-list', request=request, format=format),
        }

    return Response(api)

urlpatterns = patterns('',

    url(r'^$', api_root),

    ##
    # IMPORTS URLS FROM ALL APPS
    ##
    url(r'^', include('core.urls')),
    url(r'^', include('cloud.urls')),
    url(r'^', include('stacks.urls')),
    url(r'^', include('volumes.urls')),
)
