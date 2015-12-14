# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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

from django.conf.urls import include, url
from django.views.defaults import page_not_found

from rest_framework import status
from rest_framework.compat import OrderedDict
from rest_framework.decorators import api_view
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
def api_not_found_view(request, *args, **kwargs):
    return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


# This is our custom 404 handler so that 404 requests to /api endpoints return JSON instead
# of the default 404 page
def api_not_found(request, *args, **kwargs):
    if request.path.startswith('/api'):
        ret = api_not_found_view(request, *args, **kwargs)
        ret.render()
        return ret
    else:
        # Just use the default one
        return page_not_found(request, *args, **kwargs)


urlpatterns = (
    url(r'^$', APIRootView.as_view(), name='root'),

    ##
    # IMPORTS URLS FROM ALL APPS
    ##
    url(r'^', include('stackdio.api.users.urls', namespace='users')),
    url(r'^cloud/', include('stackdio.api.cloud.urls', namespace='cloud')),
    url(r'^blueprints/', include('stackdio.api.blueprints.urls', namespace='blueprints')),
    url(r'^formulas/', include('stackdio.api.formulas.urls', namespace='formulas')),
    url(r'^', include('stackdio.api.stacks.urls', namespace='stacks')),
    url(r'^volumes/', include('stackdio.api.volumes.urls', namespace='volumes')),
    url(r'^search/', include('stackdio.api.search.urls', namespace='search')),
)

# Format suffixes - this only should go on API endpoints, not everything!
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
