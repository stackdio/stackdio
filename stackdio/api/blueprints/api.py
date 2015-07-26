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


import logging

from guardian.shortcuts import assign_perm
from rest_framework import generics, status
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.serializers import ValidationError

from stackdio.core.permissions import (
    StackdioModelPermissions,
    StackdioObjectPermissions,
)
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from . import serializers, filters, models, permissions, mixins

logger = logging.getLogger(__name__)


class BlueprintListAPIView(generics.ListCreateAPIView):
    """
    Displays a list of all blueprints visible to you.
    """
    queryset = models.Blueprint.objects.all()
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.BlueprintFilter

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.FullBlueprintSerializer
        else:
            return serializers.BlueprintSerializer

    def perform_create(self, serializer):
        blueprint = serializer.save()
        for perm in models.Blueprint.object_permissions:
            assign_perm('blueprints.%s_blueprint' % perm, self.request.user, blueprint)


class BlueprintDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Blueprint.objects.all()
    serializer_class = serializers.BlueprintSerializer
    permission_classes = (StackdioObjectPermissions,)

    def perform_destroy(self, instance):
        """
        Check to make sure this blueprint isn't being used by any stacks
        """
        stacks = [s.title for s in instance.stacks.all()]
        if stacks:
            raise ValidationError({
                'detail': 'This blueprint is in use by one or more '
                          'stacks and cannot be removed.',
                'stacks': stacks
            })

        # The blueprint isn't being used, so delete it
        instance.delete()


class BlueprintExportAPIView(generics.RetrieveAPIView):
    """
    This endpoint will produce a valid JSON object that you can use to create a blueprint
    on another stackd.io server.
    """
    queryset = models.Blueprint.objects.all()
    serializer_class = serializers.BlueprintExportSerializer
    permission_classes = (StackdioObjectPermissions,)


class BlueprintPropertiesAPIView(mixins.BlueprintRelatedMixin, generics.RetrieveUpdateAPIView):
    queryset = models.Blueprint.objects.all()
    serializer_class = serializers.BlueprintPropertiesSerializer


class BlueprintHostDefinitionsAPIView(mixins.BlueprintRelatedMixin, generics.ListCreateAPIView):
    serializer_class = serializers.BlueprintHostDefinitionSerializer

    def get_queryset(self):
        blueprint = self.get_blueprint()
        return blueprint.host_definitions.all()

    def perform_create(self, serializer):
        serializer.save(blueprint=self.get_blueprint())


class BlueprintModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    permission_classes = (permissions.BlueprintPermissionsModelPermissions,)
    model_cls = models.Blueprint


class BlueprintModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    permission_classes = (permissions.BlueprintPermissionsModelPermissions,)
    model_cls = models.Blueprint


class BlueprintObjectUserPermissionsViewSet(mixins.BlueprintRelatedMixin,
                                            StackdioObjectUserPermissionsViewSet):
    permission_classes = (permissions.BlueprintPermissionsObjectPermissions,)


class BlueprintObjectGroupPermissionsViewSet(mixins.BlueprintRelatedMixin,
                                             StackdioObjectGroupPermissionsViewSet):
    permission_classes = (permissions.BlueprintPermissionsObjectPermissions,)


class BlueprintFormulaVersionsAPIView(mixins.BlueprintRelatedMixin, generics.ListCreateAPIView):
    serializer_class = FormulaVersionSerializer

    def get_queryset(self):
        blueprint = self.get_blueprint()
        return blueprint.formula_versions.all()

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_blueprint())
