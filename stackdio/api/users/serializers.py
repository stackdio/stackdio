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
from collections import OrderedDict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers

from stackdio.core.fields import HyperlinkedField
from . import models


logger = logging.getLogger(__name__)


LDAP_MANAGED_FIELDS = (
    'username',
    'first_name',
    'last_name',
    'email',
)


class UserGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        lookup_field = 'name'
        fields = (
            'url',
            'name',
        )


class PublicUserSerializer(serializers.HyperlinkedModelSerializer):
    groups = serializers.HyperlinkedIdentityField(
        view_name='user-grouplist',
        lookup_field='username'
    )

    class Meta:
        model = get_user_model()
        lookup_field = 'username'
        fields = (
            'url',
            'username',
            'first_name',
            'last_name',
            'email',
            'groups',
        )


class GroupUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        lookup_field = 'username'
        fields = (
            'url',
            'username',
        )


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    users = serializers.HyperlinkedIdentityField(view_name='group-userlist', lookup_field='name')
    action = serializers.HyperlinkedIdentityField(view_name='group-action', lookup_field='name')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='group-object-user-permissions-list',
        lookup_field='name',
    )
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='group-object-group-permissions-list',
        lookup_field='name',
    )

    class Meta:
        model = Group
        lookup_field = 'name'
        fields = (
            'url',
            'name',
            'users',
            'action',
            'user_permissions',
            'group_permissions',
        )


class GroupActionReturnSerializer(GroupSerializer):
    users = GroupUserSerializer(source='user_set', many=True)


class GroupActionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    available_actions = ('add-user', 'remove-user')

    action = serializers.ChoiceField(available_actions)
    user = serializers.SlugRelatedField(slug_field='username', queryset=models.get_user_queryset())

    def to_representation(self, instance):
        """
        We just want to return a serialized group object here -
        that way you can see immediately
        what the new users in the group are
        """
        return GroupActionReturnSerializer(
            instance,
            context=self.context
        ).to_representation(instance)

    def save(self, **kwargs):
        group = self.instance
        action = self.validated_data['action']
        user = self.validated_data['user']

        if action == 'add-user':
            group.user_set.add(user)
        elif action == 'remove-user':
            group.user_set.remove(user)

        return group


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserSettings
        fields = (
            'public_key',
        )


class UserSerializer(serializers.ModelSerializer):
    superuser = serializers.BooleanField(source='is_superuser', read_only=True)

    groups = serializers.HyperlinkedIdentityField(
        view_name='user-grouplist',
        lookup_field='username'
    )

    settings = UserSettingsSerializer()

    change_password = HyperlinkedField(view_name='currentuser-password')

    class Meta:
        model = get_user_model()
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'superuser',
            'last_login',
            'groups',
            'change_password',
            'settings',
        )

    def validate(self, attrs):
        if settings.LDAP_ENABLED:
            # We only run into issues if using LDAP
            errors = OrderedDict()

            for attr, value in attrs.items():
                current_value = getattr(self.instance, attr)
                # Only deny the request if the field is LDAP managed AND is changed
                if attr in LDAP_MANAGED_FIELDS and value != current_value:
                    errors[attr] = ['This in an LDAP managed field.']

            if errors:
                raise serializers.ValidationError(errors)

        return attrs

    # We need a custom update since we have a nested field
    def update(self, instance, validated_data):
        # We need to manually pop off settings and update manually
        settings = validated_data.pop('settings')

        if settings:
            settings_serializer = self.fields['settings']
            settings_serializer.update(instance.settings, settings)

        instance = super(UserSerializer, self).update(instance, validated_data)

        # Now we need to put it back, in case something else needs it later.
        if settings:
            validated_data['settings'] = settings

        return instance


class ChangePasswordSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def to_representation(self, instance):
        """
        We just want to return a serialized user object here, since we should never show
        passwords in plain text
        """
        return UserSerializer(instance, context=self.context).to_representation(instance)

    def validate(self, attrs):
        if settings.LDAP_ENABLED:
            # Just stop immediately if we're on LDAP
            raise serializers.ValidationError(
                'You cannot change your password when using LDAP authentication.'
            )

        # the current user is set as the instance when we initialize the serializer
        user = self.instance

        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({
                'current_password': ['You entered an incorrect current password value.']
            })

        return attrs

    def save(self, **kwargs):
        """
        Using create / update here doesn't really make sense, so we'll just
        override save() directly
        """
        assert hasattr(self, '_errors'), (
            'You must call `.is_valid()` before calling `.save()`.'
        )

        assert not self.errors, (
            'You cannot call `.save()` on a serializer with invalid data.'
        )

        # change the password
        new_password = self.validated_data['new_password']

        self.instance.set_password(new_password)
        self.instance.save()

        return self.instance
