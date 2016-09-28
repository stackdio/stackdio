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

from django.conf import settings
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.models import Group
from rest_framework import generics
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.response import Response

from stackdio.core.config import StackdioConfigException
from stackdio.core.notifications.models import NotificationChannel
from stackdio.core.permissions import StackdioModelPermissions
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)
from . import filters, mixins, permissions, serializers

try:
    from django_auth_ldap.backend import LDAPBackend
except ImportError:
    LDAPBackend = None


class UserListAPIView(generics.ListCreateAPIView):
    queryset = get_user_model().objects.order_by('username')
    serializer_class = serializers.PublicUserSerializer
    permission_classes = (StackdioModelPermissions,)
    lookup_field = 'username'
    filter_class = filters.UserFilter

    def get_queryset(self):
        if settings.LDAP_ENABLED and 'username' in self.request.query_params:
            if LDAPBackend is None:
                raise StackdioConfigException('LDAP is enabled, but django_auth_ldap isn\'t '
                                              'installed.  Please install django_auth_ldap')
            # Try populating the user first
            LDAPBackend().populate_user(self.request.query_params['username'])
        return super(UserListAPIView, self).get_queryset()


class UserDetailAPIView(generics.RetrieveAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.PublicUserSerializer
    lookup_field = 'username'


class UserModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    model_permissions = ('create', 'admin')
    parent_lookup_field = 'username'
    model_cls = get_user_model()


class UserModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    model_permissions = ('create', 'admin')
    parent_lookup_field = 'username'
    model_cls = get_user_model()


class UserGroupListAPIView(mixins.UserRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.UserGroupSerializer
    lookup_field = 'username'

    def get_queryset(self):
        return self.get_user().groups.order_by('name')


class GroupListAPIView(generics.ListCreateAPIView):
    queryset = Group.objects.order_by('name')
    serializer_class = serializers.GroupSerializer
    permission_classes = (StackdioModelPermissions,)
    lookup_field = 'name'
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.GroupFilter


class GroupDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = (permissions.GroupObjectPermissions,)
    lookup_field = 'name'


class GroupUserListAPIView(mixins.GroupRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.GroupUserSerializer
    lookup_field = 'name'

    def get_queryset(self):
        return self.get_group().user_set.order_by('username')


class GroupActionAPIView(mixins.GroupRelatedMixin, generics.GenericAPIView):
    serializer_class = serializers.GroupActionSerializer

    def get(self, request, *args, **kwargs):
        ret = {
            'available_actions': self.serializer_class.available_actions
        }
        return Response(ret)

    def post(self, request, *args, **kwargs):
        group = self.get_group()

        serializer = self.get_serializer(group, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GroupChannelListAPIView(mixins.GroupRelatedMixin, generics.ListCreateAPIView):
    serializer_class = serializers.GroupNotificationChannelSerializer

    def get_queryset(self):
        return NotificationChannel.objects.filter(auth_object=self.get_group())

    def get_serializer_context(self):
        context = super(GroupChannelListAPIView, self).get_serializer_context()
        context['auth_object'] = self.get_group()
        return context

    def perform_create(self, serializer):
        serializer.save(auth_object=self.get_group())


class GroupChannelDetailAPIView(mixins.GroupRelatedMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.GroupNotificationChannelSerializer
    lookup_field = 'name'

    def get_queryset(self):
        return NotificationChannel.objects.filter(auth_object=self.get_group())

    def get_serializer_context(self):
        context = super(GroupChannelDetailAPIView, self).get_serializer_context()
        context['auth_object'] = self.get_group()
        return context

    def perform_update(self, serializer):
        serializer.save(auth_object=self.get_group())


class GroupModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    model_permissions = ('create', 'admin')
    parent_lookup_field = 'name'
    model_cls = Group


class GroupModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    model_permissions = ('create', 'admin')
    parent_lookup_field = 'name'
    model_cls = Group


class GroupObjectUserPermissionsViewSet(mixins.GroupPermissionsMixin,
                                        StackdioObjectUserPermissionsViewSet):
    object_permissions = ('update', 'delete', 'admin', 'view')


class GroupObjectGroupPermissionsViewSet(mixins.GroupPermissionsMixin,
                                         StackdioObjectGroupPermissionsViewSet):
    object_permissions = ('update', 'delete', 'admin', 'view')


class CurrentUserDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return self.request.user


class CurrentUserChannelListAPIView(generics.ListCreateAPIView):
    serializer_class = serializers.UserNotificationChannelSerializer

    def get_queryset(self):
        return NotificationChannel.objects.filter(auth_object=self.request.user)

    def get_serializer_context(self):
        context = super(CurrentUserChannelListAPIView, self).get_serializer_context()
        context['auth_object'] = self.request.user
        return context

    def perform_create(self, serializer):
        serializer.save(auth_object=self.request.user)


class CurrentUserChannelDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.UserNotificationChannelSerializer
    lookup_field = 'name'

    def get_queryset(self):
        return NotificationChannel.objects.filter(auth_object=self.request.user)

    def get_serializer_context(self):
        context = super(CurrentUserChannelDetailAPIView, self).get_serializer_context()
        context['auth_object'] = self.request.user
        return context

    def perform_update(self, serializer):
        serializer.save(auth_object=self.request.user)


class ChangePasswordAPIView(generics.GenericAPIView):
    """
    API that handles changing your account password. Note that
    only POST requests are available on this endpoint. Below
    are the required parameters of the JSON object you will POST.

    * `current_password` - Your current password.
    * `new_password1` - Your new password you want to change to.
    * `new_password2` - Your new password again.  Note that this must match
        `new_password1` exactly.
    """

    serializer_class = serializers.ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # This ensures that the user doesn't get logged out after the password change
        update_session_auth_hash(request, user)
        return Response(serializer.data)
