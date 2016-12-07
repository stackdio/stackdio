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


import logging

from guardian.shortcuts import assign_perm
from rest_framework import generics
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.core.permissions import StackdioModelPermissions, StackdioObjectPermissions
from stackdio.core.serializers import ObjectPropertiesSerializer
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)

from . import filters, mixins, models, serializers

logger = logging.getLogger(__name__)


class EnvironmentListAPIView(generics.ListCreateAPIView):
    """
    Displays a list of all environments visible to you.
    """
    queryset = models.Environment.objects.all()
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.EnvironmentFilter
    lookup_field = 'name'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.FullEnvironmentSerializer
        else:
            return serializers.EnvironmentSerializer

    def perform_create(self, serializer):
        env = serializer.save()
        for perm in models.Environment.object_permissions:
            assign_perm('environments.%s_environment' % perm, self.request.user, env)


class EnvironmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Environment.objects.all()
    serializer_class = serializers.EnvironmentSerializer
    permission_classes = (StackdioObjectPermissions,)
    lookup_field = 'name'


class EnvironmentPropertiesAPIView(generics.RetrieveUpdateAPIView):
    queryset = models.Environment.objects.all()
    serializer_class = ObjectPropertiesSerializer
    permission_classes = (StackdioObjectPermissions,)
    lookup_field = 'name'


class EnvironmentLabelListAPIView(mixins.EnvironmentRelatedMixin, generics.ListCreateAPIView):
    serializer_class = serializers.EnvironmentLabelSerializer

    def get_queryset(self):
        environment = self.get_environment()
        return environment.labels.all()

    def get_serializer_context(self):
        context = super(EnvironmentLabelListAPIView, self).get_serializer_context()
        context['content_object'] = self.get_environment()
        return context

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_environment())


class EnvironmentLabelDetailAPIView(mixins.EnvironmentRelatedMixin,
                                    generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.EnvironmentLabelSerializer
    lookup_field = 'key'
    lookup_url_kwarg = 'label_name'

    def get_queryset(self):
        environment = self.get_environment()
        return environment.labels.all()

    def get_serializer_context(self):
        context = super(EnvironmentLabelDetailAPIView, self).get_serializer_context()
        context['content_object'] = self.get_environment()
        return context


class EnvironmentFormulaVersionsAPIView(mixins.EnvironmentRelatedMixin, generics.ListCreateAPIView):
    serializer_class = FormulaVersionSerializer

    def get_queryset(self):
        environment = self.get_environment()
        return environment.formula_versions.all()

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_environment())


class EnvironmentModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    model_cls = models.Environment


class EnvironmentModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    model_cls = models.Environment


class EnvironmentObjectUserPermissionsViewSet(mixins.EnvironmentPermissionsMixin,
                                              StackdioObjectUserPermissionsViewSet):
    pass


class EnvironmentObjectGroupPermissionsViewSet(mixins.EnvironmentPermissionsMixin,
                                               StackdioObjectGroupPermissionsViewSet):
    pass
