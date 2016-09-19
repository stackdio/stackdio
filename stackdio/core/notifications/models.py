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

import json
import logging

import six
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from stackdio.core.notifications.utils import get_notifier_class, get_notifier_instance

logger = logging.getLogger(__name__)


@six.python_2_unicode_compatible
class SubscribedObjectProxy(models.Model):
    """
    A proxy for the many-to-many relation between channels and generic objects
    """
    class Meta:
        unique_together = ('content_type', 'object_id')

    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()
    subscribed_object = GenericForeignKey()

    def __str__(self):
        return six.text_type(self.subscribed_object)


class NotificationChannelQuerySet(models.QuerySet):

    def filter_on_auth_object(self, auth_object):
        """
        Get all the NotificationChannels for the given auth object.
        """
        ctype = ContentType.objects.get_for_model(auth_object)
        return self.filter(auth_object_content_type=ctype, auth_object_id=auth_object.id)


@six.python_2_unicode_compatible
class NotificationChannel(models.Model):
    """
    A channel that can receive events.  If an object is configured to route events to
    """
    class Meta:
        unique_together = ('name', 'auth_object_content_type', 'auth_object_id')

    name = models.CharField('Name', max_length=128)

    events = models.ManyToManyField('core.Event', related_name='channels')

    auth_object_content_type = models.ForeignKey('contenttypes.ContentType')
    auth_object_id = models.PositiveIntegerField()
    auth_object = GenericForeignKey('auth_object_content_type', 'auth_object_id')

    # The list of objects this channel is subscribed to
    subscribed_object_proxies = models.ManyToManyField('notifications.SubscribedObjectProxy',
                                                       related_name='channels')

    objects = NotificationChannelQuerySet.as_manager()

    def __str__(self):
        events = [six.text_type(event for event in self.events.all())]
        return 'Channel {}, subscribed to {}'.format(self.name, ', '.join(events))

    @property
    def subscribed_objects(self):
        proxies = self.subscribed_object_proxies.all()
        return [object_proxy.subscribed_object for object_proxy in proxies]

    def add_subscriber(self, subscriber):
        # Find the content type
        ctype = ContentType.objects.get_for_model(subscriber)

        # Grab the object proxy
        new_object_proxy, created = SubscribedObjectProxy.objects.get_or_create(
            content_type=ctype,
            object_id=subscriber.pk
        )

        # Add the proxy to the list of subscribed objects
        self.subscribed_object_proxies.add(new_object_proxy)


@six.python_2_unicode_compatible
class NotificationHandler(models.Model):
    """
    A handler tying a notifier implementation to it's configuration
    """

    notifier = models.CharField('Notifier', max_length=256)

    options_storage = models.TextField(default='{}')

    channel = models.ForeignKey('notifications.NotificationChannel', related_name='handlers')

    def __str__(self):
        return 'Handler {} on {}'.format(self.notifier, self.channel)

    def _get_options(self):
        if self.options_storage:
            return json.loads(self.options_storage)
        else:
            return {}

    def _set_options(self, options):
        self.options_storage = json.dumps(options)
        self.save()

    options = property(_get_options, _set_options)

    # the caching logic is done in the utils methods
    def get_notifier_class(self):
        return get_notifier_class(self.notifier)

    def get_notifier_instance(self):
        return get_notifier_instance(self.notifier)


@six.python_2_unicode_compatible
class Notification(models.Model):
    """
    A representation of a single notification to be sent
    """

    sent = models.BooleanField('Sent', default=False)

    event = models.ForeignKey('core.Event')

    handler = models.ForeignKey('notifications.NotificationHandler')

    # The associated object
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return 'Notification for {} sent using {} on object {}'.format(self.event,
                                                                       self.handler,
                                                                       self.content_object)

    def to_json(self):
        return {}
