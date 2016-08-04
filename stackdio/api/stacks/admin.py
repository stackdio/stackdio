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


class StackAdmin(GuardedModelAdmin):
    list_display = [
        'title',
        'slug',
        'blueprint',
        'created',
        'modified',
    ]


admin.site.register(models.Stack, StackAdmin)


class StackHistoryAdmin(GuardedModelAdmin):
    list_display = [
        'message',
        'created',
    ]


admin.site.register(models.StackHistory, StackHistoryAdmin)


class HostAdmin(GuardedModelAdmin):
    list_display = [
        'stack',
        'cloud_image',
        'instance_size',
        'hostname',
        'provider_public_dns',
        'provider_private_dns',
        'fqdn',
    ]


admin.site.register(models.Host, HostAdmin)
