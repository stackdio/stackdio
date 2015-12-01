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
from django.http import Http404

from rest_framework.compat import OrderedDict
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


class APINotFoundView(APIView):

    def get(self, request, *args, **kwargs):
        raise Http404

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def head(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def trace(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


urlpatterns = (
    url(r'^$', APIRootView.as_view(), name='root'),

    ##
    # IMPORTS URLS FROM ALL APPS
    ##
    url(r'^', include('stackdio.api.users.urls', namespace='users')),
    url(r'^cloud/', include('stackdio.api.cloud.urls', namespace='cloud')),
    url(r'^blueprints/', include('stackdio.api.blueprints.urls', namespace='blueprints')),
    url(r'^', include('stackdio.api.formulas.urls', namespace='formulas')),
    url(r'^', include('stackdio.api.stacks.urls', namespace='stacks')),
    url(r'^', include('stackdio.api.volumes.urls', namespace='volumes')),
    url(r'^', include('stackdio.api.search.urls', namespace='search')),
    url(r'^.*$', APINotFoundView.as_view(), name='404'),
)

# Format suffixes - this only should go on API endpoints, not everything!
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
