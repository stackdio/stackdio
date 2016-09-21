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

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .utils import get_all_notifiers
from . import serializers


class NotificationsRootView(APIView):
    """
    Root of the stackd.io API. Below are all of the API endpoints that
    are currently accessible. Each API will have its own documentation
    and particular parameters that may discoverable by browsing directly
    to them.
    """

    def get(self, request, format=None):
        notifications = OrderedDict((
            ('notifiers', reverse('stackdio:notifications:notifier-list',
                                  request=request,
                                  format=format)),
        ))

        return Response(notifications)


class NotifierListApiView(generics.ListAPIView):
    queryset = get_all_notifiers()
    serializer_class = serializers.NotifierSerializer
    permission_classes = (permissions.IsAuthenticated,)
