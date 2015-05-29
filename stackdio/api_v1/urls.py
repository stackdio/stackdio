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
            ('core', {
                'settings': reverse('usersettings-detail',
                                    request=request,
                                    format=format),
                'change_password': reverse('change_password',
                                           request=request,
                                           format=format),
                'version': reverse('version',
                                   request=request,
                                   format=format),
            }),
            ('cloud', OrderedDict((
                ('provider_types', reverse('cloudprovidertype-list',
                                           request=request,
                                           format=format)),
                ('providers', reverse('cloudprovider-list',
                                      request=request,
                                      format=format)),
                ('profiles', reverse('cloudprofile-list',
                                     request=request,
                                     format=format)),
                ('instance_sizes', reverse('cloudinstancesize-list',
                                           request=request,
                                           format=format)),
                ('regions', reverse('cloudregion-list',
                                    request=request,
                                    format=format)),
                ('zones', reverse('cloudzone-list',
                                  request=request,
                                  format=format)),
                ('snapshots', reverse('snapshot-list',
                                      request=request,
                                      format=format)),
                ('security_groups', reverse('securitygroup-list',
                                            request=request,
                                            format=format)),
            ))),
            ('blueprints', reverse('blueprint-list',
                                   request=request,
                                   format=format)),
            ('formulas', reverse('formula-list',
                                 request=request,
                                 format=format)),
            ('stacks', reverse('stack-list',
                               request=request,
                               format=format)),
            ('hosts', reverse('host-list',
                              request=request,
                              format=format)),
            ('snapshots', reverse('snapshot-list',
                                  request=request,
                                  format=format)),
            ('volumes', reverse('volume-list',
                                request=request,
                                format=format)),
            ('search', reverse('search',
                               request=request,
                               format=format)),
        ))

        if request.user.is_staff:
            api['core']['users'] = reverse('user-list',
                                           request=request,
                                           format=format)

        return Response(api)


urlpatterns = patterns(
    '',

    url(r'^$', APIRootView.as_view()),

    ##
    # IMPORTS URLS FROM ALL APPS
    ##
    url(r'^', include('core.urls')),
    url(r'^', include('cloud.urls')),
    url(r'^', include('stacks.urls')),
    url(r'^', include('volumes.urls')),
    url(r'^', include('blueprints.urls')),
    url(r'^', include('formulas.urls')),
    url(r'^', include('search.urls')),
)

# Format suffixes - this only should go on API endpoints, not everything!
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
