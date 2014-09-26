from django.contrib import admin

from .models import (
    Formula, 
    FormulaComponent, 
)


class FormulaAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'owner',
        'public',
        'created',
        'modified',
    ]
admin.site.register(Formula, FormulaAdmin)


class FormulaComponentAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'formula',
        'sls_path',
    ]
admin.site.register(FormulaComponent, FormulaComponentAdmin)
