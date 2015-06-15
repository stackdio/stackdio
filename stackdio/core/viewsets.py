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

from django.http import Http404
from guardian.shortcuts import get_groups_with_perms, get_users_with_perms, remove_perm
from rest_framework import viewsets

from core.shortcuts import get_groups_with_model_perms, get_users_with_model_perms


class StackdioBasePermissionsViewSet(viewsets.ModelViewSet):
    """
    Viewset for creating permissions endpoints
    """
    user_or_group = None
    lookup_value_regex = r'[\w.@+-]+'

    def get_user_or_group(self):
        assert self.user_or_group in ('user', 'group'), (
            "'%s' should include a `user_or_group` attribute that is one of 'user' or 'group'."
            % self.__class__.__name__
        )
        return self.user_or_group

    def switch_user_group(self, if_user, if_group):
        if self.get_user_or_group() == 'user':
            return if_user
        elif self.get_user_or_group() == 'group':
            return if_group
        else:
            raise ValueError(
                "'%s' should include a `user_or_group` attribute that is one of 'user' or 'group'."
                % self.__class__.__name__
            )

    def _transform_perm(self, model_name):
        def do_tranform(item):
            perm, sep, empty = item.partition('_' + model_name)
            return perm

        return do_tranform

    def get_object(self):
        queryset = self.get_queryset()

        for obj in queryset:
            auth_obj = obj[self.get_user_or_group()]
            name_attr = self.switch_user_group('username', 'name')

            if self.kwargs[self.lookup_field] == getattr(auth_obj, name_attr):
                return obj

        raise Http404('No permissions found for %s' % self.kwargs[self.lookup_field])


class StackdioModelPermissionsViewSet(StackdioBasePermissionsViewSet):
    model_cls = None

    def get_model_cls(self):
        assert self.model_cls, (
            "'%s' should include a `model_cls` attribute or override the `get_model_cls()` method."
            % self.__class__.__name__
        )
        return self.model_cls

    def get_queryset(self):
        model_cls = self.get_model_cls()
        model_name = model_cls._meta.model_name

        # Grab the perms for either the users or groups
        perm_map = self.switch_user_group(
            get_users_with_model_perms(model_cls, attach_perms=True, with_group_users=False),
            get_groups_with_model_perms(model_cls, attach_perms=True),
        )

        ret = []
        for auth_obj, perms in perm_map.items():
            ret.append({
                self.get_user_or_group(): auth_obj,
                'permissions': map(self._transform_perm(model_name), perms),
            })
        return ret

    def list(self, request, *args, **kwargs):
        response = super(StackdioModelPermissionsViewSet, self).list(request, *args, **kwargs)
        # add available permissions to the response
        response.data['available_permissions'] = sorted(self.model_cls.model_permissions)

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


class StackdioModelGroupPermissionsViewSet(StackdioModelPermissionsViewSet):
    user_or_group = 'group'
    lookup_field = 'groupname'


class StackdioObjectPermissionsViewSet(StackdioBasePermissionsViewSet):
    """
    Viewset for creating permissions endpoints
    """

    def get_permissioned_object(self):
        raise NotImplementedError('`get_permissioned_object()` must be implemented.')

    def get_queryset(self):
        obj = self.get_permissioned_object()
        model_name = obj._meta.model_name

        # Grab the perms for either the users or groups
        perm_map = self.switch_user_group(
            get_users_with_perms(obj, attach_perms=True),
            get_groups_with_perms(obj, attach_perms=True),
        )

        ret = []
        for auth_obj, perms in perm_map.items():
            ret.append({
                self.get_user_or_group(): auth_obj,
                'permissions': map(self._transform_perm(model_name), perms),
            })
        return ret

    def list(self, request, *args, **kwargs):
        response = super(StackdioObjectPermissionsViewSet, self).list(request, *args, **kwargs)
        # add available permissions to the response
        obj = self.get_permissioned_object()
        response.data['available_permissions'] = sorted(obj.object_permissions)

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


class StackdioObjectUserPermissionsViewSet(StackdioObjectPermissionsViewSet):
    user_or_group = 'user'
    lookup_field = 'username'


class StackdioObjectGroupPermissionsViewSet(StackdioObjectPermissionsViewSet):
    user_or_group = 'group'
    lookup_field = 'groupname'
