# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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

    parent_model_cls = None

    def has_object_permission(self, request, view, obj):
        assert self.parent_model_cls is not None, (
            'Cannot apply StackdioParentObjectPermissions directly. '
            'You must subclass it and override the `parent_model_cls` '
            'attribute.')

        model_cls = self.parent_model_cls
        user = request.user

        # There's a weird case sometimes where the BrowsableAPIRenderer checks permissions
        # that it doesn't need to, and throws an exception.  We'll default to less permissions
        # here rather than more.
        if obj._meta.app_label != model_cls._meta.app_label:
            return False

        perms = self.get_required_object_permissions(request.method, model_cls)

        if not user.has_perms(perms, obj):
            # If the user does not have permissions we need to determine if
            # they have read permissions to see 403, or not, and simply see
            # a 404 response.

            if request.method in permissions.SAFE_METHODS:
                # Read permissions already checked and failed, no need
                # to make another lookup.
                raise permissions.Http404

            read_perms = self.get_required_object_permissions('GET', model_cls)
            if not user.has_perms(read_perms, obj):
                raise permissions.Http404

            # Has read permissions.
            return False

        return True


class AdminOrOwnerPermission(permissions.IsAdminUser):
    """
    A permission that allows access to owners and admins only
    """

    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner \
            or super(AdminOrOwnerPermission, self).has_permission(request, view)

    # Override this so as not to use the one from permissions.IsAdminUser
    def has_permission(self, request, view):
        return True


class AdminOrOwnerOrPublicPermission(AdminOrOwnerPermission):
    """
    A permission that allows safe methods through for public objects and
    all access to owners and admins
    """

    def has_object_permission(self, request, view, obj):
        # Give all permission to owners and admins
        if super(AdminOrOwnerOrPublicPermission, self).has_object_permission(request, view, obj):
            return True

        # Give read-only access to public objects
        if request.method in permissions.SAFE_METHODS:
            return obj.public
        else:
            return False


class IsAdminOrReadOnly(permissions.IsAdminUser):
    """
    A permission that allows all users read-only permission and admin users
    all permission
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            return super(IsAdminOrReadOnly, self).has_permission(request, view)
