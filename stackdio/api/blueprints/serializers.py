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
import string

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction
from django.utils.encoding import smart_text
from rest_framework import serializers
from rest_framework.compat import OrderedDict
from rest_framework.settings import api_settings

from stackdio.core.utils import recursive_update
from stackdio.core.validators import PropertiesValidator
from stackdio.api.cloud.models import CloudInstanceSize, CloudProfile, CloudZone
from stackdio.api.formulas.models import Formula, FormulaComponent
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.api.volumes.models import Volume
from . import models

logger = logging.getLogger(__name__)


class BlueprintPropertiesSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if obj is not None:
            # Make it work two different ways.. ooooh
            if isinstance(obj, models.Blueprint):
                return obj.properties
            else:
                return obj
        return {}

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
    snapshot = serializers.SlugRelatedField(slug_field='slug', queryset=Volume.objects.all())

    class Meta:
        model = models.BlueprintVolume
        fields = (
            'device',
            'mount_point',
            'snapshot',
        )


class BlueprintHostFormulaComponentSerializer(serializers.HyperlinkedModelSerializer):
    # Read only fields
    title = serializers.ReadOnlyField(source='component.title')
    description = serializers.ReadOnlyField(source='component.description')

    # Possibly required
    formula = serializers.SlugRelatedField(source='component.formula', slug_field='uri',
                                           queryset=Formula.objects.all(), required=False)

    # Definitely required
    sls_path = serializers.SlugRelatedField(source='component', slug_field='sls_path',
                                            queryset=FormulaComponent.objects.all())

    class Meta:
        model = models.BlueprintHostFormulaComponent
        fields = (
            'title',
            'description',
            'formula',
            'sls_path',
            'order',
        )

        extra_kwargs = {
            'order': {'min_value': 0, 'default': serializers.CreateOnlyDefault(0)}
        }

    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        if not isinstance(data, dict):
            message = self.error_messages['invalid'].format(
                datatype=type(data).__name__
            )
            raise serializers.ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            })

        ret = OrderedDict()
        errors = OrderedDict()

        def _get_field_value(field):
            # Pulled from the for loop in rest_framework.serializers:Serializer.to_internal_value()
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except serializers.ValidationError as e:
                errors[field.field_name] = e.detail
            except serializers.DjangoValidationError as e:
                errors[field.field_name] = list(e.messages)
            except serializers.SkipField:
                pass
            else:
                # Everything looks ok, just return the value
                return validated_value

            # Something went wrong, just return None
            return None

        # We only need two things - the component and the order

        # First get the component from some combination of the sls_path and the formula
        sls_field = self.fields['sls_path']
        formula_field = self.fields['formula']

        try:
            # The sls_path field should just return the component the say it's set up
            component = _get_field_value(sls_field)
            if component is not None:
                ret['component'] = component
        except MultipleObjectsReturned:
            # The _get_field_value() method won't catch this exception, so we handle it here
            # If there were multiple objects for the sls_path, then they must provide a formula
            # to disambiguate the component
            formula = _get_field_value(formula_field)
            sls_primitive_value = sls_field.get_value(data)
            if formula is None:
                # Ambiguous sls_path with no formula specified.
                err_msg = ('The sls_path "{0}" is contained in multiple formulas. '
                           'Please specify a formula uri.'.format(sls_primitive_value))
                errors.setdefault('sls_path', []).append(err_msg)
            else:
                try:
                    # Grab the component from the formula's list of components
                    ret['component'] = formula.components.get(sls_path=sls_primitive_value)
                except ObjectDoesNotExist:
                    msg = sls_field.error_messages['does_not_exist'].format(
                        slug_name='sls_path',
                        value=smart_text(sls_primitive_value)
                    )
                    errors.setdefault('sls_path', []).append(msg)
                except (TypeError, ValueError):
                    msg = sls_field.error_messages['invalid']
                    errors.setdefault('sls_path', []).append(msg)

        # Next do the order.  Nothing special here, just simple
        order_field = self.fields['order']
        order_value = _get_field_value(order_field)
        if order_value is not None:
            # Only if it's not None.  If it was None, something went wrong
            serializers.set_value(ret, order_field.source_attrs, order_value)

        # Check for errors, and raise the exception
        if errors:
            raise serializers.ValidationError(errors)

        return ret


class BlueprintHostDefinitionSerializer(serializers.HyperlinkedModelSerializer):
    formula_components = BlueprintHostFormulaComponentSerializer(many=True)
    access_rules = BlueprintAccessRuleSerializer(many=True, required=False)
    volumes = BlueprintVolumeSerializer(many=True, required=False)

    size = serializers.SlugRelatedField(slug_field='instance_id',
                                        queryset=CloudInstanceSize.objects.all())
    zone = serializers.SlugRelatedField(slug_field='title', required=False,
                                        queryset=CloudZone.objects.all())
    cloud_profile = serializers.SlugRelatedField(slug_field='slug',
                                                 queryset=CloudProfile.objects.all())

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
            'subnet_id',
            'formula_components',
            'access_rules',
            'volumes',
            'spot_price',
        )

        extra_kwargs = {
            'spot_price': {'min_value': 0.0},
        }

    def validate(self, attrs):
        hostname_template = attrs['hostname_template']
        count = attrs['count']

        # Validate hostname template
        formatter = string.Formatter()
        template_vars = [x[1] for x in formatter.parse(hostname_template) if x[1]]

        errors = {}

        if count > 1 and 'index' not in template_vars:
            err_msg = '`hostname_template` must contain "{index}" when `count` > 1'
            errors.setdefault('hostname_template', []).append(err_msg)
            errors.setdefault('count', []).append(err_msg)

        # Validate zone / subnet id
        profile = attrs['cloud_profile']
        account = profile.account

        if account.vpc_enabled:
            # If we're in a vpc, we need a VALID subnet id
            subnet_id = attrs.get('subnet_id')
            if subnet_id is None:
                err_msg = 'This is a required field for a profile in a vpc enabled account.'
                errors.setdefault('subnet_id', []).append(err_msg)

            driver = profile.get_driver()
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
            component['host'] = host_definition
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


class BlueprintSerializer(serializers.HyperlinkedModelSerializer):
    properties = serializers.HyperlinkedIdentityField(
        view_name='blueprint-properties')
    host_definitions = serializers.HyperlinkedIdentityField(
        view_name='blueprint-host-definition-list')
    formula_versions = serializers.HyperlinkedIdentityField(
        view_name='blueprint-formula-versions')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='blueprint-object-user-permissions-list')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='blueprint-object-group-permissions-list')
    export = serializers.HyperlinkedIdentityField(
        view_name='blueprint-export')

    class Meta:
        model = models.Blueprint
        fields = (
            'id',
            'url',
            'title',
            'description',
            'create_users',
            'properties',
            'host_definitions',
            'formula_versions',
            'user_permissions',
            'group_permissions',
            'export',
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

    def validate(self, attrs):
        host_definitions = attrs['host_definitions']
        if len(host_definitions) < 1:
            raise serializers.ValidationError({
                'host_definitions': ['You must supply at least 1 host definition.']
            })

        # Validate component ordering
        order_set = set()

        # Grab all the orders from each component on each host_definition
        for host_definition in host_definitions:
            formula_components = host_definition['formula_components']
            order_set.update([c['order'] for c in formula_components])

        # Every number in the range [0, MAX_ORDER] should be represented
        if sorted(order_set) != range(len(order_set)):
            err_msg = ('Ordering is zero-based, may have duplicates across hosts, but '
                       'can not have any gaps in the order. '
                       'Your de-duplicated order: {0}'.format(sorted(order_set)))
            raise serializers.ValidationError({
                'host_definitions': [err_msg]
            })

        return attrs

    def create(self, validated_data):
        # Pull out the nested stuff
        host_definitions = validated_data.pop('host_definitions')
        properties = validated_data.pop('properties', {})
        formula_versions = validated_data.pop('formula_versions', [])

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
                formula_version['blueprint'] = blueprint
            formula_version_field.create(formula_versions)

        # Add the other fields back in for deserialization
        validated_data['properties'] = properties
        validated_data['host_definitions'] = host_definitions
        validated_data['formula_versions'] = formula_versions

        return blueprint


class BlueprintExportSerializer(FullBlueprintSerializer):
    class Meta:
        model = models.Blueprint
        fields = (
            'title',
            'description',
            'create_users',
            'properties',
            'host_definitions',
            'formula_versions',
        )
