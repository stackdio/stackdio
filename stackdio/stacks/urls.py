from django.conf.urls.defaults import patterns, url

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
        'stacks': {
            
        },
    })

urlpatterns = patterns('stacks.api',
    url(r'^$', api_root),

)


