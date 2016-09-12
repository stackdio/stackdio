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

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from stackdio.core.models import Event
from . import models, utils


class NotificationsTaskException(Exception):
    pass


@shared_task(name='notifications.generate_notifications')
def generate_notifications(event_tag, object_id, content_type_id):

    try:
        event = Event.objects.get(tag=event_tag)
    except Event.DoesNotExist:
        raise NotificationsTaskException('Event with tag `{}` does not exist.'.format(event_tag))

    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
    except ObjectDoesNotExist:
        raise NotificationsTaskException('Failed to look up content object.')

    notifier_notification_map = {}

    for channel in event.channels.all():
        for handler in channel.handlers.all():
            # Create the notification object
            notification = models.Notification.objects.create(event=event,
                                                              handler=handler,
                                                              content_object=content_object)

            notifier_notification_map.setdefault(handler.notifier, []).append(notification.id)

    for notifier_name, notification_ids in notifier_notification_map.items():
        if utils.get_notifier_class(notifier_name).can_send_in_bulk:
            # Bulk is supported - only 1 task per handler
            send_bulk_notifications.apply_async(notifier_name, notification_ids)
        else:
            # No bulk support, separate task for each notification
            for notification_id in notification_ids:
                send_notification.apply_async(notification_id)


@shared_task(name='notifications.send_notification')
def send_notification(notification_id):
    try:
        notification = models.Notification.objects.get(id=notification_id)
    except models.Notification.DoesNotExist:
        raise NotificationsTaskException('Could not find notification '
                                         'with id={}'.format(notification_id))

    notifier = notification.handler.get_notifier_instance()

    result = notifier.send_notification(notification)

    # Report that the notification sent properly
    if result:
        notification.sent = True
        notification.save()


@shared_task(name='notifications.send_bulk_notifications')
def send_bulk_notifications(notifier_name, notification_ids):
    notifier = utils.get_notifier_instance(notifier_name)

    notifications = list(models.Notification.objects.filter(id__in=notification_ids))

    successful_notifications = notifier.send_notifications_in_bulk(notifications)

    # Report that the notifications sent properly
    for notification in successful_notifications:
        notification.sent = True
        notification.save()
