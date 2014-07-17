from rest_framework import permissions

import logging


logger = logging.getLogger(__name__)


class AdminOrOwnerPermission(permissions.IsAdminUser):
    """
    A permission that allows access to owners and admins only
    """
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner \
            or super(AdminOrOwnerPermission, self) \
            .has_permission(request, view)

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
        if super(AdminOrOwnerOrPublicPermission, self) \
                .has_object_permission(request, view, obj):
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
