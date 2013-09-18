from django.contrib import admin

from .models import (
    Stack, 
    StackHistory, 
    SaltRole, 
    Host,
)


class StackAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'user',
        'cloud_provider',
        'created',
        'modified',
    ]
admin.site.register(Stack, StackAdmin)


class StackHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'event',
        'status',
        'level',
        'created',
    ]
admin.site.register(StackHistory, StackHistoryAdmin)


class SaltRoleAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'role_name',
    ]
admin.site.register(SaltRole, SaltRoleAdmin)


class HostAdmin(admin.ModelAdmin):
    list_display = [
        'stack',
        'cloud_profile',
        'instance_size',
        'hostname',
        'provider_dns',
        'fqdn',
    ]
admin.site.register(Host, HostAdmin)

