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

from stackdio.core.fields import HyperlinkedParentField
from stackdio.core.mixins import SuperuserFieldsMixin
from stackdio.core.utils import recursive_update
from stackdio.api.formulas.serializers import FormulaComponentSerializer
from . import models
from .utils import get_provider_driver_class

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


class CloudProviderSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.ReadOnlyField(source='get_type_name_display')

    # Links
    instance_sizes = serializers.HyperlinkedIdentityField(view_name='cloudinstancesize-list',
                                                          lookup_field='name')
    regions = serializers.HyperlinkedIdentityField(view_name='cloudregion-list',
                                                   lookup_field='name')
    zones = serializers.HyperlinkedIdentityField(view_name='cloudzone-list',
                                                 lookup_field='name')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-object-user-permissions-list', lookup_field='name')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-object-group-permissions-list', lookup_field='name')

    class Meta:
        model = models.CloudProvider
        lookup_field = 'name'
        fields = (
            'url',
            'title',
            'name',
            'instance_sizes',
            'regions',
            'zones',
            'user_permissions',
            'group_permissions',
        )


class CloudAccountSerializer(serializers.HyperlinkedModelSerializer):
    # Foreign Key Relations
    provider = serializers.SlugRelatedField(slug_field='name',
                                            queryset=models.CloudProvider.objects.all())
    region = serializers.SlugRelatedField(slug_field='title',
                                          queryset=models.CloudRegion.objects.all())

    # Hyperlinks
    security_groups = serializers.HyperlinkedIdentityField(
        view_name='cloudaccount-securitygroup-list')
    vpc_subnets = serializers.HyperlinkedIdentityField(
        view_name='cloudaccount-vpcsubnet-list')
    global_orchestration_components = serializers.HyperlinkedIdentityField(
        view_name='cloudaccount-global-orchestration-list')
    global_orchestration_properties = serializers.HyperlinkedIdentityField(
        view_name='cloudaccount-global-orchestration-properties')
    formula_versions = serializers.HyperlinkedIdentityField(
        view_name='cloudaccount-formula-versions')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='cloudaccount-object-user-permissions-list')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='cloudaccount-object-group-permissions-list')

    class Meta:
        model = models.CloudAccount
        fields = (
            'url',
            'title',
            'slug',
            'description',
            'provider',
            'region',
            'account_id',
            'vpc_id',
            'security_groups',
            'vpc_subnets',
            'user_permissions',
            'group_permissions',
            'global_orchestration_components',
            'global_orchestration_properties',
            'formula_versions',
        )

    def validate(self, attrs):
        # validate account specific request data
        request = self.context['request']

        # patch requests only accept a few things for modification
        if request.method == 'PATCH':
            fields_available = ('title',
                                'description')
            # TODO removed default AZ for now, might add in region later

            errors = {}
            for k in self.initial_data:
                if k not in fields_available:
                    errors.setdefault(k, []).append(
                        'Field may not be modified.')
            if errors:
                logger.debug(errors)
                raise serializers.ValidationError(errors)

        elif request.method == 'POST':
            provider = attrs['provider']

            provider_class = get_provider_driver_class(provider)

            provider_driver = provider_class()

            errors = provider_driver.validate_provider_data(attrs, self.initial_data)

            if errors:
                logger.error('Cloud account validation errors: '
                             '{0}'.format(errors))
                raise serializers.ValidationError(errors)

        return attrs


class VPCSubnetSerializer(serializers.Serializer):
    vpc_id = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    availability_zone = serializers.ReadOnlyField()
    cidr_block = serializers.ReadOnlyField()
    tags = serializers.ReadOnlyField()


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

    def update(self, account, validated_data):
        if self.partial:
            # This is a PATCH, so properly merge in the old data
            old_properties = account.global_orchestration_properties
            account.global_orchestration_properties = recursive_update(old_properties,
                                                                       validated_data)
        else:
            # This is a PUT, so just add the data directly
            account.global_orchestration_properties = validated_data

        # Be sure to persist the data
        account.save()
        return account


class CloudProfileSerializer(SuperuserFieldsMixin,
                             serializers.HyperlinkedModelSerializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudAccount.objects.all()
    )
    default_instance_size = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudInstanceSize.objects.all()
    )

    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='cloudprofile-object-user-permissions-list')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='cloudprofile-object-group-permissions-list')

    class Meta:
        model = models.CloudProfile
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'account',
            'image_id',
            'default_instance_size',
            'ssh_user',
            'user_permissions',
            'group_permissions',
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
            account_id = request.DATA.get('account')
            if not account_id:
                raise serializers.ValidationError({
                    'account': 'Required field.'
                })

            account = models.CloudAccount.objects.get(pk=account_id)
            driver = account.get_driver()

            valid, exc_msg = driver.validate_image_id(image_id)
            if not valid:
                raise serializers.ValidationError({
                    'image_id': ['Image ID does not exist on the given cloud '
                                 'account. Check that it exists and you have '
                                 'access to it.'],
                    'image_id_exception': [exc_msg]
                })

        return attrs


class SnapshotSerializer(serializers.HyperlinkedModelSerializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudAccount.objects.all()
    )

    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='snapshot-object-user-permissions-list')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='snapshot-object-group-permissions-list')

    class Meta:
        model = models.Snapshot
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'account',
            'snapshot_id',
            'size_in_gb',
            'filesystem_type',
            'user_permissions',
            'group_permissions',
        )

    def validate(self, attrs):
        request = self.context['request']

        # validate that the snapshot exists by looking it up in the cloud
        # account
        account_id = request.DATA.get('account')
        driver = models.CloudAccount.objects.get(pk=account_id).get_driver()

        result, error = driver.has_snapshot(request.DATA['snapshot_id'])
        if not result:
            raise serializers.ValidationError({'errors': [error]})
        return attrs


class CloudInstanceSizeSerializer(serializers.HyperlinkedModelSerializer):
    url = HyperlinkedParentField(
        view_name='cloudinstancesize-detail',
        parent_relation_field='provider',
        parent_lookup_field='name',
        lookup_field='instance_id',
    )

    provider = serializers.CharField(source='provider.name')

    class Meta:
        model = models.CloudInstanceSize
        fields = (
            'url',
            'title',
            'slug',
            'description',
            'provider',
            'instance_id',
        )


class CloudRegionSerializer(serializers.HyperlinkedModelSerializer):
    url = HyperlinkedParentField(
        view_name='cloudregion-detail',
        parent_relation_field='provider',
        parent_lookup_field='name',
        lookup_field='title',
    )

    provider = serializers.CharField(source='provider.name')
    zones = serializers.StringRelatedField(many=True, read_only=True)
    zones_url = HyperlinkedParentField(
        view_name='cloudregion-zones',
        parent_lookup_field='name',
        parent_relation_field='provider',
        lookup_field='title',
    )

    class Meta:
        model = models.CloudRegion
        fields = (
            'url',
            'title',
            'provider',
            'zones',
            'zones_url',
        )


class CloudZoneSerializer(serializers.HyperlinkedModelSerializer):
    url = HyperlinkedParentField(
        view_name='cloudzone-detail',
        parent_relation_field='region.provider',
        parent_lookup_field='name',
        lookup_field='title',
    )

    region = serializers.CharField(source='region.title')

    provider = serializers.CharField(source='region.provider.name')

    class Meta:
        model = models.CloudZone
        fields = (
            'url',
            'title',
            'region',
            'provider',
        )


class SecurityGroupSerializer(SuperuserFieldsMixin,
                              serializers.HyperlinkedModelSerializer):
    ##
    # Read-only fields.
    ##
    group_id = serializers.ReadOnlyField()

    # Field for showing the number of active hosts using this security
    # group. It is pulled automatically from the model instance method.
    active_hosts = serializers.ReadOnlyField(source='get_active_hosts')

    # Rules are defined in two places depending on the object we're dealing
    # with. If it's a QuerySet the rules are pulled in one query to the
    # cloud account using the SecurityGroupQuerySet::with_rules method.
    # For single, detail objects we use the rules instance method on the
    # SecurityGroup object
    account_id = serializers.ReadOnlyField(source='account.id')

    rules_url = serializers.HyperlinkedIdentityField(view_name='securitygroup-rules')

    class Meta:
        model = models.SecurityGroup
        fields = (
            'id',
            'url',
            'name',
            'description',
            'rules_url',
            'group_id',
            'account',
            'account_id',
            'is_default',
            'is_managed',
            'active_hosts',
            'rules',
        )
        superuser_fields = ('is_default', 'is_managed')


class SecurityGroupRuleSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=15)
    protocol = serializers.CharField(max_length=4)
    from_port = serializers.IntegerField()
    to_port = serializers.IntegerField()
    rule = serializers.CharField(max_length=255)
