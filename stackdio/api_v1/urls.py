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
    return Response({
        'core': {
            'users': reverse('user-list', request=request, format=format),
        },
        'cloud': {
            'providers': reverse('cloudprovider-list', request=request, format=format),
            'provider_types': reverse('cloudprovidertype-list', request=request, format=format),
            'instance_sizes': reverse('cloudinstancesize-list', request=request, format=format),
            'profiles': reverse('cloudprofile-list', request=request, format=format),
        },
        'hosts': reverse('host-list', request=request, format=format),
        'stacks': reverse('stack-list', request=request, format=format),
        # 'blueprints': reverse('blueprint-list', request=request, format=format),
        # 'layers': reverse('layer-list', request=request, format=format),
        # 'states': reverse('state-list', request=request, format=format),
    })

urlpatterns = patterns('',

    url(r'^$', api_root),

    ##
    # IMPORTS URLS FROM ALL APPS
    ##
    url(r'^', include('core.urls')),
    url(r'^', include('cloud.urls')),
    url(r'^', include('stacks.urls')),

    # url(r'^blueprints/', include('blueprints.urls')),
    # url(r'^layers/', include('layers.urls')),
    # url(r'^states/', include('states.urls')),
)
