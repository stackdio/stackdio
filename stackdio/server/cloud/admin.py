# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


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


class GlobalOrchestrationFormulaComponentAdmin(admin.ModelAdmin):
    list_display = [
        'component',
        'provider',
        'order',
    ]
admin.site.register(models.GlobalOrchestrationFormulaComponent, GlobalOrchestrationFormulaComponentAdmin)


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


class CloudRegionAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'description',
        'provider_type',
    ]
admin.site.register(models.CloudRegion, CloudRegionAdmin)


class CloudZoneAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'slug',
        'description',
        'region',
    ]
admin.site.register(models.CloudZone, CloudZoneAdmin)


class SecurityGroupAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'group_id',
        'cloud_provider',
        'owner',
        'is_default',
    ]
admin.site.register(models.SecurityGroup, SecurityGroupAdmin)
