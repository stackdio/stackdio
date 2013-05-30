from django.contrib import admin

from .models import (
    Stack, 
    SaltRole, 
    Host,
    SecurityGroup,
)

class StackAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'slug',
        'user',
        'created',
        'modified',
    ]
admin.site.register(Stack, StackAdmin)

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
    ]
admin.site.register(Host, HostAdmin)

class SecurityGroupAdmin(admin.ModelAdmin):
    

    list_display = [
        'group_name',
    ]
admin.site.register(SecurityGroup, SecurityGroupAdmin)
