# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

from __future__ import unicode_literals

import six
from django.db import models
from django_extensions.db.models import TimeStampedModel

_volume_model_permissions = (
    'create',
    'admin',
)

_volume_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


@six.python_2_unicode_compatible
class Volume(TimeStampedModel):
    model_permissions = _volume_model_permissions
    object_permissions = _volume_object_permissions

    class Meta:
        default_permissions = tuple(set(_volume_model_permissions + _volume_object_permissions))

    # The host is the actual host this volume is attached to, but
    # it can only be assigned after the host is up and the volume is
    # actually attached
    host = models.ForeignKey('stacks.Host',
                             related_name='volumes')

    blueprint_volume = models.ForeignKey('blueprints.BlueprintVolume',
                                         related_name='volumes')

    # the volume id as provided by the cloud provider. This can only
    # be populated after the volume has been created, thus allowing
    # blank values
    volume_id = models.CharField('Volume ID', max_length=32, blank=True)

    def __str__(self):
        return six.text_type(self.volume_id)

    @property
    def device(self):
        return self.blueprint_volume.device

    @property
    def mount_point(self):
        return self.blueprint_volume.mount_point

    @property
    def snapshot(self):
        return self.blueprint_volume.snapshot

    @property
    def snapshot_id(self):
        return self.snapshot.snapshot_id if self.snapshot else None

    @property
    def size_in_gb(self):
        return self.blueprint_volume.size_in_gb

    @property
    def encrypted(self):
        return self.blueprint_volume.encrypted

    @property
    def extra_options(self):
        return self.blueprint_volume.extra_options

    @property
    def stack(self):
        return self.host.stack if self.host else None
