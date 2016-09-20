# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from collections import OrderedDict

import pip
from rest_framework import generics, permissions, views
from rest_framework.response import Response

from stackdio.server import __version__ as stackdio_version
from . import models, serializers

# Do this once at the module level so we don't have to load it multiple times
versions = dict((x.project_name, x) for x in pip.get_installed_distributions())

dep_versions = OrderedDict()

if 'stackdio-server' in versions:
    stackdio_dist = versions['stackdio-server']
    for dist in sorted(stackdio_dist.requires(), key=lambda x: x.project_name.lower()):
        dep_versions[dist.project_name] = versions[dist.project_name].version


class VersionAPIView(views.APIView):
    """
    Returns a JSON object with version-specific fields.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response({
            'version': stackdio_version,
            'dependency_versions': dep_versions,
        })


class EventListAPIView(generics.ListAPIView):
    """
    Get a list of all available events to subscribe to
    """
    queryset = models.Event.objects.all()
    serializer_class = serializers.EventSerializer
    permission_classes = (permissions.IsAuthenticated,)
