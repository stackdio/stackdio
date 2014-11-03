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

from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

from core.exceptions import BadRequest
from core.permissions import AdminOrOwnerOrPublicPermission
from . import serializers
from . import models
from . import filters
from . import validators
from stacks.serializers import StackSerializer

logger = logging.getLogger(__name__)


class PublicBlueprintMixin(object):
    permission_classes = (permissions.IsAuthenticated,
                          AdminOrOwnerOrPublicPermission,)

    def get_object(self):
        obj = get_object_or_404(models.Blueprint, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj


class BlueprintListAPIView(generics.ListCreateAPIView):
    model = models.Blueprint
    serializer_class = serializers.BlueprintSerializer
    parser_classes = (JSONParser,)
    filter_class = filters.BlueprintFilter

    def get_queryset(self):
        return self.request.user.blueprints.all()

    def pre_save(self, obj):
        obj.owner = self.request.user

    def create(self, request, *args, **kwargs):
        errors = validators.BlueprintValidator(request).validate()
        if errors:
            raise BadRequest(errors)

        blueprint = models.Blueprint.objects.create(request.user, request.DATA)
        return Response(self.get_serializer(blueprint).data)


class BlueprintPublicAPIView(generics.ListAPIView):
    model = models.Blueprint
    serializer_class = serializers.BlueprintSerializer
    filter_class = filters.BlueprintFilter

    def get_queryset(self):
        return self.model.objects \
            .filter(public=True) \
            .exclude(owner=self.request.user)


class BlueprintAdminListAPIView(generics.ListAPIView):
    model = models.Blueprint
    serializer_class = serializers.BlueprintSerializer
    permission_classes = (permissions.IsAdminUser,)
    filter_class = filters.BlueprintFilter

    def get_queryset(self):
        return self.model.objects.all()


class BlueprintDetailAPIView(PublicBlueprintMixin,
                             generics.RetrieveUpdateDestroyAPIView):
    model = models.Blueprint
    serializer_class = serializers.BlueprintSerializer
    parser_classes = (JSONParser,)

    def update(self, request, *args, **kwargs):
        blueprint = self.get_object()

        # Only the owner of the blueprint can submit PUT/PATCH requests
        if blueprint.owner != request.user:
            raise BadRequest('Only the owner of a blueprint may modify it.')

        # rebuild properties list
        properties = request.DATA.pop('properties', None)
        if properties and not isinstance(properties, str):
            blueprint.properties = properties

        return super(BlueprintDetailAPIView, self).update(request,
                                                          *args,
                                                          **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Override the delete method to check for ownership and prevent
        blueprints from being removed if other resources are using
        them.
        """
        blueprint = self.get_object()

        # Check ownership
        # if blueprint.owner != request.user:
        #     raise BadRequest('Only the owner of a blueprint may delete it.')

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

        return super(BlueprintDetailAPIView, self).delete(request,
                                                          *args,
                                                          **kwargs)


class BlueprintPropertiesAPIView(PublicBlueprintMixin,
                                 generics.RetrieveAPIView):
    model = models.Blueprint
    serializer_class = serializers.BlueprintPropertiesSerializer
