from django.contrib import admin
from .models import UserSettings


class UserSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'public_key',
    ]

admin.site.register(UserSettings, UserSettingsAdmin)
