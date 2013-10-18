from django.contrib import admin

from .models import (
    Blueprint, 
    BlueprintProperty, 
    BlueprintHostDefinition, 
    BlueprintAccessRule, 
)


class BlueprintAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'owner',
        'property_count',
        'host_definition_count',
        'created',
        'modified',
    ]
admin.site.register(Blueprint, BlueprintAdmin)


class BlueprintPropertyAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'value',
        'blueprint',
        'created',
        'modified',
    ]
admin.site.register(BlueprintProperty, BlueprintPropertyAdmin)


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
admin.site.register(BlueprintHostDefinition, BlueprintHostDefinitionAdmin)


class BlueprintAccessRuleAdmin(admin.ModelAdmin):
    list_display = [
        'host',
        'protocol',
        'from_port',
        'to_port',
        'rule',
    ]
admin.site.register(BlueprintAccessRule, BlueprintAccessRuleAdmin)

