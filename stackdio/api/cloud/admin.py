# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from . import models


class CloudProviderAdmin(GuardedModelAdmin):
    list_display = [
        'name',
    ]


admin.site.register(models.CloudProvider, CloudProviderAdmin)


class CloudAccountAdmin(GuardedModelAdmin):
    list_display = [
        'title',
        'slug',
        'description',
        'vpc_enabled',
    ]


admin.site.register(models.CloudAccount, CloudAccountAdmin)


class CloudInstanceSizeAdmin(GuardedModelAdmin):
    list_display = [
        'title',
        'slug',
        'description',
        'provider',
        'instance_id',
    ]


admin.site.register(models.CloudInstanceSize, CloudInstanceSizeAdmin)


class CloudImageAdmin(GuardedModelAdmin):
    list_display = [
        'title',
        'account',
        'image_id',
        'default_instance_size',
        'ssh_user',
    ]


admin.site.register(models.CloudImage, CloudImageAdmin)


class SnapshotAdmin(GuardedModelAdmin):
    list_display = [
        'title',
        'slug',
        'account',
        'snapshot_id',
        'filesystem_type',
    ]


admin.site.register(models.Snapshot, SnapshotAdmin)


class CloudRegionAdmin(GuardedModelAdmin):
    list_display = [
        'title',
        'slug',
        'description',
        'provider',
    ]


admin.site.register(models.CloudRegion, CloudRegionAdmin)


class CloudZoneAdmin(GuardedModelAdmin):
    list_display = [
        'title',
        'slug',
        'description',
        'region',
    ]


admin.site.register(models.CloudZone, CloudZoneAdmin)


class SecurityGroupAdmin(GuardedModelAdmin):
    list_display = [
        'group_id',
        'name',
        'description',
        'account',
        'is_default',
        'is_managed',
    ]


admin.site.register(models.SecurityGroup, SecurityGroupAdmin)
