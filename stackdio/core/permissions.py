from rest_framework import permissions


class AdminOrOwnerPermission(permissions.IsAdminUser):

    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner \
               or super(AdminOrOwnerPermission, self) \
                    .has_object_permission(request, view, obj)