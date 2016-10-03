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

import inspect
import logging

from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework import serializers

from .fields import HyperlinkedParentField
from . import mixins, models, validators

logger = logging.getLogger(__name__)


class BulkListSerializer(serializers.ListSerializer):

    def update(self, queryset, all_validated_data):
        id_attr = getattr(self.child.Meta, 'update_lookup_field', 'id')

        all_validated_data_by_id = {
            i.pop(id_attr): i
            for i in all_validated_data
        }

        if not all((bool(i) and not inspect.isclass(i)
                    for i in all_validated_data_by_id.keys())):
            raise serializers.ValidationError('')

        # since this method is given a queryset which can have many
        # model instances, first find all objects to update
        # and only then update the models
        objects_to_update = self.filter_queryset(queryset, id_attr, all_validated_data_by_id)

        self.check_objects_to_update(objects_to_update, all_validated_data_by_id)

        updated_objects = []

        for obj in objects_to_update:
            obj_validated_data = self.get_obj_validated_data(obj, id_attr, all_validated_data_by_id)

            # use model serializer to actually update the model
            # in case that method is overwritten
            updated_objects.append(self.child.update(obj, obj_validated_data))

        return updated_objects

    def filter_queryset(self, queryset, id_attr, all_validated_data_by_id):
        return queryset.filter(**{
            '{}__in'.format(id_attr): all_validated_data_by_id.keys(),
        })

    def check_objects_to_update(self, objects_to_update, all_validated_data_by_id):
        if len(all_validated_data_by_id) != objects_to_update.count():
            raise serializers.ValidationError({
                'bulk': 'Could not find all objects to update.',
            })

    def get_obj_validated_data(self, obj, id_attr, all_validated_data_by_id):
        obj_id = getattr(obj, id_attr)
        return all_validated_data_by_id.get(obj_id)


class BulkSerializerMixin(object):

    def to_internal_value(self, data):
        ret = super(BulkSerializerMixin, self).to_internal_value(data)

        id_attr = getattr(self.Meta, 'update_lookup_field', 'id')
        request_method = getattr(getattr(self.context.get('view'), 'request'), 'method', '')

        # add update_lookup_field field back to validated data
        # since super by default strips out read-only fields
        # hence id will no longer be present in validated_data
        if all((isinstance(self.root, BulkListSerializer),
                id_attr,
                request_method in ('PUT', 'PATCH'))):
            id_field = self.fields[id_attr]
            id_value = id_field.get_value(data)

            ret[id_attr] = id_value

        return ret


class StackdioHyperlinkedModelSerializer(serializers.HyperlinkedModelSerializer):
    """
    Override to use the appropriately namespaced url
    """

    def add_extra_kwargs(self, kwargs):
        """
        Hook to be able to add in extra kwargs
        (specifically for the StackdioParentHyperlinkedModelSerializer)
        """
        return kwargs

    def build_url_field(self, field_name, model_class):
        """
        Create a field representing the object's own URL.
        """
        field_class = self.serializer_url_field
        root_namespace = getattr(self.Meta, 'root_namespace', 'api')
        app_label = getattr(self.Meta, 'app_label', model_class._meta.app_label)
        model_name = getattr(self.Meta, 'model_name', model_class._meta.object_name.lower())
        lookup_field = getattr(self.Meta, 'lookup_field', 'pk')
        lookup_url_kwarg = getattr(self.Meta, 'lookup_url_kwarg', lookup_field)

        # Override user things
        if model_name in ('user', 'group', 'permission'):
            app_label = 'users'

        field_kwargs = {
            'view_name': '%s:%s:%s-detail' % (root_namespace, app_label, model_name),
            'lookup_field': lookup_field,
            'lookup_url_kwarg': lookup_url_kwarg,
        }

        field_kwargs = self.add_extra_kwargs(field_kwargs)

        return field_class, field_kwargs


class StackdioParentHyperlinkedModelSerializer(StackdioHyperlinkedModelSerializer):

    serializer_url_field = HyperlinkedParentField

    def add_extra_kwargs(self, kwargs):
        parent_attr = getattr(self.Meta, 'parent_attr', None)
        parent_lookup_field = getattr(self.Meta, 'parent_lookup_field', 'pk')
        default_parent_lookup_url_kwarg = 'parent_{}'.format(parent_lookup_field)
        parent_lookup_url_kwarg = getattr(self.Meta,
                                          'parent_lookup_url_kwarg',
                                          default_parent_lookup_url_kwarg)

        kwargs['parent_attr'] = parent_attr
        kwargs['parent_lookup_field'] = parent_lookup_field
        kwargs['parent_lookup_url_kwarg'] = parent_lookup_url_kwarg

        return kwargs


class StackdioLabelSerializer(mixins.CreateOnlyFieldsMixin,
                              StackdioParentHyperlinkedModelSerializer):
    """
    This is an abstract class meant to be extended for any type of object that needs to be labelled
    by setting the appropriate `app_label` and `model_name` attributes on the `Meta` class.

    ```
    class MyObjectLabelSerializer(StackdioLabelSerializer):

        # The Meta class needs to inherit from the super Meta class
        class Meta(StackdioLabelSerializer.Meta):
            app_label = 'my-app'
            model_name = 'my-object'
    ```
    """

    class Meta:
        model = models.Label
        parent_attr = 'content_object'
        lookup_field = 'key'
        lookup_url_kwarg = 'label_name'

        fields = (
            'url',
            'key',
            'value',
        )

        extra_kwargs = {
            'key': {'validators': [validators.LabelValidator()]},
            'value': {'validators': [validators.LabelValidator()]},
        }

        create_only_fields = (
            'key',
        )

    def validate(self, attrs):
        content_object = self.context.get('content_object')
        key = attrs.get('key')

        # Only need to validate if both a key was passed in and the content_object already exists
        if key and content_object:
            labels = content_object.labels.filter(key=key)

            if labels.count() > 0:
                raise serializers.ValidationError({
                    'key': ['Label keys must be unique.']
                })

        return attrs


class StackdioLiteralLabelsSerializer(StackdioLabelSerializer):

    class Meta(StackdioLabelSerializer.Meta):
        fields = (
            'key',
            'value',
        )


class PermissionsBulkListSerializer(BulkListSerializer):

    name_attr_map = {
        'user': 'username',
        'group': 'name',
    }

    def filter_queryset(self, queryset, id_attr, all_validated_data_by_id):
        ret = []
        for obj in queryset:
            auth_obj = obj[id_attr]

            name_attr = self.name_attr_map[id_attr]

            if getattr(auth_obj, name_attr) in all_validated_data_by_id:
                ret.append(obj)

        return ret

    def check_objects_to_update(self, objects_to_update, all_validated_data_by_id):
        if len(all_validated_data_by_id) != len(objects_to_update):
            raise serializers.ValidationError({
                'bulk': 'Could not find all objects to update.',
            })

    def get_obj_validated_data(self, obj, id_attr, all_validated_data_by_id):
        auth_obj = obj[id_attr]
        name_attr = self.name_attr_map[id_attr]

        return all_validated_data_by_id[getattr(auth_obj, name_attr)]


class StackdioModelPermissionsSerializer(BulkSerializerMixin, serializers.Serializer):

    class Meta:
        list_serializer_class = PermissionsBulkListSerializer

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

        with transaction.atomic():
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

        # Make sure we do this atomically - since we're removing all permissions on a PUT,
        # don't commit the transaction until the permissions have been re-created
        with transaction.atomic():
            if not self.partial:
                # PUT request - delete all the permissions, then recreate them later
                for perm in instance['permissions']:
                    remove_perm('%s.%s_%s' % (app_label, perm, model_name), auth_obj)

            # We now want to do the same thing as create
            return self.create(validated_data)


class StackdioObjectPermissionsSerializer(BulkSerializerMixin, serializers.Serializer):

    class Meta:
        list_serializer_class = PermissionsBulkListSerializer

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

        with transaction.atomic():
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

        # Make sure we do this atomically - since we're removing all permissions on a PUT,
        # don't commit the transaction until the permissions have been re-created
        with transaction.atomic():
            if not self.partial:
                # PUT request - delete all the permissions, then recreate them later
                for perm in instance['permissions']:
                    remove_perm('%s.%s_%s' % (app_label, perm, model_name), auth_obj, obj)

            # We now want to do the same thing as create
            return self.create(validated_data)


class EventField(serializers.SlugRelatedField):

    default_error_messages = {
        'does_not_exist': _('Event \'{value}\' does not exist.'),
        'invalid': _('Invalid value.'),
    }

    def __init__(self, **kwargs):
        if not kwargs.get('read_only', False):
            kwargs.setdefault('queryset', models.Event.objects.all())
        super(EventField, self).__init__(slug_field='tag', **kwargs)


class EventSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Event

        fields = (
            'tag',
        )
