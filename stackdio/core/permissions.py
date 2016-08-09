# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import logging

from rest_framework import permissions


logger = logging.getLogger(__name__)


# For list/create views
class StackdioModelPermissions(permissions.DjangoModelPermissions):
    """
    Override the default permission namings
    """
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.create_%(model_name)s'],
        'PUT': ['%(app_label)s.update_%(model_name)s'],
        'PATCH': ['%(app_label)s.update_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


# For detail views
class StackdioObjectPermissions(permissions.DjangoObjectPermissions):
    """
    Override the default permission namings
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.create_%(model_name)s'],
        'PUT': ['%(app_label)s.update_%(model_name)s'],
        'PATCH': ['%(app_label)s.update_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def has_permission(self, request, view):
        return True


# Create a wrapper view that gives the superclass the right queryset when it tries
class WrapperView(object):

    def __init__(self, view):
        super(WrapperView, self).__init__()
        self.view = view

    def get_queryset(self):
        if hasattr(self.view, 'get_parent_queryset'):
            queryset = self.view.get_parent_queryset()
        else:
            queryset = getattr(self.view, 'parent_queryset', None)

        assert queryset is not None, (
            'Cannot apply StackdioParentObjectPermissions on a view that '
            'does not set `.parent_queryset` or have a `.get_parent_queryset()` method.'
        )

        return queryset

    def __getattr__(self, item):
        return getattr(self.view, item)


class StackdioParentPermissions(permissions.DjangoObjectPermissions):
    """
    To be used on views that have parent objects to ensure the child view
    has permission to view the parent object
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.update_%(model_name)s'],
        'PUT': ['%(app_label)s.update_%(model_name)s'],
        'PATCH': ['%(app_label)s.update_%(model_name)s'],
        'DELETE': ['%(app_label)s.update_%(model_name)s'],
    }

    def has_permission(self, request, view):
        """
        Check permissions on the parent object.
        """
        return super(StackdioParentPermissions,
                     self).has_object_permission(request,
                                                 WrapperView(view),
                                                 view.get_parent_object())

    def has_object_permission(self, request, view, obj):
        return True


class StackdioParentObjectPermissions(StackdioObjectPermissions):
    """
    Very similar to regular object permissions, except that we don't want to use the model_cls
    from the queryset, since the queryset may not be the same type of object that we want to
    check permissions on.  Classic example being the `/api/stacks/<pk>/hosts/` endpoint - we want
    to check permissions on a stack object, but the queryset consists of host objects.
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.update_%(model_name)s'],
        'PUT': ['%(app_label)s.update_%(model_name)s'],
        'PATCH': ['%(app_label)s.update_%(model_name)s'],
        'DELETE': ['%(app_label)s.update_%(model_name)s'],
    }

    def has_object_permission(self, request, view, obj):
        """
        Mostly the same as the version in the parent class,
        but we'll use parent_queryset and get_parent_queryset instead.
        """
        return super(StackdioParentObjectPermissions,
                     self).has_object_permission(request, WrapperView(view), obj)


class StackdioPermissionsPermissions(StackdioParentPermissions):
    perms_map = {
        'GET': ['%(app_label)s.admin_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.admin_%(model_name)s'],
        'PUT': ['%(app_label)s.admin_%(model_name)s'],
        'PATCH': ['%(app_label)s.admin_%(model_name)s'],
        'DELETE': ['%(app_label)s.admin_%(model_name)s'],
    }


class StackdioPermissionsModelPermissions(permissions.DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.admin_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.admin_%(model_name)s'],
        'PUT': ['%(app_label)s.admin_%(model_name)s'],
        'PATCH': ['%(app_label)s.admin_%(model_name)s'],
        'DELETE': ['%(app_label)s.admin_%(model_name)s'],
    }

    model_cls = None

    def has_permission(self, request, view):
        assert self.model_cls is not None, (
            'Cannot apply %s directly. '
            'You must subclass it and override the `parent_model_cls` '
            'attribute.' % self.__class__.__name__)

        model_cls = self.model_cls

        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, '_ignore_model_permissions', False):
            return True

        perms = self.get_required_permissions(request.method, model_cls)

        return (
            request.user and
            (request.user.is_authenticated() or not self.authenticated_users_only) and
            request.user.has_perms(perms)
        )


class StackdioPermissionsObjectPermissions(StackdioParentObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.admin_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.admin_%(model_name)s'],
        'PUT': ['%(app_label)s.admin_%(model_name)s'],
        'PATCH': ['%(app_label)s.admin_%(model_name)s'],
        'DELETE': ['%(app_label)s.admin_%(model_name)s'],
    }
