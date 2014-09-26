from django.contrib import admin
from . import models


class CloudProviderTypeAdmin(admin.ModelAdmin):
    list_display = [
        'type_name',
    ]
admin.site.register(models.CloudProviderType, CloudProviderTypeAdmin)


class CloudProviderAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'description',
        'vpc_enabled',
    ]
admin.site.register(models.CloudProvider, CloudProviderAdmin)


class CloudInstanceSizeAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'description',
        'provider_type',
        'instance_id',
    ]
admin.site.register(models.CloudInstanceSize, CloudInstanceSizeAdmin)


class CloudProfileAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'cloud_provider',
        'image_id',
        'default_instance_size',
        'ssh_user',
    ]
admin.site.register(models.CloudProfile, CloudProfileAdmin)


class SnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'cloud_provider',
        'snapshot_id',
        'size_in_gb',
        'filesystem_type',
    ]
admin.site.register(models.Snapshot, SnapshotAdmin)


class SecurityGroupAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'group_id',
        'cloud_provider',
        'owner',
        'is_default',
    ]
admin.site.register(models.SecurityGroup, SecurityGroupAdmin)
