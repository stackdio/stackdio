# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import unicode_literals

from collections import OrderedDict

from django.conf.urls import include, url
from django.views.defaults import page_not_found, server_error, bad_request, permission_denied

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.views import APIView


class APIRootView(APIView):
    """
    Root of the stackd.io API. Below are all of the API endpoints that
    are currently accessible. Each API will have its own documentation
    and particular parameters that may discoverable by browsing directly
    to them.
    """

    def get(self, request, format=None):
        api = OrderedDict((
            ('version', reverse('stackdio:version',
                                request=request,
                                format=format)),
            ('events', reverse('stackdio:event-list',
                               request=request,
                               format=format)),
            ('notifications', reverse('stackdio:notifications:root',
                                      request=request,
                                      format=format)),
            ('users', reverse('api:users:user-list',
                              request=request,
                              format=format)),
            ('groups', reverse('api:users:group-list',
                               request=request,
                               format=format)),
            ('current_user', reverse('api:users:currentuser-detail',
                                     request=request,
                                     format=format)),
            ('cloud', reverse('api:cloud:root',
                              request=request,
                              format=format)),
            ('blueprints', reverse('api:blueprints:blueprint-list',
                                   request=request,
                                   format=format)),
            ('formulas', reverse('api:formulas:formula-list',
                                 request=request,
                                 format=format)),
            ('stacks', reverse('api:stacks:stack-list',
                               request=request,
                               format=format)),
            ('volumes', reverse('api:volumes:volume-list',
                                request=request,
                                format=format)),
            ('search', reverse('api:search:search',
                               request=request,
                               format=format)),
        ))

        return Response(api)


@api_view(APIView.http_method_names)
@permission_classes([permissions.AllowAny])
def api_bad_request_view(request, *args, **kwargs):
    return Response({'detail': 'Bad request.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(APIView.http_method_names)
@permission_classes([permissions.AllowAny])
def api_permission_denied_view(request, *args, **kwargs):
    return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)


@api_view(APIView.http_method_names)
@permission_classes([permissions.AllowAny])
def api_not_found_view(request, *args, **kwargs):
    return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(APIView.http_method_names)
@permission_classes([permissions.AllowAny])
def api_server_error_view(request, *args, **kwargs):
    return Response({'detail': 'Internal server error.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)


ERROR_MAP = {
    400: {
        'api': api_bad_request_view,
        'default': bad_request,
    },
    403: {
        'api': api_permission_denied_view,
        'default': permission_denied,
    },
    404: {
        'api': api_not_found_view,
        'default': page_not_found,
    },
    500: {
        'api': api_server_error_view,
        'default': server_error,
    },
}


def get_error_handler(error_code):

    # This is our custom error handler so that 400/403/404/500 requests to /api endpoints
    # return JSON instead of the default page
    def error_handler(request, *args, **kwargs):
        if request.path.startswith('/api'):
            ret = ERROR_MAP[error_code]['api'](request, *args, **kwargs)
            ret.render()
            return ret
        else:
            # Just use the default one
            return ERROR_MAP[error_code]['default'](request, *args, **kwargs)

    return error_handler


urlpatterns = (
    url(r'^$', APIRootView.as_view(), name='root'),

    ##
    # IMPORTS URLS FROM ALL APPS
    ##
    url(r'^cloud/', include('stackdio.api.cloud.urls', namespace='cloud')),
    url(r'^blueprints/', include('stackdio.api.blueprints.urls', namespace='blueprints')),
    url(r'^formulas/', include('stackdio.api.formulas.urls', namespace='formulas')),
    url(r'^stacks/', include('stackdio.api.stacks.urls', namespace='stacks')),
    url(r'^volumes/', include('stackdio.api.volumes.urls', namespace='volumes')),
    url(r'^search/', include('stackdio.api.search.urls', namespace='search')),
    url(r'^', include('stackdio.api.users.urls', namespace='users')),
)

# Format suffixes - this only should go on API endpoints, not everything!
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
