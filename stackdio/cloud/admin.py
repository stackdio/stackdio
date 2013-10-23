from django.contrib import admin

from .models import (
    CloudProviderType, 
    CloudProvider, 
    CloudInstanceSize,
    CloudProfile,
    Snapshot,
    SecurityGroup,
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

class CloudInstanceSizeAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'slug',
        'description',
        'provider_type',
        'instance_id',
    ]
admin.site.register(CloudInstanceSize, CloudInstanceSizeAdmin)

class CloudProfileAdmin(admin.ModelAdmin):


    list_display = [
        'title',
        'cloud_provider',
        'image_id',
        'default_instance_size',
        'ssh_user',
    ]
admin.site.register(CloudProfile, CloudProfileAdmin)


class SnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'cloud_provider',
        'snapshot_id',
        'size_in_gb',
        'filesystem_type',
    ]
admin.site.register(Snapshot, SnapshotAdmin)


class SecurityGroupAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'group_id',
        'cloud_provider',
        'owner',
        'is_default',
    ]
admin.site.register(SecurityGroup, SecurityGroupAdmin)

