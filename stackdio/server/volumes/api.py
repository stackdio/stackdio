# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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


import logging

from rest_framework import generics
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter

from core.permissions import StackdioDjangoObjectPermissions
from . import filters, models, serializers

logger = logging.getLogger(__name__)


class VolumeListAPIView(generics.ListAPIView):
    queryset = models.Volume.objects.all()
    serializer_class = serializers.VolumeSerializer
    permission_classes = (StackdioDjangoObjectPermissions,)
    filter_backends = (DjangoFilterBackend, DjangoObjectPermissionsFilter)
    filter_class = filters.VolumeFilter


class VolumeDetailAPIView(generics.RetrieveAPIView):
    queryset = models.Volume.objects.all()
    serializer_class = serializers.VolumeSerializer
    permission_classes = (StackdioDjangoObjectPermissions,)
