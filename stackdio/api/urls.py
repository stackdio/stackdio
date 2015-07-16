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


from django.conf.urls import patterns, include, url

from rest_framework.compat import OrderedDict
from rest_framework.permissions import IsAuthenticated
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
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        api = OrderedDict((
            ('version', reverse('version',
                                request=request,
                                format=format)),
            ('users', reverse('user-list',
                              request=request,
                              format=format)),
            ('groups', reverse('group-list',
                               request=request,
                               format=format)),
            ('current_user', reverse('currentuser-detail',
                                     request=request,
                                     format=format)),
            ('cloud', reverse('cloud-root',
                              request=request,
                              format=format)),
            ('blueprints', reverse('blueprint-list',
                                   request=request,
                                   format=format)),
            ('formulas', reverse('formula-list',
                                 request=request,
                                 format=format)),
            ('stacks', reverse('stack-list',
                               request=request,
                               format=format)),
            ('volumes', reverse('volume-list',
                                request=request,
                                format=format)),
            ('search', reverse('search',
                               request=request,
                               format=format)),
        ))

        return Response(api)


urlpatterns = patterns(
    '',

    url(r'^$', APIRootView.as_view(), name='api-root'),

    ##
    # IMPORTS URLS FROM ALL APPS
    ##
    url(r'^', include('stackdio.api.users.urls')),
    url(r'^', include('stackdio.core.urls')),
    url(r'^cloud/', include('stackdio.api.cloud.urls')),
    url(r'^', include('stackdio.api.stacks.urls')),
    url(r'^', include('stackdio.api.volumes.urls')),
    url(r'^', include('stackdio.api.blueprints.urls')),
    url(r'^', include('stackdio.api.formulas.urls')),
    url(r'^', include('stackdio.api.search.urls')),
)

# Format suffixes - this only should go on API endpoints, not everything!
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
