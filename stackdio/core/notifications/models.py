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

import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models

from stackdio.core.notifications.utils import get_notifier_class, get_notifier_instance

logger = logging.getLogger(__name__)


class SubscribedObjectProxy(models.Model):
    """
    A proxy for the many-to-many relation between channels and generic objects
    """
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()
    subscribed_object = GenericForeignKey()


class NotificationChannel(models.Model):
    """
    A channel that can receive events.  If an object is configured to route events to
    """
    name = models.CharField('Name', max_length=128)

    events = models.ManyToManyField('core.Event', related_name='channels')

    auth_object_content_type = models.ForeignKey('contenttypes.ContentType')
    auth_object_id = models.PositiveIntegerField()
    auth_object = GenericForeignKey('auth_object_content_type', 'auth_object_id')

    # The list of objects this channel is subscribed to
    subscribed_objects = models.ManyToManyField('notifications.SubscribedObjectProxy',
                                                related_name='channels')


class NotificationHandler(models.Model):
    """
    A handler tying a notifier implementation to it's configuration
    """

    notifier = models.CharField('Notifier', max_length=256)

    # metadata = models

    channel = models.ForeignKey('notifications.NotificationChannel', related_name='handlers')

    # the caching logic is done in the utils methods
    def get_nofifier_class(self):
        return get_notifier_class(self.notifier)

    def get_notifier_instance(self):
        return get_notifier_instance(self.notifier)


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

    def send(self):
        # logic to send this notification (presumably using the notifier
        pass
