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


import logging
import os
import string

import six
import salt.cloud
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework import serializers
from rest_framework.compat import OrderedDict
from rest_framework.exceptions import PermissionDenied

from stackdio.core.mixins import CreateOnlyFieldsMixin
from stackdio.core.serializers import (
    StackdioHyperlinkedModelSerializer,
    StackdioLabelSerializer,
    StackdioLiteralLabelsSerializer,
)
from stackdio.core.utils import recursive_update, recursively_sort_dict
from stackdio.core.validators import PropertiesValidator, validate_hostname
from stackdio.api.blueprints.models import Blueprint, BlueprintHostDefinition
from stackdio.api.blueprints.serializers import BlueprintHostDefinitionSerializer
from stackdio.api.cloud.models import SecurityGroup
from stackdio.api.cloud.serializers import SecurityGroupSerializer
from stackdio.api.formulas.serializers import FormulaComponentSerializer, FormulaVersionSerializer
from . import models, tasks, utils, workflows

logger = logging.getLogger(__name__)


class StackPropertiesSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    def to_representation(self, obj):
        ret = {}
        if obj is not None:
            # Make it work two different ways.. ooooh
            if isinstance(obj, models.Stack):
                ret = obj.properties
            else:
                ret = obj
        return recursively_sort_dict(ret)

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

        # Be sure to save the instance
        stack.save()

        return stack


class HostSerializer(StackdioHyperlinkedModelSerializer):
    # Read only fields
    subnet_id = serializers.ReadOnlyField()
    availability_zone = serializers.PrimaryKeyRelatedField(read_only=True)
    blueprint_host_definition = serializers.ReadOnlyField(source='blueprint_host_definition.title')
    formula_components = FormulaComponentSerializer(many=True, read_only=True)

    # Fields for adding / removing hosts
    available_actions = ('add', 'remove')

    action = serializers.ChoiceField(available_actions, write_only=True)
    host_definition = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=BlueprintHostDefinition.objects.all()
    )
    count = serializers.IntegerField(write_only=True, min_value=1)
    backfill = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = models.Host
        fields = (
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
            'blueprint_host_definition',
            'formula_components',
            'action',
            'host_definition',
            'count',
            'backfill',
        )

        read_only_fields = (
            'hostname',
            'provider_dns',
            'provider_private_dns',
            'provider_private_ip',
            'fqdn',
            'state',
            'state_reason',
            'status',
            'status_detail',
            'sir_id',
            'sir_price',
        )

    def __init__(self, *args, **kwargs):
        super(HostSerializer, self).__init__(*args, **kwargs)
        self.create_object = False

    def get_fields(self):
        """
        Override to insert the provider_metadata field if requested
        """
        fields = super(HostSerializer, self).get_fields()

        request = self.context['request']
        provider_metadata = request.query_params.get('provider_metadata', False)
        true_values = ('true', 'True', 'yes', 'Yes', '1', '')

        if provider_metadata in true_values:
            fields['provider_metadata'] = serializers.DictField(read_only=True)

        return fields

    def to_representation(self, instance):
        if self.create_object:
            serializer = HostSerializer(context=self.context, many=True)
            return OrderedDict((
                ('count', len(instance)),
                ('results', serializer.to_representation(instance)),
            ))
        else:
            return super(HostSerializer, self).to_representation(instance)

    def validate(self, attrs):
        stack = self.context['stack']
        blueprint = stack.blueprint

        action = attrs['action']
        count = attrs['count']
        host_definition = attrs['host_definition']

        current_count = stack.hosts.filter(blueprint_host_definition=host_definition).count()

        errors = {}

        # Make sure we aren't removing too many hosts
        if action == 'remove':
            if count > current_count:
                err_msg = 'You may not remove more hosts than already exist.'
                errors.setdefault('count', []).append(err_msg)

        # Make sure the stack is in a valid state
        if stack.status != models.Stack.FINISHED:
            err_msg = 'You may not add hosts to the stack in its current state: {0}'
            raise serializers.ValidationError({
                'stack': [err_msg.format(stack.status)]
            })

        # Make sure that the host definition belongs to the proper blueprint
        if host_definition not in blueprint.host_definitions.all():
            err_msg = 'The host definition you provided isn\'t related to this stack'
            raise serializers.ValidationError({
                'host_definition': [err_msg]
            })

        formatter = string.Formatter()
        template_vars = [x[1] for x in formatter.parse(host_definition.hostname_template) if x[1]]

        # Make sure the hostname_template has an index if there will be more than 1 host
        if (count + current_count) > 1 and 'index' not in template_vars:
            err_msg = ('The provided host_definition has a hostname_template without an `index` '
                       'key in it.  This is required so as not to introduce duplicate hostnames.')
            errors.setdefault('host_definition', []).append(err_msg)

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def do_add(self, stack, validated_data):
        hosts = stack.create_hosts(**validated_data)

        if hosts:
            host_ids = [h.id for h in hosts]

            # Launch celery tasks to create the hosts
            workflow = workflows.LaunchWorkflow(stack, host_ids=host_ids, opts=self.initial_data)
            workflow.execute()

        return hosts

    def do_remove(self, stack, validated_data):
        count = validated_data['count']
        hostdef = validated_data['host_definition']

        # Even though this looks like it will be a list, it's actually a QuerySet already
        hosts = stack.hosts.filter(blueprint_host_definition=hostdef).order_by('-index')[:count]

        logger.debug('Hosts to remove: {0}'.format(hosts))
        host_ids = [h.id for h in hosts]
        if host_ids:
            models.Host.objects.filter(id__in=host_ids).update(
                state=models.Host.DELETING,
                state_reason='User initiated delete.'
            )

            # Start the celery task chain to kill the hosts
            workflow = workflows.DestroyHostsWorkflow(stack, host_ids, opts=self.initial_data)
            workflow.execute()

        return hosts

    def create(self, validated_data):
        self.create_object = True
        stack = self.context['stack']
        action = validated_data.pop('action')

        action_map = {
            'add': self.do_add,
            'remove': self.do_remove,
        }

        return action_map[action](stack, validated_data)


class StackHistorySerializer(StackdioHyperlinkedModelSerializer):
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
        blueprint_id = self._context.initial_data.get('blueprint', None)
        if blueprint_id is None:
            return None
        if not isinstance(blueprint_id, six.integer_types):
            return None
        try:
            blueprint = Blueprint.objects.get(pk=blueprint_id)
            return blueprint.create_users
        except Blueprint.DoesNotExist:
            return None


class StackSerializer(CreateOnlyFieldsMixin, StackdioHyperlinkedModelSerializer):
    # Read only fields
    host_count = serializers.ReadOnlyField(source='hosts.count')
    volume_count = serializers.ReadOnlyField(source='volumes.count')
    label_list = StackdioLiteralLabelsSerializer(read_only=True, many=True, source='labels')

    # Identity links
    hosts = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-hosts')
    action = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-action')
    commands = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-command-list')
    logs = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-logs')
    volumes = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-volumes')
    labels = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-label-list')
    properties = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-properties')
    history = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-history')
    security_groups = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-security-groups')
    formula_versions = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-formula-versions')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-object-user-permissions-list')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:stacks:stack-object-group-permissions-list')

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
            'label_list',
            'user_permissions',
            'group_permissions',
            'hosts',
            'volumes',
            'labels',
            'properties',
            'history',
            'action',
            'commands',
            'security_groups',
            'formula_versions',
            'logs',
        )

        create_only_fields = (
            'blueprint',
            'namespace',
        )

        read_only_fields = (
            'status',
        )

        extra_kwargs = {
            'create_users': {'default': serializers.CreateOnlyDefault(StackCreateUserDefault())},
            'blueprint': {'view_name': 'api:blueprints:blueprint-detail'},
        }

    def validate(self, attrs):
        errors = {}

        # make sure the user has a public key or they won't be able to SSH
        # later
        request = self.context['request']
        if 'create_users' in attrs:
            create_users = attrs['create_users']
        else:
            create_users = self.instance.create_users
        if create_users and not request.user.settings.public_key:
            errors.setdefault('public_key', []).append(
                'You have not added a public key to your user '
                'profile and will not be able to SSH in to any '
                'machines. Please update your user profile '
                'before continuing.'
            )

        # Check to see if the launching user has permission to launch from the blueprint
        user = request.user
        blueprint = self.instance.blueprint if self.instance else attrs['blueprint']

        if not user.has_perm('blueprints.view_blueprint', blueprint):
            err_msg = 'You do not have permission to launch a stack from this blueprint.'
            errors.setdefault('blueprint', []).append(err_msg)

        # Check to make sure we don't have security group creation turned off without default
        # security groups
        accounts = set()
        for host_definition in blueprint.host_definitions.all():
            accounts.add(host_definition.cloud_image.account)

        for account in accounts:
            if (
                not account.create_security_groups and
                account.security_groups.filter(is_default=True).count() < 1
            ):
                errors.setdefault('security_groups', []).append(
                    'Account `{0}` has per-stack security groups disabled, but doesn\'t define any '
                    'default security groups.  You must define at least 1 default security group '
                    'on this account before launching stacks.'.format(account.title)
                )

        # check for hostname collisions if namespace is provided
        namespace = attrs.get('namespace')

        if namespace:
            # This all has to be here vs. in its own validator b/c it needs the blueprint
            hostname_errors = validate_hostname(namespace)
            if hostname_errors:
                errors.setdefault('namespace', []).extend(hostname_errors)

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
                err_msg = 'Duplicate hostnames: {0}'.format(', '.join([h.hostname for h in hosts]))
                errors.setdefault('namespace', []).append(err_msg)

            if errors:
                # Go ahead and raise an error here so that we don't check the provider if
                # we don't need to
                raise serializers.ValidationError(errors)

            salt_cloud = salt.cloud.CloudClient(os.path.join(
                settings.STACKDIO_CONFIG.salt_config_root,
                'cloud'
            ))
            query = salt_cloud.query()

            # Since a blueprint can have multiple accounts
            accounts = set()
            for bhd in host_definitions:
                accounts.add(bhd.cloud_image.account)

            # Check to find duplicates
            dups = []
            for account in accounts:
                provider = account.provider.name
                for instance, details in query.get(account.slug, {}).get(provider, {}).items():
                    if instance in hostnames:
                        if details['state'] not in ('shutting-down', 'terminated'):
                            dups.append(instance)

            if dups:
                err_msg = 'Duplicate hostnames: {0}'.format(', '.join(dups))
                errors.setdefault('namespace', []).append(err_msg)

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class FullStackSerializer(StackSerializer):
    properties = StackPropertiesSerializer(required=False)
    blueprint = serializers.PrimaryKeyRelatedField(queryset=Blueprint.objects.all())
    formula_versions = FormulaVersionSerializer(many=True, required=False)

    def to_representation(self, instance):
        """
        We want to return links instead of the full object
        """
        return StackSerializer(instance, context=self.context).to_representation(instance)

    def create(self, validated_data):
        formula_versions = validated_data.pop('formula_versions', [])

        with transaction.atomic(using=models.Stack.objects.db):
            # Create the stack
            stack = self.Meta.model.objects.create(**validated_data)

            # Create the formula versions
            formula_version_field = self.fields['formula_versions']
            # Add in the stack to all the formula versions
            for formula_version in formula_versions:
                formula_version['content_object'] = stack
            formula_version_field.create(formula_versions)

        # The stack was created, now let's launch it
        # We'll pass the initial_data in as the opts
        workflow = workflows.LaunchWorkflow(stack, opts=self.initial_data)
        workflow.execute()

        return stack


class StackLabelSerializer(StackdioLabelSerializer):

    class Meta(StackdioLabelSerializer.Meta):
        app_label = 'stacks'
        model_name = 'stack-label'

    def validate(self, attrs):
        attrs = super(StackLabelSerializer, self).validate(attrs)

        key = attrs.get('key')

        if key and key in ('Name', 'stack_id'):
            raise serializers.ValidationError({
                'key': ['The keys `Name` and `stack_id` are reserved for system use.']
            })

        return attrs

    def save(self, **kwargs):
        label = super(StackLabelSerializer, self).save(**kwargs)

        stack_ctype = ContentType.objects.get_for_model(models.Stack)

        if label.content_type == stack_ctype:
            logger.info('Tagging infrastructure...')

            # Spin up the task to tag everything
            tasks.tag_infrastructure.si(label.object_id, None, False).apply_async()

        return label


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
            'rules',
            'group_id',
            'blueprint_host_definition',
            'account',
            'is_default',
            'is_managed',
            'active_hosts',
            'rules',
        )


class StackActionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    action = serializers.CharField(write_only=True)
    args = serializers.ListField(child=serializers.DictField(), required=False)

    def validate(self, attrs):
        stack = self.instance
        action = attrs['action']
        request = self.context['request']

        if stack.status not in models.Stack.SAFE_STATES:
            raise serializers.ValidationError({
                'action': ['You may not perform an action while the stack is in its current state.']
            })

        driver_hosts_map = stack.get_driver_hosts_map()
        total_host_count = len(stack.get_hosts().exclude(instance_id=''))

        available_actions = set()

        # check the individual provider for available actions
        for driver in driver_hosts_map:
            host_available_actions = driver.get_available_actions()
            if action not in host_available_actions:
                err_msg = ('At least one of the hosts in this stack does not support '
                           'the requested action.')
                raise serializers.ValidationError({
                    'action': [err_msg]
                })
            available_actions.update(host_available_actions)

        if action not in available_actions:
            raise serializers.ValidationError({
                'action': ['{0} is not a valid action.'.format(action)]
            })

        # Check to make sure the user is authorized to execute the action
        if action not in utils.filter_actions(request.user, stack, available_actions):
            raise PermissionDenied(
                'You are not authorized to run the "{0}" action on this stack'.format(action)
            )

        # All actions other than launch require hosts to be available
        if action != 'launch' and total_host_count == 0:
            err_msg = ('The submitted action requires the stack to have available hosts. '
                       'Perhaps you meant to run the launch action instead.')
            raise serializers.ValidationError({
                'action': [err_msg]
            })

        # Make sure the action is executable on all hosts
        for driver, hosts in driver_hosts_map.items():
            # check the action against current states (e.g., starting can't
            # happen unless the hosts are in the stopped state.)
            # XXX: Assuming that host metadata is accurate here
            for host in hosts:
                start_stop_msg = ('{0} action requires all hosts to be in the {1} '
                                  'state first. At least one host is reporting an invalid '
                                  'state: {2}')

                if action == driver.ACTION_START and host.state != driver.STATE_STOPPED:
                    raise serializers.ValidationError({
                        'action': [start_stop_msg.format('Start', driver.STATE_STOPPED, host.state)]
                    })
                if action == driver.ACTION_STOP and host.state != driver.STATE_RUNNING:
                    raise serializers.ValidationError({
                        'action': [start_stop_msg.format('Stop', driver.STATE_RUNNING, host.state)]
                    })
                if action == driver.ACTION_TERMINATE and host.state not in (driver.STATE_RUNNING,
                                                                            driver.STATE_STOPPED):
                    raise serializers.ValidationError({
                        'action': [start_stop_msg.format('Terminate',
                                                         'running or stopped',
                                                         host.state)]
                    })

                require_running = (
                    driver.ACTION_PROVISION,
                    driver.ACTION_ORCHESTRATE
                )

                if action in require_running and host.state != driver.STATE_RUNNING:
                    err_msg = ('Provisioning actions require all hosts to be in the '
                               'running state first. At least one host is reporting '
                               'an invalid state: {0}'.format(host.state))
                    raise serializers.ValidationError({
                        'action': [err_msg]
                    })

        return attrs

    def to_representation(self, instance):
        """
        We just want to return a serialized stack object here.  Returning an object with
        the action in it just doesn't make much sense.
        """
        return StackSerializer(instance, context=self.context).to_representation(instance)

    def save(self, **kwargs):
        stack = self.instance
        action = self.validated_data['action']
        args = self.validated_data.get('args', [])

        stack.set_status(models.Stack.EXECUTING_ACTION,
                         models.Stack.EXECUTING_ACTION,
                         'Stack is executing action \'{0}\''.format(action))

        # Utilize our workflow to run the action
        workflow = workflows.ActionWorkflow(stack, action, args)
        workflow.execute()

        return self.instance


class StackCommandSerializer(StackdioHyperlinkedModelSerializer):
    zip_url = serializers.HyperlinkedIdentityField(view_name='api:stacks:stackcommand-zip')

    class Meta:
        model = models.StackCommand
        fields = (
            'id',
            'url',
            'zip_url',
            'submit_time',
            'start_time',
            'finish_time',
            'status',
            'host_target',
            'command',
            'std_out',
            'std_err',
        )

        read_only_fields = (
            'status',
        )

    def create(self, validated_data):
        command = super(StackCommandSerializer, self).create(validated_data)

        # Start the celery task to run the command
        tasks.run_command.si(command.id).apply_async()

        return command
