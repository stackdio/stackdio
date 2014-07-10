from rest_framework import permissions


class AdminOrOwnerPermission(permissions.IsAdminUser):

    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner \
               or super(AdminOrOwnerPermission, self) \
                    .has_object_permission(request, view, obj)

class AdminOrOwnerOrPublicPermission(AdminOrOwnerPermission):

    def has_object_permission(self, request, view, obj):
        if super(AdminOrOwnerOrPublicPermission, self) \
                .has_object_permission(request, view, obj):
            return True

        if not obj.public:
            return False

        return request.method in permissions.SAFE_METHODS
