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
from collections import OrderedDict
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers

from stackdio.core.fields import HyperlinkedField, PasswordField
from stackdio.core.notifications.serializers import NotificationChannelSerializer
from stackdio.core.serializers import (
    StackdioHyperlinkedModelSerializer,
    StackdioParentHyperlinkedModelSerializer,
)
from . import models, utils


logger = logging.getLogger(__name__)


LDAP_MANAGED_FIELDS = (
    'username',
    'first_name',
    'last_name',
    'email',
)


class UserGroupSerializer(StackdioHyperlinkedModelSerializer):
    class Meta:
        model = Group
        lookup_field = 'name'
        fields = (
            'url',
            'name',
        )


class GroupUserSerializer(StackdioHyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        lookup_field = 'username'
        fields = (
            'url',
            'username',
        )


class GroupSerializer(StackdioHyperlinkedModelSerializer):
    users = serializers.HyperlinkedIdentityField(
        view_name='api:users:group-userlist',
        lookup_field='name', lookup_url_kwarg='parent_name')
    action = serializers.HyperlinkedIdentityField(
        view_name='api:users:group-action',
        lookup_field='name', lookup_url_kwarg='parent_name')
    channels = serializers.HyperlinkedIdentityField(
        view_name='api:users:group-channel-list',
        lookup_field='name', lookup_url_kwarg='parent_name')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:users:group-object-user-permissions-list',
        lookup_field='name', lookup_url_kwarg='parent_name')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:users:group-object-group-permissions-list',
        lookup_field='name', lookup_url_kwarg='parent_name')

    class Meta:
        model = Group
        lookup_field = 'name'
        fields = (
            'url',
            'name',
            'users',
            'action',
            'channels',
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
            'advanced_view',
        )

    def update(self, instance, validated_data):
        previous_value = instance.advanced_view
        instance = super(UserSettingsSerializer, self).update(instance, validated_data)
        new_value = instance.advanced_view

        request = self.context['request']._request

        if previous_value and not new_value:
            messages.info(request, 'You have disabled the advanced view.  It may take a minute '
                                   'for all of the advanced links to be disabled.')
        elif not previous_value and new_value:
            messages.info(request, 'You have enabled the advanced view.  It may take a minute '
                                   'for all of the advanced links to be enabled.')

        return instance


class UserSerializer(StackdioHyperlinkedModelSerializer):
    superuser = serializers.BooleanField(source='is_superuser', read_only=True)

    groups = serializers.HyperlinkedIdentityField(
        view_name='api:users:user-grouplist',
        lookup_field='username', lookup_url_kwarg='parent_username',
    )

    settings = UserSettingsSerializer()

    channels = HyperlinkedField(view_name='api:users:currentuser-channel-list')

    change_password = HyperlinkedField(view_name='api:users:currentuser-password')

    class Meta:
        model = get_user_model()
        lookup_field = 'username'
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'superuser',
            'last_login',
            'groups',
            'channels',
            'change_password',
            'settings',
        )

        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
        }

    def validate(self, attrs):
        if settings.LDAP_ENABLED and self.instance:
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

    def create(self, validated_data):
        """
        We want to override this method so we can send an email to the new user with a link
        to reset their password
        """
        user = super(UserSerializer, self).create(validated_data)

        request = self.context['request']

        from_email = None

        subject_template_name = 'stackdio/auth/new_user_subject.txt'
        email_template_name = 'stackdio/auth/password_reset_email.html'

        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain

        context = {
            'email': user.email,
            'domain': domain,
            'site_name': site_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': default_token_generator.make_token(user),
            'protocol': 'https' if request.is_secure() else 'http',
            'intro_line': 'You\'re receiving this email because one of the administrators at {0} '
                          'has created an account for you.'.format(site_name)
        }

        utils.send_mail(subject_template_name, email_template_name, context, from_email, user.email)

        return user

    # We need a custom update since we have a nested field
    def update(self, instance, validated_data):
        # We need to manually pop off settings and update manually
        user_settings = validated_data.pop('settings')

        if user_settings:
            settings_serializer = self.fields['settings']
            settings_serializer.update(instance.settings, user_settings)

        instance = super(UserSerializer, self).update(instance, validated_data)

        # Now we need to put it back, in case something else needs it later.
        if user_settings:
            validated_data['settings'] = user_settings

        return instance


class PublicUserSerializer(UserSerializer):
    """
    This is the serializer for the main user list view.  It's the same as the main UserSerializer,
    it just has a few fields hidden.
    """
    class Meta(UserSerializer.Meta):
        fields = (
            'url',
            'username',
            'first_name',
            'last_name',
            'email',
            'groups',
        )


class ChangePasswordSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    current_password = PasswordField(label='Current Password')
    new_password1 = PasswordField(label='New Password')
    new_password2 = PasswordField(label='New Password Again')

    def to_representation(self, instance):
        """
        We just want to return a serialized user object here, since we should never show
        passwords in plain text
        """
        return UserSerializer(instance, context=self.context).to_representation(instance)

    def validate(self, attrs):
        if settings.LDAP_ENABLED:
            # Just stop immediately if we're on LDAP
            raise serializers.ValidationError({
                'current_password': ['You cannot change your password when using LDAP '
                                     'authentication.']
            })

        # the current user is set as the instance when we initialize the serializer
        user = self.instance

        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({
                'current_password': ['You entered an incorrect current password value.']
            })

        if attrs['new_password1'] != attrs['new_password2']:
            raise serializers.ValidationError({
                'new_password2': ['The 2 new passwords don\'t match.']
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

        # change the password.  We can just grab new_password1 since we validated that it's the
        # same as new_password2 in the validate() method
        new_password = self.validated_data['new_password1']

        self.instance.set_password(new_password)
        self.instance.save()

        return self.instance


class UserNotificationChannelSerializer(NotificationChannelSerializer):

    class Meta(NotificationChannelSerializer.Meta):
        app_label = 'users'
        model_name = 'currentuser-channel'


class GroupNotificationChannelSerializer(StackdioParentHyperlinkedModelSerializer,
                                         NotificationChannelSerializer):

    class Meta(NotificationChannelSerializer.Meta):
        app_label = 'users'
        model_name = 'group-channel'
        parent_attr = 'auth_object'
        parent_lookup_field = 'name'
