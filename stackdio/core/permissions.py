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

    def has_permission(self, request, view):
        """
        Since this is for 'parent' object permissions, override this to check permissions on
        the parent object.
        """
        try:
            model_name = self.parent_model_cls._meta.model_name
        except AttributeError:
            return False

        # Grab the get_object method
        get_object_method = getattr(view, 'get_%s' % model_name, None)

        # Couldn't find a method, no permission granted
        if get_object_method is None:
            return False

        return self.has_object_permission(request, view, get_object_method())

    def has_object_permission(self, request, view, obj):
        assert self.parent_model_cls is not None, (
            'Cannot apply %s directly. '
            'You must subclass it and override the `parent_model_cls` '
            'attribute.' % self.__class__.__name__)

        model_cls = self.parent_model_cls
        user = request.user

        # There's a weird case sometimes where the BrowsableAPIRenderer checks permissions
        # that it doesn't need to, and throws an exception.  We'll default to less permissions
        # here rather than more.
        try:
            if obj._meta.app_label != model_cls._meta.app_label:
                return False
        except AttributeError:
            # This means the BrowsableRenderer is trying to check object permissions on one of our
            # permissions responses... which are just dicts, so it doesn't know what to do.  We'll
            # check the parent object instead.
            model_name = model_cls._meta.model_name
            # All of our parent views have a `get_<model_name>` method, so we'll grab that and use
            # it to get an object to check permissions on.
            get_parent_obj = getattr(view, 'get_%s' % model_name)
            if get_parent_obj:
                return self.has_object_permission(request, view, get_parent_obj())
            else:
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


class StackdioPermissionsModelPermissions(permissions.DjangoModelPermissions):
    """
    Override the default permission namings
    """
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
