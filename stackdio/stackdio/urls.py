from django.conf.urls import patterns, include, url

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

# Enable admin interface
from django.contrib import admin
admin.autodiscover()

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
    })


urlpatterns = patterns('',

    # Admin interface
    url(r'^__private/admin/', include(admin.site.urls)),

    # API root endpoint and additional app endpoints. Pretty much
    # each application will need to pull in their urls.py here
    # if they want to be added to be discoverable
    (r'^api/$', api_root),
    (r'^api/', include('core.urls')),

)
