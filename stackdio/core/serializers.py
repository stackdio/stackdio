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

from celery import chain
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework import serializers

from stackdio.core import mixins, models
from stackdio.api.stacks.tasks import tag_infrastructure, finish_stack
from stackdio.api.stacks.models import Stack

logger = logging.getLogger(__name__)


class StackdioHyperlinkedModelSerializer(serializers.HyperlinkedModelSerializer):
    """
    Override to use the appropriately namespaced url
    """
    def build_url_field(self, field_name, model_class):
        """
        Create a field representing the object's own URL.
        """
        field_class = self.serializer_url_field
        app_label = getattr(self.Meta, 'app_label', model_class._meta.app_label)
        model_name = getattr(self.Meta, 'model_name', model_class._meta.object_name.lower())

        # Override user things
        if model_name in ('user', 'group', 'permission'):
            app_label = 'users'
        field_kwargs = {
            'view_name': 'api:%s:%s-detail' % (app_label, model_name),
        }

        return field_class, field_kwargs


class LabelUrlField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk is None:
            return None

        kwargs = {
            'pk': obj.object_id,
            'label_name': obj.key,
        }
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class StackdioLabelSerializer(mixins.CreateOnlyFieldsMixin, StackdioHyperlinkedModelSerializer):

    serializer_url_field = LabelUrlField

    class Meta:
        model = models.Label
        app_label = 'stacks'
        model_name = 'stack-label'

        fields = (
            'url',
            'key',
            'value',
        )

        create_only_fields = (
            'key',
        )

    def validate(self, attrs):
        content_object = self.context['content_object']
        key = attrs.get('key')

        if key:
            labels = content_object.labels.filter(key=key)

            if labels.count() > 0:
                raise serializers.ValidationError({
                    'key': ['Label keys must be unique.']
                })

        return attrs

    def save(self, **kwargs):
        label = super(StackdioLabelSerializer, self).save(**kwargs)

        stack_ctype = ContentType.objects.get_for_model(Stack)

        if label.content_type == stack_ctype:
            logger.info('Tagging infrastructure...')

            # Spin up the task to tag everything
            task_chain = chain(
                tag_infrastructure.si(label.object_id),
                finish_stack.si(label.object_id),
            )

            task_chain.apply_async()

        return label


class StackdioModelPermissionsSerializer(serializers.Serializer):

    def validate(self, attrs):
        view = self.context['view']

        available_perms = view.get_model_permissions()
        bad_perms = []

        for perm in attrs['permissions']:
            if perm not in available_perms:
                bad_perms.append(perm)

        if bad_perms:
            raise serializers.ValidationError({
                'permissions': ['Invalid permissions: {0}'.format(', '.join(bad_perms))]
            })

        return attrs

    def create(self, validated_data):
        # Determine if this is a user or group
        view = self.context['view']
        user_or_group = view.get_user_or_group()

        # Grab our data
        auth_obj = validated_data[user_or_group]

        # Grab model class
        model_cls = validated_data['model_cls']
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name

        for perm in validated_data['permissions']:
            assign_perm('%s.%s_%s' % (app_label, perm, model_name), auth_obj)

        return self.to_internal_value(validated_data)

    def update(self, instance, validated_data):
        # Determine if this is a user or group
        view = self.context['view']
        user_or_group = view.get_user_or_group()

        # The funkiness below is to prevent a client from submitting a PUT or PATCH request to
        # /api/<resource>/permissions/users/user_id1 with user="user_id2".  If this were
        # allowed, you could change the permissions of any user from the endpoint of any other user

        # Pull the user from the instance to update rather than from the incoming request
        auth_obj = instance[user_or_group]
        # Then add it to the validated_data so the create request uses the correct user
        validated_data[user_or_group] = auth_obj

        # Grab the object
        model_cls = validated_data['model_cls']
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name

        if not self.partial:
            # PUT request - delete all the permissions, then recreate them later
            for perm in instance['permissions']:
                remove_perm('%s.%s_%s' % (app_label, perm, model_name), auth_obj)

        # We now want to do the same thing as create
        return self.create(validated_data)


class StackdioObjectPermissionsSerializer(serializers.Serializer):

    def validate(self, attrs):
        view = self.context['view']

        available_perms = view.get_object_permissions()
        bad_perms = []

        for perm in attrs['permissions']:
            if perm not in available_perms:
                bad_perms.append(perm)

        if bad_perms:
            raise serializers.ValidationError({
                'permissions': ['Invalid permissions: {0}'.format(', '.join(bad_perms))]
            })

        return attrs

    def create(self, validated_data):
        # Determine if this is a user or group
        view = self.context['view']
        user_or_group = view.get_user_or_group()

        # Grab our data
        auth_obj = validated_data[user_or_group]
        # Grab the object
        obj = validated_data['object']
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name

        for perm in validated_data['permissions']:
            assign_perm('%s.%s_%s' % (app_label, perm, model_name), auth_obj, obj)

        return self.to_internal_value(validated_data)

    def update(self, instance, validated_data):
        # Determine if this is a user or group
        view = self.context['view']
        user_or_group = view.get_user_or_group()

        # The funkiness below is to prevent a client from submitting a PUT or PATCH request to
        # /api/<resource>/<pk>/permissions/users/user_id1 with user="user_id2".  If this were
        # allowed, you could change the permissions of any user from the endpoint of any other user

        # Pull the user from the instance to update rather than from the incoming request
        auth_obj = instance[user_or_group]
        # Then add it to the validated_data so the create request uses the correct user
        validated_data[user_or_group] = auth_obj

        # Grab the object
        obj = validated_data['object']
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name

        if not self.partial:
            # PUT request - delete all the permissions, then recreate them later
            for perm in instance['permissions']:
                remove_perm('%s.%s_%s' % (app_label, perm, model_name), auth_obj, obj)

        # We now want to do the same thing as create
        return self.create(validated_data)
