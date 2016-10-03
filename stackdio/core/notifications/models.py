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

import logging

import six
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver
from django_extensions.db.models import TimeStampedModel
from stackdio.core.fields import JSONField
from stackdio.core.notifications.utils import get_notifier_class, get_notifier_instance

logger = logging.getLogger(__name__)


def get_auth_object_limit():
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split('.')
    user_q = models.Q(app_label=user_app_label, model=user_model_name)
    group_q = models.Q(app_label='auth', model='Group')

    return user_q | group_q


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

    def filter(self, *args, **kwargs):
        """
        Add the ability to filter on the auth_object or subscribed_object
        """
        auth_object = kwargs.pop('auth_object', None)

        if auth_object is not None:
            ctype = ContentType.objects.get_for_model(auth_object)
            kwargs['auth_object_content_type'] = ctype
            kwargs['auth_object_id'] = auth_object.pk

        subscribed_object = kwargs.pop('subscribed_object', None)

        if subscribed_object is not None:
            ctype = ContentType.objects.get_for_model(subscribed_object)
            proxies = SubscribedObjectProxy.objects.filter(content_type=ctype,
                                                           object_id=subscribed_object.pk)
            kwargs['subscribed_object_proxies__in'] = proxies

        return super(NotificationChannelQuerySet, self).filter(*args, **kwargs)


@six.python_2_unicode_compatible
class NotificationChannel(models.Model):
    """
    A channel that can receive events.  If an object is configured to route events to
    """
    class Meta:
        unique_together = ('name', 'auth_object_content_type', 'auth_object_id')

    name = models.CharField('Name', max_length=128)

    events = models.ManyToManyField('core.Event', related_name='channels')

    auth_object_content_type = models.ForeignKey('contenttypes.ContentType',
                                                 limit_choices_to=get_auth_object_limit())
    auth_object_id = models.PositiveIntegerField()
    auth_object = GenericForeignKey('auth_object_content_type', 'auth_object_id')

    # The list of objects this channel is subscribed to
    subscribed_object_proxies = models.ManyToManyField('notifications.SubscribedObjectProxy',
                                                       related_name='channels')

    objects = NotificationChannelQuerySet.as_manager()

    def __str__(self):
        events = [six.text_type(event) for event in self.events.all()]
        return six.text_type('Channel {}, subscribed to {}'.format(self.name, ', '.join(events)))

    @property
    def subscribed_objects(self):
        proxies = self.subscribed_object_proxies.all()
        return [object_proxy.subscribed_object for object_proxy in proxies]

    def add_subscriber(self, subscriber):
        # Find the content type
        ctype = ContentType.objects.get_for_model(subscriber)

        # Grab the object proxy
        new_object_proxy, _ = SubscribedObjectProxy.objects.get_or_create(
            content_type=ctype,
            object_id=subscriber.pk
        )

        # Add the proxy to the list of subscribed objects
        self.subscribed_object_proxies.add(new_object_proxy)

    def remove_subscriber(self, subscriber):
        # Find the content type
        ctype = ContentType.objects.get_for_model(subscriber)

        # Grab the object proxy
        try:
            object_proxy = SubscribedObjectProxy.objects.get(
                content_type=ctype,
                object_id=subscriber.pk
            )
        except SubscribedObjectProxy.DoesNotExist:
            # if the proxy doesn't exist, we don't need to do anything else
            return

        # Otherwise remove the proxy
        self.subscribed_object_proxies.remove(object_proxy)


@receiver(models.signals.m2m_changed, sender=NotificationChannel.subscribed_object_proxies.through)
def delete_empty_proxies(sender, instance, action, reverse, pk_set, **kwargs):
    """
    Use this method to ensure emtpy proxies are cleaned up.
    """
    # if the action isn't post_remove, we don't care about it
    if action != 'post_remove':
        return

    # Find the proxies, how to find them depends on if this was triggered from
    # the reverse relation or not
    if reverse:
        # reverse relation
        # i.e. subscribed_object_proxy.channels.remove(channel)
        proxies = [instance]
    else:
        # forward relation
        # i.e. channel.subscribed_object_proxies.remove(subscribed_object_proxy, ...)
        # OR  channel.remove_subscriber(subscribed_object)
        proxies = SubscribedObjectProxy.objects.filter(pk__in=pk_set)

    # Delete the proxies with no channels left
    for proxy in proxies:
        if proxy.channels.count() == 0:
            proxy.delete()


@six.python_2_unicode_compatible
class NotificationHandler(models.Model):
    """
    A handler tying a notifier implementation to it's configuration
    """

    notifier = models.CharField('Notifier', max_length=256)

    options = JSONField('Options')

    channel = models.ForeignKey('notifications.NotificationChannel', related_name='handlers')

    # Some notifiers might need to be verified before we can send notifications using them
    verified = models.BooleanField('Verified', default=False)

    # If too many notifications fail to send, we'll disable the handler.
    disabled = models.BooleanField('Disabled', default=False)

    def __str__(self):
        return six.text_type('Handler {} on {}'.format(self.notifier, self.channel))

    # the caching logic is done in the utils methods
    def get_notifier_class(self):
        return get_notifier_class(self.notifier)

    def get_notifier_instance(self):
        return get_notifier_instance(self.notifier)


@six.python_2_unicode_compatible
class Notification(TimeStampedModel):
    """
    A representation of a single notification to be sent
    """

    sent = models.BooleanField('Sent', default=False)

    failed_count = models.PositiveIntegerField('Failed Count', default=0)

    event = models.ForeignKey('core.Event')

    handler = models.ForeignKey('notifications.NotificationHandler')

    # The associated object
    content_type = models.ForeignKey('contenttypes.ContentType',
                                     related_name='+')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    # The associated user - channels can have users or groups - but we want the ability to
    # split a channel group up into several notifications associated with a single user.
    auth_object_content_type = models.ForeignKey('contenttypes.ContentType',
                                                 limit_choices_to=get_auth_object_limit(),
                                                 related_name='+')
    auth_object_id = models.PositiveIntegerField()
    auth_object = GenericForeignKey('auth_object_content_type', 'auth_object_id')

    def __str__(self):
        return six.text_type('Notification for {} sent using {} on object {}'.format(
            self.event,
            self.handler,
            self.content_object
        ))
