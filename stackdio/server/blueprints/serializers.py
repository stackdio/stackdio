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

from rest_framework import serializers

from core.utils import recursive_update
from . import models

logger = logging.getLogger(__name__)


class BlueprintPropertiesSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if obj is not None:
            return obj.properties
        return {}

    def to_internal_value(self, data):
        return data

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return recursive_update(instance, validated_data)


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
    # Read only fields
    owner = serializers.ReadOnlyField(source='owner.username')

    properties = serializers.HyperlinkedIdentityField(view_name='blueprint-properties')
    host_definitions = BlueprintHostDefinitionSerializer(many=True)

    class Meta:
        model = models.Blueprint
        fields = (
            'id',
            'title',
            'description',
            'owner',
            'public',
            'url',
            'properties',
            'host_definitions',
        )

    def validate(self, attrs):
        return attrs