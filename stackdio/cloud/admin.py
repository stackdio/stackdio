from django.contrib import admin

from .models import (
    CloudProviderType, 
    CloudProvider, 
    CloudProviderInstanceSize,
    CloudProfile,
)

class CloudProviderTypeAdmin(admin.ModelAdmin):


    list_display = [
        'type_name',
    ]
admin.site.register(CloudProviderType, CloudProviderTypeAdmin)

class CloudProviderAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'slug',
        'description',
    ]
admin.site.register(CloudProvider, CloudProviderAdmin)

class CloudProviderInstanceSizeAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'slug',
        'description',
        'provider_type',
        'instance_id',
    ]
admin.site.register(CloudProviderInstanceSize, CloudProviderInstanceSizeAdmin)

class CloudProfileAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'cloud_provider',
        'image_id',
        'default_instance_size',
        'script',
        'ssh_user',
    ]
admin.site.register(CloudProfile, CloudProfileAdmin)
