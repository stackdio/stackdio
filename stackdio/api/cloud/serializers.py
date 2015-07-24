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

import yaml
from rest_framework import permissions
from rest_framework import serializers

from stackdio.core.fields import HyperlinkedParentField
from stackdio.core.mixins import CreateOnlyFieldsMixin
from stackdio.core.utils import recursive_update
from stackdio.api.cloud.providers.base import (
    GroupExistsException,
    GroupNotFoundException,
    RuleExistsException,
    RuleNotFoundException,
    SecurityGroupRule,
)
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


class CloudAccountSerializer(CreateOnlyFieldsMixin, serializers.HyperlinkedModelSerializer):
    # Foreign Key Relations
    provider = serializers.SlugRelatedField(slug_field='name',
                                            queryset=models.CloudProvider.objects.all())
    region = serializers.SlugRelatedField(slug_field='title',
                                          queryset=models.CloudRegion.objects.all())

    # Hyperlinks
    security_groups = serializers.HyperlinkedIdentityField(
        view_name='cloudaccount-securitygroup-list')
    all_security_groups = serializers.HyperlinkedIdentityField(
        view_name='cloudaccount-fullsecuritygroup-list')
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
            'all_security_groups',
            'vpc_subnets',
            'user_permissions',
            'group_permissions',
            'global_orchestration_components',
            'global_orchestration_properties',
            'formula_versions',
        )

        # Don't allow these to be changed after account creation
        create_only_fields = (
            'provider',
            'region',
            'account_id',
            'vpc_id',
        )

    def validate(self, attrs):
        if self.instance is not None:
            # This is an update request, so there's no further validation required
            return attrs
        else:
            # this is a create request, so we need to do more validation
            provider = attrs['provider']
            provider_class = get_provider_driver_class(provider)
            provider_driver = provider_class()

            # Farm provider-specific validation out to the provider driver
            return provider_driver.validate_provider_data(attrs, self.initial_data)

    def create(self, validated_data):
        logger.debug(validated_data)

        account = super(CloudAccountSerializer, self).create(validated_data)

        driver = account.get_driver()

        # Leverage the driver to generate its required data that
        # will be serialized down to yaml and stored in both the database
        # and the salt cloud providers file
        provider_data = driver.get_provider_data(validated_data)

        # Generate the yaml and store in the database
        yaml_data = {
            account.slug: provider_data
        }
        account.yaml = yaml.safe_dump(yaml_data, default_flow_style=False)
        account.save()

        # Update the salt cloud providers file
        account.update_config()

        return account


class VPCSubnetSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    vpc_id = serializers.CharField()
    id = serializers.CharField()
    availability_zone = serializers.CharField()
    cidr_block = serializers.CharField()
    tags = serializers.DictField(child=serializers.CharField())


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


class CloudProfileSerializer(CreateOnlyFieldsMixin, serializers.HyperlinkedModelSerializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudAccount.objects.all()
    )
    default_instance_size = serializers.SlugRelatedField(
        slug_field='instance_id',
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

        # Don't allow these to be changed after profile creation
        create_only_fields = (
            'account',
        )

    def validate(self, attrs):
        image_id = attrs['image_id']
        account = attrs['account']

        driver = account.get_driver()

        # Ensure that the image id is valid
        valid, exc_msg = driver.validate_image_id(image_id)
        if not valid:
            raise serializers.ValidationError({
                'image_id': ['Image ID does not exist on the given cloud '
                             'account. Check that it exists and you have '
                             'access to it.',
                             exc_msg],
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


class SecurityGroupSerializer(CreateOnlyFieldsMixin, serializers.HyperlinkedModelSerializer):
    # Field for showing the number of active hosts using this security
    # group. It is pulled automatically from the model instance method.
    active_hosts = serializers.ReadOnlyField(source='get_active_hosts')

    account = serializers.PrimaryKeyRelatedField(queryset=models.CloudAccount.objects.all())

    rules = serializers.HyperlinkedIdentityField(view_name='securitygroup-rules')

    default = serializers.BooleanField(source='is_default', required=False)
    managed = serializers.BooleanField(source='is_managed', read_only=True)

    default_description = 'Created by stackd.io'

    class Meta:
        model = models.SecurityGroup
        fields = (
            'id',
            'url',
            'group_id',
            'name',
            'description',
            'account',
            'default',
            'managed',
            'active_hosts',
            'rules',
        )

        extra_kwargs = {
            'name': {'required': False},
            'group_id': {'required': False},
            'description': {'required': False},
        }

        create_only_fields = (
            'group_id',
            'name',
            'account',
            'description',
        )

    def __init__(self, *args, **kwargs):
        super(SecurityGroupSerializer, self).__init__(*args, **kwargs)
        self.should_create_group = None

    def validate(self, attrs):
        if self.instance is None:
            # All of this validation only matters if we are creating a new group
            account = attrs['account']
            driver = account.get_driver()

            name = attrs.get('name')
            group_id = attrs.get('group_id')

            if not name and not group_id:
                err_msg = 'You must provide one of `name` or `group_id`'
                raise serializers.ValidationError({
                    'name': [err_msg],
                    'group_id': [err_msg],
                })

            # check if the group exists on the account
            if group_id:
                try:
                    account_group_list = driver.get_security_groups([group_id])

                    if len(account_group_list) != 1:
                        logger.info('The list of account groups doesn\'t have the right number of '
                                    'elements (If you\'re seeing this, something has gone '
                                    'horribly wrong): {0}'.format(account_group_list))
                        raise GroupNotFoundException()

                    account_group = account_group_list[0]
                    logger.debug('Security group with id "{0}" and name "{1}" already exists on '
                                 'the account.'.format(group_id, name))
                except GroupNotFoundException:
                    # doesn't exist on the account, we'll try to create it later
                    account_group = None
            else:
                account_group = None

            # Set all the appropriate data
            if account_group:
                # Already exists, just need to create in our database
                attrs['group_id'] = account_group.group_id
                attrs['description'] = account_group.description
                attrs['is_managed'] = False
                self.should_create_group = False
            else:
                # create a new group
                self.should_create_group = True
                attrs['is_managed'] = True

        return attrs

    def create(self, validated_data):
        account = validated_data['account']

        validated_data.setdefault('description', self.default_description)
        validated_data.setdefault('is_default', False)

        if self.should_create_group:
            # Only create the group on the provider if we deemed it necessary during validation
            name = validated_data['name']
            description = validated_data['description']
            driver = account.get_driver()

            # create the new provider group
            try:
                validated_data['group_id'] = driver.create_security_group(name, description)
            except GroupExistsException:
                raise serializers.ValidationError({
                    'name': ['A group with the name `{0}` already exists on this '
                             'account.'.format(name)],
                })

        # Create the database object
        group = super(SecurityGroupSerializer, self).create(validated_data)

        logger.debug('Writing cloud accounts file because new security '
                     'group was added with is_default flag set to True')
        account.update_config()

        return group

    def update(self, instance, validated_data):
        logger.debug(validated_data)

        group = super(SecurityGroupSerializer, self).update(instance, validated_data)

        account = validated_data['account']
        logger.debug('Writing cloud accounts file because new security '
                     'group was added with is_default flag set to True')
        account.update_config()

        return group


class CloudAccountSecurityGroupSerializer(SecurityGroupSerializer):
    account = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.SecurityGroup
        fields = (
            'id',
            'url',
            'group_id',
            'name',
            'description',
            'account',
            'default',
            'managed',
            'active_hosts',
            'rules',
        )

        extra_kwargs = {
            'group_id': {'required': False},
            'description': {'required': False},
        }

        create_only_fields = (
            'group_id',
            'name',
            'description',
        )


class SecurityGroupRuleSerializer(serializers.Serializer):
    available_actions = ('authorize', 'revoke')

    action = serializers.CharField(write_only=True)
    protocol = serializers.CharField(max_length=4)
    from_port = serializers.IntegerField(min_value=0, max_value=65535)
    to_port = serializers.IntegerField(min_value=0, max_value=65535)
    rule = serializers.CharField(max_length=255)

    def __init__(self, security_group=None, *args, **kwargs):
        self.security_group = security_group
        super(SecurityGroupRuleSerializer, self).__init__(*args, **kwargs)

    def validate(self, attrs):
        action = attrs['action']

        if action not in self.available_actions:
            raise serializers.ValidationError({
                'action': ['{0} is not a valid action.'.format(action)]
            })

        from_port = attrs['from_port']
        to_port = attrs['to_port']

        if from_port > to_port:
            err_msg = '`from_port` ({0}) must be less than `to_port` ({1})'.format(from_port,
                                                                                   to_port)
            raise serializers.ValidationError({
                'from_port': [err_msg],
                'to_port': [err_msg],
            })

        group = self.security_group
        account = group.account
        driver = account.get_driver()
        rule = attrs['rule']

        # Check the rule to determine the "type" of the rule. This
        # can be a CIDR or group rule. CIDR will look like an IP
        # address and anything else will be considered a group
        # rule, however, a group can contain the account id of
        # the group we're dealing with. If the group rule does
        # not contain a colon then we'll add the account's
        # account id
        if not driver.is_cidr_rule(rule) and ':' not in rule:
            rule = account.account_id + ':' + rule
            attrs['rule'] = rule
            logger.debug('Prefixing group rule with account id. '
                         'New rule: {0}'.format(rule))

        return attrs

    def save(self, **kwargs):
        group = self.security_group
        account = group.account
        driver = account.get_driver()

        action = self.validated_data['action']

        rule_actions = {
            'authorize': driver.authorize_security_group,
            'revoke': driver.revoke_security_group,
        }

        try:
            rule_actions[action](group.group_id, self.validated_data)
        except (RuleNotFoundException, RuleExistsException, GroupNotFoundException) as e:
            raise serializers.ValidationError({
                'rule': e.message
            })

        self.instance = SecurityGroupRule(
            self.validated_data['protocol'],
            self.validated_data['from_port'],
            self.validated_data['to_port'],
            self.validated_data['rule'],
        )

        return self.instance


class DirectCloudAccountSecurityGroupSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    name = serializers.CharField()
    description = serializers.CharField()
    group_id = serializers.CharField()
    vpc_id = serializers.CharField()
    rules = SecurityGroupRuleSerializer(many=True)
    rules_egress = SecurityGroupRuleSerializer(many=True)
