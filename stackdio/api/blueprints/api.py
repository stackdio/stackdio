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
from rest_framework.serializers import ValidationError

from stackdio.core.permissions import StackdioModelPermissions, StackdioObjectPermissions
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)
from stackdio.api.formulas.models import FormulaVersion
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from . import serializers, filters, models, mixins

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

        # Create all the formula versions
        for formula in blueprint.get_formulas():
            # Make sure the version doesn't already exist (could have been created in
            # the serializer.save() call)
            try:
                blueprint.formula_versions.get(formula=formula)
            except FormulaVersion.DoesNotExist:
                blueprint.formula_versions.create(formula=formula, version=formula.default_version)


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
                'detail': ['This blueprint is in use by one or more '
                           'stacks and cannot be removed.'],
                'stacks': stacks,
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


class BlueprintPropertiesAPIView(generics.RetrieveUpdateAPIView):
    queryset = models.Blueprint.objects.all()
    serializer_class = serializers.BlueprintPropertiesSerializer
    permission_classes = (StackdioObjectPermissions,)


class BlueprintHostDefinitionListAPIView(mixins.BlueprintRelatedMixin, generics.ListCreateAPIView):
    serializer_class = serializers.BlueprintHostDefinitionSerializer

    def get_queryset(self):
        blueprint = self.get_blueprint()
        return blueprint.host_definitions.all()

    def perform_create(self, serializer):
        serializer.save(blueprint=self.get_blueprint())


class BlueprintHostDefinitionDetailAPIView(mixins.BlueprintRelatedMixin,
                                           generics.RetrieveUpdateAPIView):
    serializer_class = serializers.BlueprintHostDefinitionSerializer

    def get_queryset(self):
        blueprint = self.get_blueprint()
        return blueprint.host_definitions.all()


class BlueprintFormulaVersionsAPIView(mixins.BlueprintRelatedMixin, generics.ListCreateAPIView):
    serializer_class = FormulaVersionSerializer

    def get_queryset(self):
        blueprint = self.get_blueprint()
        return blueprint.formula_versions.all()

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_blueprint())


class BlueprintLabelListAPIView(mixins.BlueprintRelatedMixin, generics.ListCreateAPIView):
    serializer_class = serializers.BlueprintLabelSerializer

    def get_queryset(self):
        blueprint = self.get_blueprint()
        return blueprint.labels.all()

    def get_serializer_context(self):
        context = super(BlueprintLabelListAPIView, self).get_serializer_context()
        context['content_object'] = self.get_blueprint()
        return context

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_blueprint())


class BlueprintLabelDetailAPIView(mixins.BlueprintRelatedMixin,
                                  generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.BlueprintLabelSerializer
    lookup_field = 'key'
    lookup_url_kwarg = 'label_name'

    def get_queryset(self):
        blueprint = self.get_blueprint()
        return blueprint.labels.all()

    def get_serializer_context(self):
        context = super(BlueprintLabelDetailAPIView, self).get_serializer_context()
        context['content_object'] = self.get_blueprint()
        return context


# All the permissions things
class BlueprintModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    model_cls = models.Blueprint


class BlueprintModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    model_cls = models.Blueprint


class BlueprintObjectUserPermissionsViewSet(mixins.BlueprintPermissionsMixin,
                                            StackdioObjectUserPermissionsViewSet):
    pass


class BlueprintObjectGroupPermissionsViewSet(mixins.BlueprintPermissionsMixin,
                                             StackdioObjectGroupPermissionsViewSet):
    pass
