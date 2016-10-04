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

from functools import reduce
from operator import or_

import six
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.cache import cache
from django.db import models
from django.db.models import Q
from django.dispatch import receiver


class SearchQuerySet(models.QuerySet):
    searchable_fields = ()

    def search(self, query):
        # Put together the Q args
        q_objs = [Q(**{'%s__icontains' % field: query}) for field in self.searchable_fields]
        qset = reduce(or_, q_objs)

        return self.filter(qset).distinct()


@six.python_2_unicode_compatible
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

    def __str__(self):
        return six.text_type('{}:{} on {}'.format(self.key, self.value, self.content_object))


@six.python_2_unicode_compatible
class Event(models.Model):
    """
    An event that can be generated.
    """
    tag = models.CharField('Tag', max_length=128, unique=True)

    def __str__(self):
        return six.text_type(self.tag)


@receiver([models.signals.post_save, models.signals.post_delete], sender=Label)
def label_post_save(sender, **kwargs):
    label = kwargs.pop('instance')

    # Delete from the cache
    cache_key = '{}-{}-label-list'.format(label.content_type_id, label.object_id)
    cache.delete(cache_key)
