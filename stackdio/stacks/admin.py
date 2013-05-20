from django.contrib import admin

from .models import Stack, Role, StackMetadata, Host

class StackAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'slug',
        'user',
        'created',
        'modified',
    ]
admin.site.register(Stack, StackAdmin)

class RoleAdmin(admin.ModelAdmin):
    

    list_display = [
        'title',
        'slug',
        'role_name',
    ]
admin.site.register(Role, RoleAdmin)

class StackMetadataAdmin(admin.ModelAdmin):
    

    list_display = [
        'stack',
        'role',
        'instance_count',
        'host_pattern',
    ]
admin.site.register(StackMetadata, StackMetadataAdmin)

class HostAdmin(admin.ModelAdmin):
    

    list_display = [
        'stack',
        'role',
        'hostname',
    ]
admin.site.register(Host, HostAdmin)
