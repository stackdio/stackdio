# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
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

from __future__ import absolute_import, unicode_literals

import logging
import re

from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.validators import UniqueValidator
from stackdio.api.environments import models, utils, workflows
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.core.constants import Action, Activity
from stackdio.core.serializers import (
    PropertiesField,
    StackdioHyperlinkedModelSerializer,
    StackdioLabelSerializer,
    StackdioLiteralLabelsSerializer,
)

logger = logging.getLogger(__name__)


ENV_NAME_REGEX = r'^[a-z0-9\-\_]+$'


def validate_name(value):
    if not re.match(ENV_NAME_REGEX, value):
        raise serializers.ValidationError(
            'Name may only contain alphanumeric characters, dashes (-), and underscores (_).'
        )


class EnvironmentSerializer(StackdioHyperlinkedModelSerializer):

    label_list = StackdioLiteralLabelsSerializer(read_only=True, many=True, source='labels')

    properties = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-properties',
        lookup_field='name')
    formula_versions = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-formula-versions',
        lookup_field='name', lookup_url_kwarg='parent_name')
    labels = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-label-list',
        lookup_field='name', lookup_url_kwarg='parent_name')
    components = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-component-list',
        lookup_field='name', lookup_url_kwarg='parent_name')
    action = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-action',
        lookup_field='name', lookup_url_kwarg='parent_name')
    logs = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-logs',
        lookup_field='name', lookup_url_kwarg='parent_name')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-object-user-permissions-list',
        lookup_field='name', lookup_url_kwarg='parent_name')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-object-group-permissions-list',
        lookup_field='name', lookup_url_kwarg='parent_name')

    class Meta:
        model = models.Environment
        lookup_field = 'name'
        fields = (
            'url',
            'name',
            'description',
            'orchestrate_sls_path',
            'activity',
            'health',
            'create_users',
            'label_list',
            'properties',
            'components',
            'labels',
            'formula_versions',
            'action',
            'logs',
            'user_permissions',
            'group_permissions',
        )

        read_only_fields = (
            'activity',
            'health',
        )

        extra_kwargs = {
            'name': {
                'validators': [
                    UniqueValidator(models.Environment.objects.all()),
                    validate_name,
                ]
            },
            'create_users': {
                'default': serializers.CreateOnlyDefault(settings.STACKDIO_CONFIG.create_ssh_users)
            },
        }


class FullEnvironmentSerializer(EnvironmentSerializer):

    properties = PropertiesField(required=False)
    formula_versions = FormulaVersionSerializer(many=True, required=False)
    labels = StackdioLiteralLabelsSerializer(many=True, required=False)

    def create(self, validated_data):
        # Pull out the nested stuff
        formula_versions = validated_data.pop('formula_versions', [])
        labels = validated_data.pop('labels', [])

        with transaction.atomic(using=models.Environment.objects.db):
            # Create the environment
            environment = super(FullEnvironmentSerializer, self).create(validated_data)

            # Create the formula versions
            formula_version_field = self.fields['formula_versions']
            # Add in the environment to all the formula versions
            for formula_version in formula_versions:
                formula_version['content_object'] = environment
            formula_version_field.create(formula_versions)

            # Create the labels
            label_field = self.fields['labels']
            # Add in the environment to all the labels
            for label in labels:
                label['content_object'] = environment
            label_field.create(labels)

        # Add the other fields back in for deserialization
        validated_data['formula_versions'] = formula_versions
        validated_data['labels'] = labels

        return environment

    def to_representation(self, instance):
        super_serializer = EnvironmentSerializer(instance, context=self.context)
        return super_serializer.to_representation(instance)


class EnvironmentActionSerializer(serializers.Serializer):
    action = serializers.CharField(write_only=True)
    args = serializers.ListField(child=serializers.DictField(), required=False)

    def validate(self, attrs):
        environment = self.instance
        action = attrs['action']
        request = self.context['request']

        if action not in Action.ENVIRONMENT_ALL:
            raise serializers.ValidationError({
                'action': ['{0} is not a valid action.'.format(action)]
            })

        if action not in Activity.env_action_map.get(environment.activity, []):
            err_msg = 'You may not perform the {0} action while the environment is {1}.'
            raise serializers.ValidationError({
                'action': [err_msg.format(action, environment.activity)]
            })

        # Check to make sure the user is authorized to execute the action
        if action not in utils.filter_actions(request.user, environment, Action.ENVIRONMENT_ALL):
            raise PermissionDenied(
                'You are not authorized to run the "{0}" action on this environment'.format(action)
            )

        single_sls_errors = []

        if action == Action.SINGLE_SLS:
            args = attrs.get('args', [])
            for arg in args:
                if 'component' not in arg:
                    single_sls_errors.append('arg is missing a component')

        if single_sls_errors:
            raise serializers.ValidationError({
                'args': single_sls_errors,
            })

        return attrs

    def to_representation(self, instance):
        """
        We just want to return a serialized environment object here.  Returning an object with
        the action in it just doesn't make much sense.
        """
        return EnvironmentSerializer(instance, context=self.context).to_representation(instance)

    def create(self, validated_data):
        raise NotImplementedError('Don\'t call create')

    def update(self, instance, validated_data):
        raise NotImplementedError('Don\'t call update')

    def save(self, **kwargs):
        environment = self.instance
        action = self.validated_data['action']
        args = self.validated_data.get('args', [])

        environment.activity = Activity.QUEUED
        environment.save()

        # Utilize our workflow to run the action
        workflow = workflows.ActionWorkflow(environment, action, args)
        workflow.execute()

        return self.instance


class EnvironmentLabelSerializer(StackdioLabelSerializer):

    class Meta(StackdioLabelSerializer.Meta):
        app_label = 'environments'
        model_name = 'environment-label'
        parent_lookup_field = 'name'


class EnvironmentHostSerializer(serializers.Serializer):

    hostname = serializers.CharField(source='id')

    roles = serializers.ListField()

    ip_addresses = serializers.ListField(source='ipv4')

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class ComponentMetadataSerializer(serializers.ModelSerializer):

    timestamp = serializers.DateTimeField(source='modified')

    class Meta:
        model = models.ComponentMetadata

        fields = (
            'host',
            'status',
            'health',
            'timestamp',
        )


class EnvironmentComponentSerializer(serializers.Serializer):

    sls_path = serializers.CharField()
    status = serializers.CharField()
    health = serializers.CharField()
    hosts = ComponentMetadataSerializer(many=True, source='metadatas')

    def create(self, validated_data):
        raise NotImplementedError('Cannot create components.')

    def update(self, instance, validated_data):
        raise NotImplementedError('Cannot update components.')
