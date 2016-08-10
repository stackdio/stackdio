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

from django.conf import settings
from rest_framework import permissions


logger = logging.getLogger(__name__)


def log_permissions(cls):
    """
    decorator to log some things about permissions.
    """

    # Log permissions only if we're debugging
    if settings.DEBUG:
        cur_has_perm = getattr(cls, 'has_permission')
        cur_has_obj_perm = getattr(cls, 'has_object_permission')

        def has_permission(self, request, view):
            try:
                ret = cur_has_perm(self, request, view)
                logger.debug('{} has_permission for {} {} called: {}'.format(
                    cls.__name__,
                    request.method,
                    request.get_full_path(),
                    ret
                ))
                return ret
            except Exception as e:
                logger.debug('{} has_permission for {} {} threw an exception: {}'.format(
                    cls.__name__,
                    request.method,
                    request.get_full_path(),
                    e.message
                ))
                raise

        def has_object_permission(self, request, view, obj):
            try:
                ret = cur_has_obj_perm(self, request, view, obj)
                logger.debug('{} has_object_permission for {} {} called: {}'.format(
                    cls.__name__,
                    request.method,
                    request.get_full_path(),
                    ret
                ))
                return ret
            except Exception as e:
                logger.debug('{} has_object_permission for {} {} threw an exception: {}'.format(
                    cls.__name__,
                    request.method,
                    request.get_full_path(),
                    e.message
                ))
                raise

        cls.has_permission = has_permission
        cls.has_object_permission = has_object_permission

    return cls


# For list/create views
@log_permissions
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
@log_permissions
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


class WrapperView(object):
    """
    Just a simple wrapper so that when parent permission classes call us, they check
    permissions on the parent object instead of the current object.
    """
    def __init__(self, view, perm_obj):
        super(WrapperView, self).__init__()
        self.view = view
        self.perm_obj = perm_obj

    def get_queryset(self):
        if hasattr(self.view, 'get_parent_queryset'):
            queryset = self.view.get_parent_queryset()
        else:
            queryset = getattr(self.view, 'parent_queryset', None)

        assert queryset is not None, (
            'Cannot apply {} on a view that does not set `.parent_queryset` or have a '
            '`.get_parent_queryset()` method.'.format(self.perm_obj.__class__.__name__)
        )

        return queryset

    # Just in class we call something else
    def __getattr__(self, item):
        return getattr(self.view, item)


@log_permissions
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
                                                 WrapperView(view, self),
                                                 view.get_parent_object())

    def has_object_permission(self, request, view, obj):
        return True


@log_permissions
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


@log_permissions
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
