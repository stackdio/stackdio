import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

from . import models

logger = logging.getLogger(__name__)


class BlueprintPropertiesSerializer(serializers.Serializer):
    def to_native(self, obj):
        if obj is not None:
            return obj.properties
        return {}


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
    title = serializers.Field(source='component.title')
    description = serializers.Field(source='component.description')
    formula = serializers.Field(source='component.formula')
    sls_path = serializers.Field(source='component.sls_path')

    class Meta:
        model = models.BlueprintHostFormulaComponent
        fields = (
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
            'title',
            'description',
            'cloud_profile',
            'count',
            'hostname_template',
            'size',
            'zone',
            'formula_components',
            'access_rules',
            'volumes',
            'spot_price',
        )


class BlueprintSerializer(serializers.HyperlinkedModelSerializer):
    
    properties = serializers.HyperlinkedIdentityField(view_name='blueprint-properties')
    host_definitions = BlueprintHostDefinitionSerializer(many=True, required=False)

    class Meta:
        model = models.Blueprint
        fields = (
            'id',
            'title',
            'description',
            'public',
            'url',
            'properties',
            'host_definitions',
        )

