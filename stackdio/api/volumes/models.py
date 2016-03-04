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


class Volume(TimeStampedModel):

    model_permissions = _volume_model_permissions
    object_permissions = _volume_object_permissions

    class Meta:
        default_permissions = tuple(set(_volume_model_permissions + _volume_object_permissions))

    # The stack this volume belongs to
    stack = models.ForeignKey('stacks.Stack', related_name='volumes')

    # The hostname is used to match up volumes to hosts as they
    # come online.
    hostname = models.CharField('Hostname', max_length=64)

    # The host is the actual host this volume is attached to, but
    # it can only be assigned after the host is up and the volume is
    # actually attached
    host = models.ForeignKey('stacks.Host',
                             null=True,
                             on_delete=models.SET_NULL,
                             related_name='volumes')

    # the volume id as provided by the cloud provider. This can only
    # be populated after the volume has been created, thus allowing
    # blank values
    volume_id = models.CharField('Volume ID', max_length=32, blank=True)

    # when the last attach time for the volume was. This is also set
    # after the volume has been created
    attach_time = models.DateTimeField('Attach Time', default=None, null=True, blank=True)

    # the snapshot used when this volume is created. The size of the volume
    # is determined by the snapshot
    snapshot = models.ForeignKey('cloud.Snapshot')

    # the device id (e.g, /dev/sdb, dev/sdc, etc) the volume will assume when
    # it's attached to its host
    device = models.CharField('Device', max_length=32)

    # where on the machine should this volume be mounted?
    mount_point = models.CharField('Mount Point', max_length=255)

    def __unicode__(self):
        return '{0}'.format(self.volume_id)
