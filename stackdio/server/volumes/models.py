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


import logging

from django.conf import settings
from django.db import models
from django.core.files.storage import FileSystemStorage

from django_extensions.db.models import (
    TimeStampedModel,
)

class Volume(TimeStampedModel):
    # The stack this volume belongs to
    stack = models.ForeignKey('stacks.Stack', related_name='volumes')

    # The hostname is used to match up volumes to hosts as they
    # come online.
    hostname = models.CharField(max_length=64)

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
    volume_id = models.CharField(max_length=32, blank=True)

    # when the last attach time for the volume was. This is also set
    # after the volume has been created
    attach_time = models.DateTimeField(default=None, null=True, blank=True)

    # the snapshot used when this volume is created. The size of the volume
    # is determined by the snapshot
    snapshot = models.ForeignKey('cloud.Snapshot')

    # the device id (e.g, /dev/sdj or /dev/sdk) the volume will assume when
    # it's attached to its host
    device = models.CharField(max_length=32)

    # where on the machine should this volume be mounted?
    mount_point = models.CharField(max_length=255)

    def __unicode__(self):
        return '{0}'.format(self.volume_id)

