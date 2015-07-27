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
import os

import salt.cloud
from django.conf import settings
from rest_framework import serializers

from stackdio.core.mixins import CreateOnlyFieldsMixin
from stackdio.core.utils import recursive_update
from stackdio.core.validators import PropertiesValidator
from stackdio.api.blueprints.models import Blueprint, BlueprintHostDefinition
from stackdio.api.blueprints.serializers import (
    BlueprintHostFormulaComponentSerializer,
    BlueprintHostDefinitionSerializer
)
from stackdio.api.cloud.models import SecurityGroup
from stackdio.api.cloud.serializers import SecurityGroupSerializer
from . import models, workflows

logger = logging.getLogger(__name__)


class StackPropertiesSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if obj is not None:
            # Make it work two different ways.. ooooh
            if isinstance(obj, models.Stack):
                return obj.properties
            else:
                return obj
        return {}

    def to_internal_value(self, data):
        return data

    def validate(self, attrs):
        PropertiesValidator().validate(attrs)
        return attrs

    def update(self, stack, validated_data):
        if self.partial:
            # This is a PATCH, so properly merge in the old data
            old_properties = stack.properties
            stack.properties = recursive_update(old_properties, validated_data)
        else:
            # This is a PUT, so just add the data directly
            stack.properties = validated_data

        # Regenerate the pillar file with the new properties
        stack.generate_pillar_file()

        # Be sure to save the instance
        stack.save()

        return stack


class HostSerializer(serializers.HyperlinkedModelSerializer):
    # Read only fields
    subnet_id = serializers.ReadOnlyField()
    availability_zone = serializers.PrimaryKeyRelatedField(read_only=True)
    formula_components = BlueprintHostFormulaComponentSerializer(many=True, read_only=True)

    class Meta:
        model = models.Host
        fields = (
            'id',
            'url',
            'hostname',
            'provider_dns',
            'provider_private_dns',
            'provider_private_ip',
            'fqdn',
            'state',
            'state_reason',
            'status',
            'status_detail',
            'availability_zone',
            'subnet_id',
            'created',
            'sir_id',
            'sir_price',
            'formula_components',
        )


class StackHistorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.StackHistory
        fields = (
            'event',
            'status',
            'status_detail',
            'level',
            'created'
        )


class StackCreateUserDefault(object):
    """
    Used to set the default value of create_users to be that of the blueprint
    """
    def __init__(self):
        super(StackCreateUserDefault, self).__init__()
        self._context = None

    def set_context(self, field):
        self._context = field.parent

    def __call__(self):
        blueprint = Blueprint.objects.get(pk=self._context.initial_data['blueprint'])
        return blueprint.create_users


class StackSerializer(CreateOnlyFieldsMixin, serializers.HyperlinkedModelSerializer):
    # Read only fields
    host_count = serializers.ReadOnlyField(source='hosts.count')
    volume_count = serializers.ReadOnlyField(source='volumes.count')

    # Identity links
    hosts = serializers.HyperlinkedIdentityField(
        view_name='stack-hosts')
    fqdns = serializers.HyperlinkedIdentityField(
        view_name='stack-fqdns')
    action = serializers.HyperlinkedIdentityField(
        view_name='stack-action')
    actions = serializers.HyperlinkedIdentityField(
        view_name='stackaction-list')
    logs = serializers.HyperlinkedIdentityField(
        view_name='stack-logs')
    orchestration_errors = serializers.HyperlinkedIdentityField(
        view_name='stack-orchestration-errors')
    provisioning_errors = serializers.HyperlinkedIdentityField(
        view_name='stack-provisioning-errors')
    volumes = serializers.HyperlinkedIdentityField(
        view_name='stack-volumes')
    properties = serializers.HyperlinkedIdentityField(
        view_name='stack-properties')
    history = serializers.HyperlinkedIdentityField(
        view_name='stack-history')
    security_groups = serializers.HyperlinkedIdentityField(
        view_name='stack-security-groups')
    formula_versions = serializers.HyperlinkedIdentityField(
        view_name='stack-formula-versions')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='stack-object-user-permissions-list')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='stack-object-group-permissions-list')

    # Relation Links
    blueprint = serializers.PrimaryKeyRelatedField(queryset=Blueprint.objects.all())

    class Meta:
        model = models.Stack
        fields = (
            'id',
            'url',
            'blueprint',
            'title',
            'description',
            'status',
            'namespace',
            'create_users',
            'host_count',
            'volume_count',
            'created',
            'user_permissions',
            'group_permissions',
            'fqdns',
            'hosts',
            'volumes',
            'properties',
            'history',
            'action',
            'actions',
            'security_groups',
            'formula_versions',
            'logs',
            'orchestration_errors',
            'provisioning_errors',
        )

        create_only_fields = (
            'blueprint',
            'namespace',
        )

        read_only_fields = (
            'status',
        )

        extra_kwargs = {
            'create_users': {'default': serializers.CreateOnlyDefault(StackCreateUserDefault())}
        }

    def validate(self, attrs):
        errors = {}

        # make sure the user has a public key or they won't be able to SSH
        # later
        request = self.context['request']
        if 'create_users' in attrs:
            create_users = attrs['create_users']
        else:
            create_users = self.instance.create_user
        if create_users and not request.user.settings.public_key:
            errors.setdefault('public_key', []).append(
                'You have not added a public key to your user '
                'profile and will not be able to SSH in to any '
                'machines. Please update your user profile '
                'before continuing.'
            )

        # Check to see if the launching user has permission to launch from the blueprint
        user = self.context['request'].user
        blueprint = self.instance.blueprint if self.instance else attrs['blueprint']

        if not user.has_perm('blueprints.view_blueprint', blueprint):
            err_msg = 'You do not have permission to launch a stack from this blueprint.'
            errors.setdefault('blueprint', []).append(err_msg)

        # check for hostname collisions if namespace is provided
        namespace = attrs.get('namespace')

        if namespace:
            # This all has to be here vs. in its own validator b/c it needs the blueprint

            # This is all only necessary if a namespace was provided
            #  (It may not be provided on a PATCH request)
            host_definitions = blueprint.host_definitions.all()
            hostnames = models.get_hostnames_from_hostdefs(
                host_definitions,
                namespace=namespace
            )

            # query for existing host names
            # Leave this in so that we catch errors faster if they are local,
            #    Only hit up salt cloud if there are no duplicates locally
            hosts = models.Host.objects.filter(hostname__in=hostnames)
            if hosts.count() > 0:
                errors.setdefault('duplicate_hostnames', []).extend([h.hostname for h in hosts])

            salt_cloud = salt.cloud.CloudClient(os.path.join(
                settings.STACKDIO_CONFIG.salt_config_root,
                'cloud'
            ))
            query = salt_cloud.query()

            # Since a blueprint can have multiple accounts
            accounts = set()
            for bhd in host_definitions:
                accounts.add(bhd.cloud_profile.account)

            # Check to find duplicates
            dups = []
            for account in accounts:
                provider = account.provider.name
                for instance, details in query.get(account.slug, {}).get(provider, {}).items():
                    if instance in hostnames:
                        if details['state'] not in ('shutting-down', 'terminated'):
                            dups.append(instance)

            if dups:
                errors.setdefault('duplicate_hostnames', []).extend(dups)

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class FullStackSerializer(StackSerializer):
    properties = StackPropertiesSerializer(required=False)

    def create(self, validated_data):
        # Create the stack
        stack = self.Meta.model.objects.create(**validated_data)

        # The stack was created, now let's launch it
        # We'll pass the initial_data in as the opts
        workflow = workflows.LaunchWorkflow(stack, opts=self.initial_data)
        workflow.execute()

        return stack


class StackBlueprintHostDefinitionSerializer(BlueprintHostDefinitionSerializer):
    class Meta:
        model = BlueprintHostDefinition
        fields = (
            'title',
            'description',
        )


class StackSecurityGroupSerializer(SecurityGroupSerializer):
    blueprint_host_definition = StackBlueprintHostDefinitionSerializer()

    class Meta:
        model = SecurityGroup
        fields = (
            'id',
            'url',
            'name',
            'description',
            'rules_url',
            'group_id',
            'blueprint_host_definition',
            'account',
            'account_id',
            'is_default',
            'is_managed',
            'active_hosts',
            'rules',
        )


class StackActionSerializer(serializers.HyperlinkedModelSerializer):
    zip_url = serializers.HyperlinkedIdentityField(view_name='stackaction-zip')

    class Meta:
        model = models.StackAction
        fields = (
            'id',
            'url',
            'zip_url',
            'submit_time',
            'start_time',
            'finish_time',
            'status',
            'type',
            'host_target',
            'command',
            'std_out',
            'std_err',
        )
