from django.contrib import admin

from . import models


class StackAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'owner',
        'blueprint',
        #'cloud_provider',
        'created',
        'modified',
    ]
admin.site.register(models.Stack, StackAdmin)


class StackHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'event',
        'status',
        'level',
        'created',
    ]
admin.site.register(models.StackHistory, StackHistoryAdmin)


class HostAdmin(admin.ModelAdmin):
    list_display = [
        'stack',
        'cloud_profile',
        'instance_size',
        'hostname',
        'provider_dns',
        'fqdn',
    ]
admin.site.register(models.Host, HostAdmin)

