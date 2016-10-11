# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

# pylint: disable=abstract-method

from __future__ import unicode_literals

import logging
import string

from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from stackdio.api.cloud.models import CloudImage, CloudInstanceSize, CloudZone, Snapshot
from stackdio.api.formulas.serializers import FormulaVersionSerializer, FormulaComponentSerializer
from stackdio.api.formulas.validators import validate_formula_components
from stackdio.core.mixins import CreateOnlyFieldsMixin
from stackdio.core.serializers import (
    StackdioHyperlinkedModelSerializer,
    StackdioParentHyperlinkedModelSerializer,
    StackdioLabelSerializer,
    StackdioLiteralLabelsSerializer,
)
from stackdio.core.utils import recursive_update, recursively_sort_dict
from stackdio.core.validators import PropertiesValidator

from . import models, validators

logger = logging.getLogger(__name__)


class BlueprintPropertiesSerializer(serializers.Serializer):
    def to_representation(self, obj):
        ret = {}
        if obj is not None:
            # Make it work two different ways.. ooooh
            if isinstance(obj, models.Blueprint):
                ret = obj.properties
            else:
                ret = obj
        return recursively_sort_dict(ret)

    def to_internal_value(self, data):
        return data

    def validate(self, attrs):
        PropertiesValidator().validate(attrs)
        return attrs

    def update(self, instance, validated_data):
        blueprint = instance
        if self.partial:
            # This is a PATCH, so properly merge in the old data
            old_properties = blueprint.properties
            blueprint.properties = recursive_update(old_properties, validated_data)
        else:
            # This is a PUT, so just add the data directly
            blueprint.properties = validated_data

        # Be sure to persist the data
        blueprint.save()
        return blueprint


class BlueprintAccessRuleSerializer(serializers.ModelSerializer):
    from_port = serializers.IntegerField(min_value=0, max_value=65535)
    to_port = serializers.IntegerField(min_value=0, max_value=65535)

    class Meta:
        model = models.BlueprintAccessRule
        fields = (
            'protocol',
            'from_port',
            'to_port',
            'rule',
        )

    def validate(self, attrs):
        from_port = attrs['from_port']
        to_port = attrs['to_port']

        if from_port > to_port:
            err_msg = '`from_port` ({0}) must be less than `to_port` ({1})'.format(from_port,
                                                                                   to_port)
            raise serializers.ValidationError({
                'from_port': [err_msg],
                'to_port': [err_msg],
            })

        return attrs


class BlueprintVolumeSerializer(serializers.ModelSerializer):
    snapshot = serializers.SlugRelatedField(slug_field='slug', queryset=Snapshot.objects.all(),
                                            allow_null=True, default=None)

    extra_options = serializers.JSONField(default={})

    class Meta:
        model = models.BlueprintVolume
        fields = (
            'device',
            'mount_point',
            'snapshot',
            'size_in_gb',
            'encrypted',
            'extra_options',
        )

        extra_kwargs = {
            'size_in_gb': {'default': None},
        }

    def validate(self, attrs):
        snapshot = attrs.get('snapshot')

        size = attrs.get('size_in_gb')

        if snapshot and size:
            err_msg = 'You may only specify one of `snapshot` or `size_in_gb`.'
            raise serializers.ValidationError({
                'snapshot': [err_msg],
                'size_in_gb': [err_msg],
            })

        if not snapshot and not size:
            err_msg = 'You must specify either `snapshot` or `size_in_gb`.'
            raise serializers.ValidationError({
                'snapshot': [err_msg],
                'size_in_gb': [err_msg],
            })

        return attrs


class BlueprintHostDefinitionSerializer(CreateOnlyFieldsMixin,
                                        StackdioParentHyperlinkedModelSerializer):
    formula_components = FormulaComponentSerializer(many=True)
    access_rules = BlueprintAccessRuleSerializer(many=True, required=False)
    volumes = BlueprintVolumeSerializer(many=True, required=False)

    size = serializers.SlugRelatedField(slug_field='instance_id',
                                        queryset=CloudInstanceSize.objects.all())
    zone = serializers.SlugRelatedField(slug_field='title', required=False, allow_null=True,
                                        queryset=CloudZone.objects.all())
    cloud_image = serializers.SlugRelatedField(slug_field='slug',
                                               queryset=CloudImage.objects.all())
    extra_options = serializers.JSONField(default={})

    class Meta:
        model = models.BlueprintHostDefinition
        model_name = 'blueprint-host-definition'
        parent_attr = 'blueprint'
        fields = (
            'id',
            'url',
            'title',
            'description',
            'cloud_image',
            'count',
            'hostname_template',
            'size',
            'zone',
            'subnet_id',
            'spot_price',
            'formula_components',
            'access_rules',
            'volumes',
            'extra_options',
        )

        create_only_fields = (
            'cloud_image',
            'size',
            'formula_components',
            'access_rules',
            'volumes',
        )

        extra_kwargs = {
            'spot_price': {'min_value': 0.0},
            'subnet_id': {'allow_null': True},
            'hostname_template': {'validators': [validators.BlueprintHostnameTemplateValidator()]},
        }

    def validate(self, attrs):
        hostname_template = attrs.get('hostname_template')

        errors = {}

        # Only validate the hostname template if we have one
        if hostname_template is not None:
            count = attrs.get('count')
            if count is None:
                if not self.instance:
                    raise ValueError('`count` not found and the serializer doesn\'t '
                                     'have an instance attribute')
                # Grab the count from the instance
                count = self.instance.count

            # Validate hostname template
            formatter = string.Formatter()
            template_vars = [x[1] for x in formatter.parse(hostname_template) if x[1]]

            if count > 1 and 'index' not in template_vars:
                err_msg = '`hostname_template` must contain "{index}" when `count` > 1'
                errors.setdefault('hostname_template', []).append(err_msg)
                errors.setdefault('count', []).append(err_msg)

        # Validate zone / subnet id
        image = attrs.get('cloud_image')
        if image is None:
            if not self.instance:
                raise ValueError('`cloud_image` not found and the serializer doesn\'t '
                                 'have an instance attribute')
            # Grab the image from the instance
            image = self.instance.cloud_image

        account = image.account

        if account.vpc_enabled:
            # If we're in a vpc, we need a VALID subnet id
            subnet_id = attrs.get('subnet_id')
            if subnet_id is None:
                err_msg = 'This is a required field for a image in a vpc enabled account.'
                errors.setdefault('subnet_id', []).append(err_msg)

            driver = image.get_driver()
            subnets = driver.get_vpc_subnets([subnet_id])
            if subnets is None:
                err_msg = '"{0}" is not a valid subnet id.'.format(subnet_id)
                errors.setdefault('subnet_id', []).append(err_msg)
        else:
            # if we're not in a VPC, we only need a zone
            zone = attrs.get('zone')
            if zone is None:
                err_msg = 'This is a required field for a provile in a non-vpc enabled account.'
                errors.setdefault('zone', []).append(err_msg)

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        formula_components = validated_data.pop('formula_components')
        access_rules = validated_data.pop('access_rules', [])
        volumes = validated_data.pop('volumes', [])

        host_definition = super(BlueprintHostDefinitionSerializer, self).create(validated_data)

        # Create the formula components
        formula_component_field = self.fields['formula_components']
        # Add in the host definition to all the formula components
        for component in formula_components:
            component['content_object'] = host_definition
        formula_component_field.create(formula_components)

        # Create the access rules
        access_rule_field = self.fields['access_rules']
        # Add in the host definition to all the access rules
        for access_rule in access_rules:
            access_rule['host'] = host_definition
        access_rule_field.create(access_rules)

        # Create the volumes
        volume_field = self.fields['volumes']
        # Add in the host definition to all the volumes
        for volume in volumes:
            volume['host'] = host_definition
        volume_field.create(volumes)

        return host_definition


class BlueprintSerializer(StackdioHyperlinkedModelSerializer):
    label_list = StackdioLiteralLabelsSerializer(read_only=True, many=True,
                                                 source='get_cached_label_list')

    properties = serializers.HyperlinkedIdentityField(
        view_name='api:blueprints:blueprint-properties')
    host_definitions = serializers.HyperlinkedIdentityField(
        view_name='api:blueprints:blueprint-host-definition-list',
        lookup_url_kwarg='parent_pk')
    formula_versions = serializers.HyperlinkedIdentityField(
        view_name='api:blueprints:blueprint-formula-versions',
        lookup_url_kwarg='parent_pk')
    labels = serializers.HyperlinkedIdentityField(
        view_name='api:blueprints:blueprint-label-list',
        lookup_url_kwarg='parent_pk')
    export = serializers.HyperlinkedIdentityField(
        view_name='api:blueprints:blueprint-export')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:blueprints:blueprint-object-user-permissions-list',
        lookup_url_kwarg='parent_pk')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:blueprints:blueprint-object-group-permissions-list',
        lookup_url_kwarg='parent_pk')

    class Meta:
        model = models.Blueprint
        fields = (
            'id',
            'url',
            'title',
            'description',
            'create_users',
            'stack_count',
            'label_list',
            'properties',
            'host_definitions',
            'formula_versions',
            'labels',
            'export',
            'user_permissions',
            'group_permissions',
        )

        extra_kwargs = {
            'create_users': {
                'default': serializers.CreateOnlyDefault(settings.STACKDIO_CONFIG.create_ssh_users)
            },
        }


class FullBlueprintSerializer(BlueprintSerializer):
    properties = BlueprintPropertiesSerializer(required=False)
    host_definitions = BlueprintHostDefinitionSerializer(many=True)
    formula_versions = FormulaVersionSerializer(many=True, required=False)
    labels = StackdioLiteralLabelsSerializer(many=True, required=False)

    def validate(self, attrs):
        host_definitions = attrs['host_definitions']
        formula_versions = attrs.get('formula_versions', [])
        if len(host_definitions) < 1:
            raise serializers.ValidationError({
                'host_definitions': ['You must supply at least 1 host definition.']
            })

        errors = {}

        # Make sure the titles don't conflict
        titles = []
        hostnames = []
        for host_definition in host_definitions:
            title = host_definition['title']
            hostname = host_definition['hostname_template']
            if title in titles:
                err_msg = 'Duplicate title: {0}'.format(title)
                errors.setdefault('host_definitions', []).append(err_msg)
            if hostname in hostnames:
                err_msg = 'Duplicate hostname template: {0}'.format(hostname)
                errors.setdefault('host_definitions', []).append(err_msg)
            titles.append(title)
            hostnames.append(hostname)

        # Validate component ordering, and ensure that component ordering matches
        # across host definitions
        order_set = set()
        component_map = {}

        # Grab all the orders from each component on each host_definition
        for host_definition in host_definitions:
            formula_components = host_definition['formula_components']

            # Validate the components (i.e. make sure they exist in the formula on the
            # specified version)
            formula_components = validate_formula_components(formula_components, formula_versions)

            for component in formula_components:
                # Add the order to the order set
                order_set.add(component['order'])
                # Also add the order to the component map
                component_map.setdefault(component['sls_path'], set()).add(component['order'])

        for component, orders in component_map.items():
            if len(orders) > 1:
                err_msg = 'Formula component "{0}" has inconsistent orders across host definitions.'
                errors.setdefault('host_definitions', []).append(err_msg.format(component))

        # Every number in the range [0, MAX_ORDER] should be represented
        if sorted(order_set) != range(len(order_set)):
            err_msg = ('Ordering is zero-based, may have duplicates across hosts, but '
                       'can not have any gaps in the order. '
                       'Your de-duplicated order: {0}'.format(sorted(order_set)))
            errors.setdefault('host_definitions', []).append(err_msg)

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        # Pull out the nested stuff
        host_definitions = validated_data.pop('host_definitions')
        properties = validated_data.pop('properties', {})
        formula_versions = validated_data.pop('formula_versions', [])
        labels = validated_data.pop('labels', [])

        with transaction.atomic(using=models.Blueprint.objects.db):
            # Create the blueprint
            blueprint = super(FullBlueprintSerializer, self).create(validated_data)

            # Set the properties
            blueprint.properties = properties

            # Create the host definitions
            host_definition_field = self.fields['host_definitions']
            # Add in the blueprint to all the host defs
            for host_definition in host_definitions:
                host_definition['blueprint'] = blueprint
            host_definition_field.create(host_definitions)

            # Create the formula versions
            formula_version_field = self.fields['formula_versions']
            # Add in the blueprint to all the formula versions
            for formula_version in formula_versions:
                formula_version['content_object'] = blueprint
            formula_version_field.create(formula_versions)

            # Create the labels
            label_field = self.fields['labels']
            # Add in the blueprint to all the labels
            for label in labels:
                label['content_object'] = blueprint
            label_field.create(labels)

        # Add the other fields back in for deserialization
        validated_data['properties'] = properties
        validated_data['host_definitions'] = host_definitions
        validated_data['formula_versions'] = formula_versions
        validated_data['labels'] = labels

        return blueprint


class BlueprintExportSerializer(FullBlueprintSerializer):
    class Meta:
        model = models.Blueprint
        fields = (
            'title',
            'description',
            'create_users',
            'properties',
            'labels',
            'host_definitions',
            'formula_versions',
        )


class BlueprintLabelSerializer(StackdioLabelSerializer):

    class Meta(StackdioLabelSerializer.Meta):
        app_label = 'blueprints'
        model_name = 'blueprint-label'
