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

from rest_framework import permissions
from rest_framework import serializers

from core.mixins import SuperuserFieldsMixin
from core.utils import recursive_update
from formulas.serializers import FormulaComponentSerializer
from . import models
from .utils import get_provider_type_and_class

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


class CloudProviderTypeSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.ReadOnlyField(source='get_type_name_display')

    class Meta:
        model = models.CloudProviderType
        fields = (
            'id',
            'url',
            'title',
            'type_name',
        )


class CloudProviderSerializer(SuperuserFieldsMixin,
                              serializers.HyperlinkedModelSerializer):
    # Read only fields
    provider_type_name = serializers.ReadOnlyField(source='provider_type.type_name')

    # Foreign Key Relations
    provider_type = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudProviderType.objects.all())
    region = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudRegion.objects.all())

    # Hyperlinks
    security_groups = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-securitygroup-list')
    vpc_subnets = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-vpcsubnet-list')
    global_orchestration_components = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-global-orchestration-list')
    global_orchestration_properties = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-global-orchestration-properties')

    class Meta:
        model = models.CloudProvider
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'provider_type',
            'provider_type_name',
            'account_id',
            'vpc_id',
            'region',
            'security_groups',
            'vpc_subnets',
            'global_orchestration_components',
            'global_orchestration_properties',
        )

    def validate(self, attrs):
        # validate provider specific request data
        request = self.context['request']

        # patch requests only accept a few things for modification
        if request.method == 'PATCH':
            fields_available = ('title',
                                'description')
            # TODO removed default AZ for now, might add in region later

            errors = {}
            for k in request.DATA:
                if k not in fields_available:
                    errors.setdefault(k, []).append(
                        'Field may not be modified.')
            if errors:
                logger.debug(errors)
                raise serializers.ValidationError(errors)

        elif request.method == 'POST':

            provider_type, provider_class = get_provider_type_and_class(
                request.DATA.get('provider_type'))

            # Grab the region name from the database
            try:
                region = models.CloudRegion.objects.get(id=request.DATA['region']).slug
                request.DATA['region'] = region
            except models.CloudRegion.DoesNotExist:
                raise serializers.ValidationError('Invalid region')

            provider = provider_class()
            errors = provider.validate_provider_data(request.DATA,
                                                     request.FILES)

            if errors:
                logger.error('Cloud provider validation errors: '
                             '{0}'.format(errors))
                raise serializers.ValidationError(errors)

        return attrs


class VPCSubnetSerializer(serializers.Serializer):
    vpc_id = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    availability_zone = serializers.ReadOnlyField()
    cidr_block = serializers.ReadOnlyField()
    tags = serializers.ReadOnlyField()


class CloudInstanceSizeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.CloudInstanceSize
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'provider_type',
            'instance_id',
        )


class GlobalOrchestrationFormulaComponentSerializer(serializers.HyperlinkedModelSerializer):
    component = serializers.PrimaryKeyRelatedField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(GlobalOrchestrationFormulaComponentSerializer, self).__init__(*args, **kwargs)

        # If read request, put in the component object, otherwise just pk
        context = kwargs.get('context')
        if context:
            request = context.get('request')
            if request and request.method in permissions.SAFE_METHODS:
                self.fields['component'] = FormulaComponentSerializer()

    class Meta:
        model = models.GlobalOrchestrationFormulaComponent
        fields = (
            'id',
            'url',
            'order',
            'component',
        )


class GlobalOrchestrationPropertiesSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if obj is not None:
            return obj.global_orchestration_properties
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
        return super(GlobalOrchestrationPropertiesSerializer, self).create(validated_data)

    def update(self, provider, validated_data):
        if self.partial:
            # This is a PATCH, so properly merge in the old data
            old_properties = provider.global_orchestration_properties
            provider.global_orchestration_properties = recursive_update(old_properties, validated_data)
        else:
            # This is a PUT, so just add the data directly
            provider.global_orchestration_properties = validated_data

        # Be sure to persist the data
        provider.save()
        return provider


class CloudProfileSerializer(SuperuserFieldsMixin,
                             serializers.HyperlinkedModelSerializer):
    cloud_provider = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudProvider.objects.all()
    )
    default_instance_size = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudInstanceSize.objects.all()
    )

    class Meta:
        model = models.CloudProfile
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'cloud_provider',
            'image_id',
            'default_instance_size',
            'ssh_user',
        )

        superuser_fields = ('image_id',)

    # TODO: Ignoring code complexity issues
    def validate(self, attrs):  # NOQA
        # validate provider specific request data
        request = self.context['request']

        # patch requests only accept a few things for modification
        if request.method in ('PATCH', 'PUT'):
            fields_available = ('title',
                                'description',
                                'image_id',
                                'default_instance_size',
                                'ssh_user',)

            errors = {}
            for k in request.DATA:
                if k not in fields_available:
                    errors.setdefault(k, []).append(
                        'Field may not be modified.')
            if errors:
                logger.debug(errors)
                raise serializers.ValidationError(errors)

        elif request.method == 'POST':
            image_id = request.DATA.get('image_id')
            provider_id = request.DATA.get('cloud_provider')
            if not provider_id:
                raise serializers.ValidationError({
                    'cloud_provider': 'Required field.'
                })

            provider = models.CloudProvider.objects.get(pk=provider_id)
            driver = provider.get_driver()

            valid, exc_msg = driver.validate_image_id(image_id)
            if not valid:
                raise serializers.ValidationError({
                    'image_id': ['Image ID does not exist on the given cloud '
                                 'provider. Check that it exists and you have '
                                 'access to it.'],
                    'image_id_exception': [exc_msg]
                })

        return attrs


class SnapshotSerializer(serializers.HyperlinkedModelSerializer):
    cloud_provider = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudProvider.objects.all()
    )

    class Meta:
        model = models.Snapshot
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'cloud_provider',
            'snapshot_id',
            'size_in_gb',
            'filesystem_type',
        )

    def validate(self, attrs):
        request = self.context['request']

        # validate that the snapshot exists by looking it up in the cloud
        # provider
        provider_id = request.DATA.get('cloud_provider')
        driver = models.CloudProvider.objects.get(pk=provider_id).get_driver()

        result, error = driver.has_snapshot(request.DATA['snapshot_id'])
        if not result:
            raise serializers.ValidationError({'errors': [error]})
        return attrs


class CloudRegionSerializer(serializers.HyperlinkedModelSerializer):
    provider_type = serializers.PrimaryKeyRelatedField(read_only=True)
    zones = serializers.StringRelatedField(many=True, read_only=True)
    zones_url = serializers.HyperlinkedIdentityField(view_name='cloudregion-zones')

    class Meta:
        model = models.CloudRegion
        fields = (
            'id',
            'title',
            'provider_type',
            'zones',
            'zones_url',
        )


class CloudZoneSerializer(serializers.HyperlinkedModelSerializer):
    provider_type = serializers.PrimaryKeyRelatedField(
        source='region.provider_type',
        queryset=models.CloudProviderType.objects.all()
    )

    class Meta:
        model = models.CloudZone
        fields = (
            'id',
            'title',
            'provider_type',
            'region',
        )


class SecurityGroupSerializer(SuperuserFieldsMixin,
                              serializers.HyperlinkedModelSerializer):
    ##
    # Read-only fields.
    ##
    group_id = serializers.ReadOnlyField()
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    # Field for showing the number of active hosts using this security
    # group. It is pulled automatically from the model instance method.
    active_hosts = serializers.ReadOnlyField(source='get_active_hosts')

    # Rules are defined in two places depending on the object we're dealing
    # with. If it's a QuerySet the rules are pulled in one query to the
    # cloud provider using the SecurityGroupQuerySet::with_rules method.
    # For single, detail objects we use the rules instance method on the
    # SecurityGroup object
    provider_id = serializers.ReadOnlyField(source='cloud_provider.id')

    rules_url = serializers.HyperlinkedIdentityField(
        view_name='securitygroup-rules')

    class Meta:
        model = models.SecurityGroup
        fields = (
            'id',
            'url',
            'name',
            'description',
            'rules_url',
            'group_id',
            'cloud_provider',
            'provider_id',
            'owner',
            'is_default',
            'is_managed',
            'active_hosts',
            'rules',
        )
        superuser_fields = ('owner', 'is_default', 'is_managed')


class SecurityGroupRuleSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=15)
    protocol = serializers.CharField(max_length=4)
    from_port = serializers.IntegerField()
    to_port = serializers.IntegerField()
    rule = serializers.CharField(max_length=255)
