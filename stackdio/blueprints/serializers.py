import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import (
    Blueprint,
    BlueprintProperty,
    BlueprintAccessRule,
    BlueprintHostDefinition,
)

from formulas.serializers import FormulaComponentSerializer

logger = logging.getLogger(__name__)


class BlueprintPropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = BlueprintProperty
        fields = (
            'name',
            'value',
        )


class BlueprintAccessRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlueprintAccessRule
        fields = (
            'protocol',
            'from_port',
            'to_port',
            'rule',
        )


class BlueprintHostDefinitionSerializer(serializers.HyperlinkedModelSerializer):

    formula_components = FormulaComponentSerializer(many=True)
    access_rules = BlueprintAccessRuleSerializer(many=True, required=False)

    class Meta:
        model = BlueprintHostDefinition
        fields = (
            'cloud_profile',
            'count',
            'prefix',
            'size',
            'zone',
            'formula_components',
            'access_rules',
        )


class BlueprintSerializer(serializers.HyperlinkedModelSerializer):
    
    properties = BlueprintPropertySerializer(many=True, required=False)
    host_definitions = BlueprintHostDefinitionSerializer(many=True, required=False)

    class Meta:
        model = Blueprint
        fields = (
            'title',
            'description',
            'url',
            'properties',
            'host_definitions',
        )

    def validate(self, attrs):
        # if the user failed to supply a properties list, then
        # we'll default to the empty list
        if attrs.get('properties', None) is None:
            attrs['properties'] = []

        # property names must be unique
        properties = attrs['properties']
        if properties:
            names = set([p.name for p in properties])
            if len(names) != len(properties):
                raise serializers.ValidationError({
                    'properties': ['Property names must be unique.']
                })
        return super(BlueprintSerializer, self).validate(attrs)
