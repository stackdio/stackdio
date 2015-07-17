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
from rest_framework.response import Response

from stackdio.core.exceptions import BadRequest
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
from stackdio.api.formulas.models import FormulaVersion
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.api.stacks.serializers import StackSerializer
from . import serializers, filters, models, validators, permissions, mixins

logger = logging.getLogger(__name__)


class BlueprintListAPIView(generics.ListCreateAPIView):
    """
    Displays a list of all blueprints visible to you.
    """
    queryset = models.Blueprint.objects.all()
    serializer_class = serializers.BlueprintSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.BlueprintFilter

    # TODO redo this method
    def create(self, request, *args, **kwargs):
        errors = validators.BlueprintValidator(request).validate()
        if errors:
            raise BadRequest(errors)

        blueprint = models.Blueprint.objects.create(request.DATA)

        for perm in models.Blueprint.object_permissions:
            assign_perm('blueprints.%s_blueprint' % perm, self.request.user, blueprint)

        return Response(self.get_serializer(blueprint).data)


class BlueprintDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Blueprint.objects.all()
    serializer_class = serializers.BlueprintSerializer
    permission_classes = (StackdioObjectPermissions,)

    def update(self, request, *args, **kwargs):
        blueprint = self.get_object()

        # rebuild properties list
        properties = request.DATA.pop('properties', None)
        if properties and isinstance(properties, dict):
            blueprint.properties = properties
        else:
            logger.warning('Invalid properties for blueprint {0}: {1}'.format(blueprint.title, properties))

        return super(BlueprintDetailAPIView, self).update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Override the delete method to check for ownership and prevent
        blueprints from being removed if other resources are using
        them.
        """
        blueprint = self.get_object()

        # Check usage
        stacks = blueprint.stacks.all()
        if stacks:
            stacks = StackSerializer(stacks,
                                     context=dict(request=request)).data
            return Response({
                'detail': 'This blueprint is in use by one or more '
                          'stacks and cannot be removed.',
                'stacks': stacks
            }, status=status.HTTP_400_BAD_REQUEST)

        return super(BlueprintDetailAPIView, self).delete(request, *args, **kwargs)


class BlueprintPropertiesAPIView(mixins.BlueprintRelatedMixin, generics.RetrieveUpdateAPIView):
    queryset = models.Blueprint.objects.all()
    serializer_class = serializers.BlueprintPropertiesSerializer


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        formula = serializer.validated_data.get('formula')
        blueprint = self.get_blueprint()

        try:
            # Setting self.instance will cause self.update() to be called instead of
            # self.create() during save()
            serializer.instance = blueprint.formula_versions.get(formula=formula)
            response_code = status.HTTP_200_OK
        except FormulaVersion.DoesNotExist:
            # Return the proper response code
            response_code = status.HTTP_201_CREATED

        serializer.save(content_object=blueprint)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=response_code, headers=headers)
