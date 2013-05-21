from django.contrib import admin

#from .models import Stack, Role, StackMetadata, Host

class CloudProviderTypeAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'slug',
        'description',
    ]
admin.site.register('cloud.CloudProviderType', CloudProviderTypeAdmin)

class CloudProviderAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'slug',
        'description',
    ]
admin.site.register('cloud.CloudProvider', CloudProviderAdmin)

class CloudProviderInstanceSizeAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'slug',
        'description',
    ]
admin.site.register('cloud.CloudProviderInstanceSize', CloudProviderInstanceSizeAdmin)
