from django.contrib import admin

from .models import (
    Volume, 
)


class VolumeAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'created',
        'modified',
    ]
admin.site.register(Volume, VolumeAdmin)
