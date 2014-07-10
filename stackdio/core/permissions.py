from rest_framework import permissions


class AdminOrOwnerPermission(permissions.BasePermission):
    """
    A permission that allows access to owners and admins only
    """
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner or request.user.is_staff


class AdminOrOwnerOrPublicPermission(AdminOrOwnerPermission):
    """
    A permission that allows safe methods through for public objects and
    all access to owners and admins
    """
    def has_object_permission(self, request, view, obj):
        if super(AdminOrOwnerOrPublicPermission, self) \
                .has_object_permission(request, view, obj):
            return True

        if not obj.public:
            return False

        return request.method in permissions.SAFE_METHODS
