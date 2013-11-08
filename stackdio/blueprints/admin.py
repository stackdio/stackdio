from django.contrib import admin

from . import models


class BlueprintAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'owner',
        'host_definition_count',
        'created',
        'modified',
    ]
admin.site.register(models.Blueprint, BlueprintAdmin)


class BlueprintHostDefinitionAdmin(admin.ModelAdmin):
    list_display = [
        'prefix',
        'blueprint',
        'cloud_profile',
        'count',
        'size',
        'zone',
        'formula_components_count',
    ]
admin.site.register(models.BlueprintHostDefinition, BlueprintHostDefinitionAdmin)


class BlueprintAccessRuleAdmin(admin.ModelAdmin):
    list_display = [
        'host',
        'protocol',
        'from_port',
        'to_port',
        'rule',
    ]
admin.site.register(models.BlueprintAccessRule, BlueprintAccessRuleAdmin)

