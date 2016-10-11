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


class VolumeAdmin(GuardedModelAdmin):
    list_display = [
        'volume_id',
        'stack',
        'host',
        'snapshot',
        'device',
        'mount_point',
    ]


admin.site.register(models.Volume, VolumeAdmin)
