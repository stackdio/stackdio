from django.conf.urls.defaults import *
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
        'blueprints': reverse('blueprint-list', request=request, format=format),
        # 'layers': reverse('user-list', request=request, format=format),
        # 'stacks': reverse('user-list', request=request, format=format),
        # 'states': reverse('user-list', request=request, format=format),
    })

urlpatterns = patterns('',

    url(r'^$', api_root),

    ##
    # IMPORTS URLS FROM ALL APPS
    ##
    url(r'^', include('core.urls')),

    url(r'^blueprints/', include('blueprints.urls')),
    url(r'^layers/', include('layers.urls')),
    url(r'^stacks/', include('stacks.urls')),
    url(r'^states/', include('states.urls')),
)