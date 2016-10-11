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

# Just disable this for the file
# pylint: disable=abstract-method

import logging

import yaml
from rest_framework import serializers

from stackdio.core.fields import HyperlinkedParentField
from stackdio.core.mixins import CreateOnlyFieldsMixin
from stackdio.core.serializers import (
    StackdioHyperlinkedModelSerializer,
    StackdioParentHyperlinkedModelSerializer,
)
from stackdio.core.utils import recursive_update, recursively_sort_dict
from stackdio.core.validators import PropertiesValidator
from stackdio.api.blueprints.models import PROTOCOL_CHOICES
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


class CloudProviderSerializer(StackdioHyperlinkedModelSerializer):
    title = serializers.ReadOnlyField(source='get_type_name_display')

    # Links
    required_fields = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudprovider-required',
        lookup_field='name')
    instance_sizes = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudinstancesize-list',
        lookup_field='name', lookup_url_kwarg='parent_name')
    regions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudregion-list',
        lookup_field='name', lookup_url_kwarg='parent_name')
    zones = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudzone-list',
        lookup_field='name', lookup_url_kwarg='parent_name')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudprovider-object-user-permissions-list',
        lookup_field='name', lookup_url_kwarg='parent_name')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudprovider-object-group-permissions-list',
        lookup_field='name', lookup_url_kwarg='parent_name')

    class Meta:
        model = models.CloudProvider
        lookup_field = 'name'
        fields = (
            'url',
            'title',
            'name',
            'required_fields',
            'instance_sizes',
            'regions',
            'zones',
            'user_permissions',
            'group_permissions',
        )


class CloudAccountSerializer(CreateOnlyFieldsMixin, StackdioHyperlinkedModelSerializer):
    # Foreign Key Relations
    provider = serializers.SlugRelatedField(slug_field='name',
                                            queryset=models.CloudProvider.objects.all())
    region = serializers.SlugRelatedField(slug_field='title',
                                          queryset=models.CloudRegion.objects.all())

    # Hyperlinks
    images = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudaccount-cloudimage-list',
        lookup_url_kwarg='parent_pk')
    security_groups = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudaccount-securitygroup-list',
        lookup_url_kwarg='parent_pk')
    all_security_groups = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudaccount-fullsecuritygroup-list',
        lookup_url_kwarg='parent_pk')
    vpc_subnets = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudaccount-vpcsubnet-list',
        lookup_url_kwarg='parent_pk')
    global_orchestration_components = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudaccount-global-orchestration-list',
        lookup_url_kwarg='parent_pk')
    global_orchestration_properties = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudaccount-global-orchestration-properties')
    formula_versions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudaccount-formula-versions',
        lookup_url_kwarg='parent_pk')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudaccount-object-user-permissions-list',
        lookup_url_kwarg='parent_pk')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudaccount-object-group-permissions-list',
        lookup_url_kwarg='parent_pk')

    class Meta:
        model = models.CloudAccount
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'provider',
            'region',
            'vpc_id',
            'create_security_groups',
            'images',
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
            'vpc_id',
        )

        extra_kwargs = {
            'url': {'view_name': 'api:cloud:cloudaccount-detail'},
        }

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
        provider_data = driver.get_provider_data(validated_data, self.initial_data)

        # Generate the yaml and store in the database
        yaml_data = {
            account.slug: provider_data
        }
        account.yaml = yaml.safe_dump(yaml_data, default_flow_style=False)
        account.save()

        # Update the salt cloud providers file
        account.update_config()

        return account


class VPCSubnetSerializer(serializers.Serializer):
    vpc_id = serializers.CharField()
    id = serializers.CharField()
    availability_zone = serializers.CharField()
    cidr_block = serializers.CharField()
    tags = serializers.DictField(child=serializers.CharField())


class GlobalOrchestrationPropertiesSerializer(serializers.Serializer):
    def to_representation(self, obj):
        ret = {}
        if obj is not None:
            ret = obj.global_orchestration_properties
        return recursively_sort_dict(ret)

    def to_internal_value(self, data):
        return data

    def validate(self, attrs):
        PropertiesValidator().validate(attrs)
        return attrs

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


class GlobalOrchestrationComponentSerializer(FormulaComponentSerializer):

    class Meta(FormulaComponentSerializer.Meta):
        app_label = 'cloud'
        model_name = 'cloudaccount-global-orchestration'

        fields = (
            'url',
            'formula',
            'title',
            'description',
            'sls_path',
            'order',
        )


class CloudImageSerializer(CreateOnlyFieldsMixin, StackdioHyperlinkedModelSerializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudAccount.objects.all()
    )
    default_instance_size = serializers.SlugRelatedField(
        slug_field='instance_id',
        queryset=models.CloudInstanceSize.objects.all()
    )

    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudimage-object-user-permissions-list',
        lookup_url_kwarg='parent_pk')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:cloudimage-object-group-permissions-list',
        lookup_url_kwarg='parent_pk')

    class Meta:
        model = models.CloudImage
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

        # Don't allow these to be changed after image creation
        create_only_fields = (
            'account',
        )

    def validate(self, attrs):
        image_id = attrs.get('image_id')
        # Don't validate when it's a PATCH request and image_id doesn't exist
        if not self.partial or image_id is not None:
            account = attrs.get('account') or self.instance.account

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


class SnapshotSerializer(CreateOnlyFieldsMixin, StackdioHyperlinkedModelSerializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=models.CloudAccount.objects.all()
    )

    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:snapshot-object-user-permissions-list',
        lookup_url_kwarg='parent_pk')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:cloud:snapshot-object-group-permissions-list',
        lookup_url_kwarg='parent_pk')

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
            'filesystem_type',
            'user_permissions',
            'group_permissions',
        )

        create_only_fields = (
            'account',
        )

    def validate(self, attrs):
        if 'snapshot_id' in attrs:
            account = attrs.get('account') or self.instance.account

            # validate that the snapshot exists by looking it up in the cloud
            # account
            driver = account.get_driver()

            result, error = driver.has_snapshot(attrs['snapshot_id'])
            if not result:
                raise serializers.ValidationError({'snapshot_id': [error]})
        return attrs


class CloudInstanceSizeSerializer(StackdioParentHyperlinkedModelSerializer):
    provider = serializers.CharField(source='provider.name')

    class Meta:
        model = models.CloudInstanceSize
        parent_attr = 'provider'
        parent_lookup_field = 'name'
        lookup_field = 'instance_id'
        fields = (
            'url',
            'title',
            'slug',
            'description',
            'provider',
            'instance_id',
        )


class CloudRegionSerializer(StackdioParentHyperlinkedModelSerializer):
    provider = serializers.CharField(source='provider.name')
    zones = serializers.StringRelatedField(many=True, read_only=True)

    zones_url = HyperlinkedParentField(
        view_name='api:cloud:cloudregion-zones',
        parent_attr='provider',
        parent_lookup_field='name',
        lookup_field='title',
    )

    class Meta:
        model = models.CloudRegion
        parent_attr = 'provider'
        parent_lookup_field = 'name'
        lookup_field = 'title'
        fields = (
            'url',
            'title',
            'provider',
            'zones',
            'zones_url',
        )


class CloudZoneSerializer(StackdioParentHyperlinkedModelSerializer):
    region = serializers.CharField(source='region.title')

    provider = serializers.CharField(source='region.provider.name')

    class Meta:
        model = models.CloudZone
        parent_attr = 'provider'
        parent_lookup_field = 'name'
        lookup_field = 'title'
        fields = (
            'url',
            'title',
            'region',
            'provider',
        )


class SecurityGroupSerializer(CreateOnlyFieldsMixin, StackdioHyperlinkedModelSerializer):
    # Field for showing the number of active hosts using this security
    # group. It is pulled automatically from the model instance method.
    active_hosts = serializers.ReadOnlyField(source='get_active_hosts')

    account = serializers.PrimaryKeyRelatedField(queryset=models.CloudAccount.objects.all())

    name = serializers.CharField(default='')

    rules = serializers.HyperlinkedIdentityField(view_name='api:cloud:securitygroup-rules',
                                                 lookup_url_kwarg='parent_pk')

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
                err_msg = 'You must provide one of either `name` or `group_id`'
                raise serializers.ValidationError({
                    'name': [err_msg],
                    'group_id': [err_msg],
                })

            if name and group_id:
                err_msg = 'You may only provide one of `name` or `group_id`'
                raise serializers.ValidationError({
                    'name': [err_msg],
                    'group_id': [err_msg],
                })

            if group_id:
                # check if the group exists on the account
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
                except GroupNotFoundException as e:
                    if e.message:
                        err_msg = e.message
                    else:
                        err_msg = ('The group_id `{0}` doesn\'t exist on the provider '
                                   'account.'.format(group_id))

                    raise serializers.ValidationError({
                        'group_id': [err_msg],
                    })

                # Set appropriate properties we got back from the provider
                attrs['group_id'] = account_group.group_id
                attrs['description'] = account_group.description
                attrs['name'] = account_group.name
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

    def to_internal_value(self, data):
        ret = super(CloudAccountSecurityGroupSerializer, self).to_internal_value(data)
        # Add in the account so the UniqueTogetherValidator doesn't get angry
        ret['account'] = self.context['account']
        return ret


class SecurityGroupRuleSerializer(serializers.Serializer):
    available_actions = ('authorize', 'revoke')

    action = serializers.CharField(write_only=True)
    protocol = serializers.ChoiceField(PROTOCOL_CHOICES)
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


class DirectCloudAccountSecurityGroupSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    group_id = serializers.CharField()
    vpc_id = serializers.CharField()
    rules = SecurityGroupRuleSerializer(many=True)
    rules_egress = SecurityGroupRuleSerializer(many=True)
