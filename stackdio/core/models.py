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

from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models


class Label(models.Model):
    """
    Allows us to add arbitrary key/value pairs to any object
    """

    class Meta:
        unique_together = ('content_type', 'object_id', 'key')

    # the key
    key = models.CharField('Key', max_length=255)

    # the value
    value = models.CharField('Value', max_length=255, null=True)

    # the labeled object
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
