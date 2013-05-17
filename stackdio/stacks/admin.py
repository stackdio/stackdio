from django.contrib import admin

from .models import Stack

class StackAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'user',
        'created',
        'modified',
    ]
admin.site.register(Stack, StackAdmin)
