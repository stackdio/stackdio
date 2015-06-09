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

from guardian.shortcuts import assign_perm, remove_perm
from rest_framework import serializers

from core.fields import UserField
from core.utils import recursive_update
from . import models

logger = logging.getLogger(__name__)


def validate_properties(properties):
    """
    Make sure properties are a valid dict and that they don't contain `__stackdio__`
    """
    if not isinstance(properties, dict):
        raise serializers.ValidationError({
            'properties': ['This field must be a JSON object.']
        })

    if '__stackdio__' in properties:
        raise serializers.ValidationError({
            'properties': ['The `__stackdio__` key is reserved for system use.']
        })


class BlueprintPropertiesSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if obj is not None:
            return obj.properties
        return {}

    def to_internal_value(self, data):
        return data

    def validate(self, attrs):
        validate_properties(attrs)
        return attrs

    def create(self, validated_data):
        """
        We never create anything with this serializer, so just leave it as not implemented
        """
        return super(BlueprintPropertiesSerializer, self).create(validated_data)

    def update(self, blueprint, validated_data):
        if self.partial:
            # This is a PATCH, so properly merge in the old data
            old_properties = blueprint.properties
            blueprint.properties = recursive_update(old_properties, validated_data)
        else:
            # This is a PUT, so just add the data directly
            blueprint.properties = validated_data

        return blueprint


class BlueprintAccessRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BlueprintAccessRule
        fields = (
            'protocol',
            'from_port',
            'to_port',
            'rule',
        )


class BlueprintVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BlueprintVolume
        fields = (
            'device',
            'mount_point',
            'snapshot',
        )


class BlueprintHostFormulaComponentSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.ReadOnlyField(source='component.title')
    description = serializers.ReadOnlyField(source='component.description')
    formula = serializers.PrimaryKeyRelatedField(read_only=True, source='component.formula')
    component_id = serializers.ReadOnlyField(source='component.id')
    sls_path = serializers.ReadOnlyField(source='component.sls_path')

    class Meta:
        model = models.BlueprintHostFormulaComponent
        fields = (
            'component_id',
            'title',
            'description',
            'formula',
            'sls_path',
            'order',
        )


class BlueprintHostDefinitionSerializer(serializers.HyperlinkedModelSerializer):
    formula_components = BlueprintHostFormulaComponentSerializer(many=True)
    access_rules = BlueprintAccessRuleSerializer(many=True, required=False)
    volumes = BlueprintVolumeSerializer(many=True)

    class Meta:
        model = models.BlueprintHostDefinition
        fields = (
            'id',
            'title',
            'description',
            'cloud_profile',
            'count',
            'hostname_template',
            'size',
            'zone',
            'subnet_id',
            'formula_components',
            'access_rules',
            'volumes',
            'spot_price',
        )


class BlueprintSerializer(serializers.HyperlinkedModelSerializer):
    properties = serializers.HyperlinkedIdentityField(view_name='blueprint-properties')
    user_permissions = serializers.HyperlinkedIdentityField(view_name='blueprint-user-permissions-list')
    host_definitions = BlueprintHostDefinitionSerializer(many=True)
    formula_versions = serializers.HyperlinkedIdentityField(view_name='blueprint-formula-versions')

    class Meta:
        model = models.Blueprint
        fields = (
            'id',
            'title',
            'description',
            'url',
            'properties',
            'user_permissions',
            'formula_versions',
            'host_definitions',
        )


class BlueprintPermissionsSerializer(serializers.Serializer):
    user = UserField()
    permissions = serializers.ListField()

    def create(self, validated_data):
        # Grab our data
        user = validated_data['user']
        blueprint = validated_data['blueprint']
        for perm in validated_data['permissions']:
            assign_perm('blueprints.%s_blueprint' % perm, user, blueprint)

        return self.to_internal_value(validated_data)

    def update(self, instance, validated_data):
        # The funkiness below is to prevent a client from submitting a PUT or PATCH request to
        # /api/<resource>/<pk>/permissions/users/user_id1 with user="user_id2".  If this were
        # allowed, you could change the permissions of any user from the endpoint of any other user

        # Pull the user from the instance to update rather than from the incoming request
        user = instance['user']
        # Then add it to the validated_data so the create request uses the correct user
        validated_data['user'] = user
        blueprint = validated_data['blueprint']

        if not self.partial:
            # PUT request - delete all the permissions, then recreate them later
            for perm in instance['permissions']:
                remove_perm('blueprints.%s_blueprint' % perm, user, blueprint)

        # We now want to do the same thing as create
        return self.create(validated_data)
