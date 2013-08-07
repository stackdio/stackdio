from django.contrib import admin

from .models import (
    Volume, 
)


class VolumeAdmin(admin.ModelAdmin):
    list_display = [
        'volume_id',
        'attach_time',
        'stack',
        'hostname',
        'host',
        'snapshot',
        'device',
        'mount_point',
    ]
admin.site.register(Volume, VolumeAdmin)

