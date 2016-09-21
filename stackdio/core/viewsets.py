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

from django.conf import settings
from django.contrib.auth.models import Group
from django.http import Http404
from guardian.shortcuts import get_groups_with_perms, get_users_with_perms, remove_perm
from rest_framework import viewsets
from rest_framework.serializers import ListField, SlugRelatedField, ValidationError

from stackdio.api.users.models import get_user_queryset
from stackdio.core.config import StackdioConfigException
from .permissions import StackdioPermissionsModelPermissions
from .shortcuts import get_groups_with_model_perms, get_users_with_model_perms
from . import fields, mixins, serializers

try:
    from django_auth_ldap.backend import LDAPBackend
except ImportError:
    LDAPBackend = None

logger = logging.getLogger(__name__)


def _filter_perms(available_perms, perms):
    ret = []
    for perm in perms:
        if perm in available_perms:
            ret.append(perm)
    return ret


class UserSlugRelatedField(SlugRelatedField):

    def to_internal_value(self, data):
        try:
            return super(UserSlugRelatedField, self).to_internal_value(data)
        except ValidationError:
            if settings.LDAP_ENABLED:
                if LDAPBackend is None:
                    raise StackdioConfigException('LDAP is enabled, but django_auth_ldap isn\'t '
                                                  'installed.  Please install django_auth_ldap')
                # Grab the ldap user and try again
                user = LDAPBackend().populate_user(data)
                if user is not None:
                    return super(UserSlugRelatedField, self).to_internal_value(data)
            # Nothing worked, just re-raise the exception
            raise


class StackdioBasePermissionsViewSet(mixins.BulkUpdateModelMixin, viewsets.ModelViewSet):
    """
    Viewset for creating permissions endpoints
    """
    user_or_group = None
    model_or_object = None
    lookup_value_regex = r'[\w.@+-]+'
    parent_lookup_field = 'pk'
    parent_lookup_url_kwarg = None

    def get_model_name(self):
        raise NotImplementedError('`get_model_name()` must be implemented.')

    def get_app_label(self):
        raise NotImplementedError('`get_app_label()` must be implemented.')

    def get_serializer_class(self):
        user_or_group = self.get_user_or_group()
        model_or_object = self.get_model_or_object()
        model_name = self.get_model_name()
        app_label = self.get_app_label()

        super_cls = self.switch_model_object(serializers.StackdioModelPermissionsSerializer,
                                             serializers.StackdioObjectPermissionsSerializer)

        default_parent_lookup_url_kwarg = 'parent_{}'.format(self.parent_lookup_field)

        url_field_kwargs = {
            'view_name': 'api:{0}:{1}-{2}-{3}-permissions-detail'.format(
                app_label,
                model_name,
                model_or_object,
                user_or_group
            ),
            'permission_lookup_field': self.lookup_field,
            'permission_lookup_url_kwarg': self.lookup_url_kwarg or self.lookup_field,
            'lookup_field': self.parent_lookup_field,
            'lookup_url_kwarg': self.parent_lookup_url_kwarg or default_parent_lookup_url_kwarg,
        }

        url_field_cls = self.switch_model_object(
            fields.HyperlinkedModelPermissionsField,
            fields.HyperlinkedObjectPermissionsField,
        )

        # Create a class
        class StackdioUserPermissionsSerializer(super_cls):
            user = UserSlugRelatedField(slug_field='username', queryset=get_user_queryset())
            url = url_field_cls(**url_field_kwargs)
            permissions = ListField()

            class Meta(super_cls.Meta):
                update_lookup_field = 'user'

        class StackdioGroupPermissionsSerializer(super_cls):
            group = SlugRelatedField(slug_field='name', queryset=Group.objects.all())
            url = url_field_cls(**url_field_kwargs)
            permissions = ListField()

            class Meta(super_cls.Meta):
                update_lookup_field = 'group'

        return self.switch_user_group(StackdioUserPermissionsSerializer,
                                      StackdioGroupPermissionsSerializer)

    def get_user_or_group(self):
        assert self.user_or_group in ('user', 'group'), (
            "'%s' should include a `user_or_group` attribute that is one of 'user' or 'group'."
            % self.__class__.__name__
        )
        return self.user_or_group

    def switch_user_group(self, if_user, if_group):
        return {
            'user': if_user,
            'group': if_group,
        }.get(self.get_user_or_group())

    def get_model_or_object(self):
        assert self.model_or_object in ('model', 'object'), (
            "'%s' should include a `model_or_object` attribute that is one of 'model' or 'object'."
            % self.__class__.__name__
        )
        return self.model_or_object

    def switch_model_object(self, if_model, if_object):
        return {
            'model': if_model,
            'object': if_object,
        }.get(self.get_model_or_object())

    def _transform_perm(self, model_name):
        def do_tranform(item):
            # pylint: disable=unused-variable
            perm, sep, empty = item.partition('_' + model_name)
            return perm

        return do_tranform

    def get_object(self):
        queryset = self.get_queryset()

        url_kwarg = self.lookup_url_kwarg or self.lookup_field
        name_attr = self.switch_user_group('username', 'name')

        for obj in queryset:
            auth_obj = obj[self.get_user_or_group()]

            if self.kwargs[url_kwarg] == getattr(auth_obj, name_attr):
                return obj

        raise Http404('No permissions found for %s' % self.kwargs[url_kwarg])


class StackdioModelPermissionsViewSet(StackdioBasePermissionsViewSet):
    model_cls = None
    model_or_object = 'model'
    permission_classes = (StackdioPermissionsModelPermissions,)

    def get_model_cls(self):
        assert self.model_cls, (
            "'%s' should include a `model_cls` attribute or override the `get_model_cls()` method."
            % self.__class__.__name__
        )
        return self.model_cls

    def get_model_name(self):
        return self.get_model_cls()._meta.model_name

    def get_app_label(self):
        ret = self.get_model_cls()._meta.app_label
        if ret == 'auth':
            # one-off thing, since users/groups are in the `users` app, not `auth`
            return 'users'
        return ret

    def get_model_permissions(self):
        return getattr(self.get_model_cls(),
                       'model_permissions',
                       getattr(self, 'model_permissions', ()))

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        ret = []
        for permission_cls in self.permission_classes:
            permission = permission_cls()

            # Inject our model_cls into the permission
            if isinstance(permission, StackdioPermissionsModelPermissions) \
                    and permission.model_cls is None:
                permission.model_cls = self.model_cls

            ret.append(permission)

        return ret

    def get_queryset(self):  # pylint: disable=method-hidden
        model_cls = self.get_model_cls()
        model_name = model_cls._meta.model_name
        model_perms = self.get_model_permissions()

        # Grab the perms for either the users or groups
        perm_map_func = self.switch_user_group(
            lambda: get_users_with_model_perms(model_cls, attach_perms=True,
                                               with_group_users=False),
            lambda: get_groups_with_model_perms(model_cls, attach_perms=True),
        )

        # Do this as a function so we don't fetch both the user AND group permissions on each
        # request
        perm_map = perm_map_func()

        ret = []
        sorted_perms = sorted(perm_map.items(), key=lambda x: getattr(x[0], self.lookup_field))
        for auth_obj, perms in sorted_perms:
            new_perms = [self._transform_perm(model_name)(perm) for perm in perms]

            ret.append({
                self.get_user_or_group(): auth_obj,
                'permissions': _filter_perms(model_perms, new_perms),
            })
        return ret

    def list(self, request, *args, **kwargs):
        response = super(StackdioModelPermissionsViewSet, self).list(request, *args, **kwargs)
        # add available permissions to the response
        response.data['available_permissions'] = sorted(self.get_model_permissions())

        return response

    def perform_create(self, serializer):
        serializer.save(model_cls=self.get_model_cls())

    def perform_update(self, serializer):
        serializer.save(model_cls=self.get_model_cls())

    def perform_destroy(self, instance):
        model_cls = self.get_model_cls()
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name
        for perm in instance['permissions']:
            remove_perm('%s.%s_%s' % (app_label, perm, model_name),
                        instance[self.get_user_or_group()])


class StackdioModelUserPermissionsViewSet(StackdioModelPermissionsViewSet):
    user_or_group = 'user'
    lookup_field = 'username'
    lookup_url_kwarg = 'username'


class StackdioModelGroupPermissionsViewSet(StackdioModelPermissionsViewSet):
    user_or_group = 'group'
    lookup_field = 'name'
    lookup_url_kwarg = 'groupname'


class StackdioObjectPermissionsViewSet(StackdioBasePermissionsViewSet):
    """
    Viewset for creating permissions endpoints
    """
    model_or_object = 'object'

    def get_permissioned_object(self):
        raise NotImplementedError('`get_permissioned_object()` must be implemented.')

    def get_model_name(self):
        return self.get_permissioned_object()._meta.model_name

    def get_app_label(self):
        ret = self.get_permissioned_object()._meta.app_label
        if ret == 'auth':
            # one-off thing, since users/groups are in the `users` app, not `auth`
            return 'users'
        return ret

    def get_object_permissions(self):
        return getattr(self.get_permissioned_object(),
                       'object_permissions',
                       getattr(self, 'object_permissions', ()))

    def get_queryset(self):  # pylint: disable=method-hidden
        obj = self.get_permissioned_object()
        model_name = obj._meta.model_name
        object_perms = self.get_object_permissions()

        # Grab the perms for either the users or groups
        perm_map_func = self.switch_user_group(
            lambda: get_users_with_perms(obj, attach_perms=True,
                                         with_superusers=False, with_group_users=False),
            lambda: get_groups_with_perms(obj, attach_perms=True),
        )

        perm_map = perm_map_func()

        ret = []
        sorted_perms = sorted(perm_map.items(), key=lambda x: getattr(x[0], self.lookup_field))
        for auth_obj, perms in sorted_perms:
            new_perms = [self._transform_perm(model_name)(perm) for perm in perms]

            ret.append({
                self.get_user_or_group(): auth_obj,
                'permissions': _filter_perms(object_perms, new_perms),
            })
        return ret

    def list(self, request, *args, **kwargs):
        response = super(StackdioObjectPermissionsViewSet, self).list(request, *args, **kwargs)
        # add available permissions to the response
        response.data['available_permissions'] = sorted(self.get_object_permissions())

        return response

    def perform_create(self, serializer):
        serializer.save(object=self.get_permissioned_object())

    def perform_update(self, serializer):
        serializer.save(object=self.get_permissioned_object())

    def perform_destroy(self, instance):
        obj = self.get_permissioned_object()
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name
        for perm in instance['permissions']:
            remove_perm('%s.%s_%s' % (app_label, perm, model_name),
                        instance[self.get_user_or_group()],
                        obj)


# pylint: disable=abstract-method
class StackdioObjectUserPermissionsViewSet(StackdioObjectPermissionsViewSet):
    user_or_group = 'user'
    lookup_field = 'username'
    lookup_url_kwarg = 'username'


class StackdioObjectGroupPermissionsViewSet(StackdioObjectPermissionsViewSet):
    user_or_group = 'group'
    lookup_field = 'name'
    lookup_url_kwarg = 'groupname'
