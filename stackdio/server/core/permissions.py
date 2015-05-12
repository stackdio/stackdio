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


class StackdioDjangoObjectPermissions(permissions.DjangoObjectPermissions):
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
