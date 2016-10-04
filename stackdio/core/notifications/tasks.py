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
from collections import defaultdict

from celery import shared_task
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from stackdio.core.models import Event
from . import models, utils

logger = logging.getLogger(__name__)


class NotificationTaskException(Exception):
    pass


def generate_notification_tasks(notifications):
    notifier_notification_map = defaultdict(list)

    for notification in notifications:
        notifier_notification_map[notification.handler.notifier].append(notification.id)

    for notifier_name, notification_ids in notifier_notification_map.items():
        if utils.get_notifier_class(notifier_name).prefer_send_in_bulk:
            # Bulk is supported - only 1 task per handler
            send_bulk_notifications.si(notifier_name, notification_ids).apply_async()
        else:
            # No bulk support, separate task for each notification
            for notification_id in notification_ids:
                send_notification.si(notification_id).apply_async()


@shared_task(name='notifications.generate_notifications')
def generate_notifications(event_tag, object_id, content_type_id):

    try:
        event = Event.objects.get(tag=event_tag)
    except Event.DoesNotExist:
        raise NotificationTaskException('Event with tag `{}` does not exist.'.format(event_tag))

    try:
        content_type = ContentType.objects.get_for_id(content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
    except ObjectDoesNotExist:
        raise NotificationTaskException('Failed to look up content object.')

    new_notifications = []

    subscribed_channels = models.NotificationChannel.objects.filter(
        subscribed_object=content_object,
        events=event,
    )

    for channel in subscribed_channels:
        auth_object = channel.auth_object

        # We only care about the handlers that are both verified and enabled
        for handler in channel.handlers.filter(verified=True, disabled=False):
            if utils.get_notifier_class(handler.notifier).split_group_notifications:
                if isinstance(auth_object, get_user_model()):
                    auth_objects = [auth_object]
                elif isinstance(auth_object, Group):
                    auth_objects = auth_object.user_set.all()
                else:
                    raise TypeError('Channel has an auth_object that isn\'t a User or Group.')
            else:
                auth_objects = [auth_object]

            for auth_obj in auth_objects:
                # Create the notification object
                notification = models.Notification.objects.create(event=event,
                                                                  handler=handler,
                                                                  auth_object=auth_obj,
                                                                  content_object=content_object)

                new_notifications.append(notification)

    # start up the tasks
    generate_notification_tasks(new_notifications)


@shared_task(name='notifications.resend_failed_notifications')
def resend_failed_notifications():
    # We only care about notifications that failed and we've retried less than 5 times
    failed_notifications = models.Notification.objects.filter(sent=False, failed_count__lte=5)

    # start up the tasks
    generate_notification_tasks(failed_notifications)


@shared_task(name='notifications.send_notification')
def send_notification(notification_id):
    try:
        notification = models.Notification.objects.get(id=notification_id)
    except models.Notification.DoesNotExist:
        raise NotificationTaskException('Could not find notification '
                                        'with id={}'.format(notification_id))

    notifier = notification.handler.get_notifier_instance()

    try:
        result = notifier.send_notification(notification)
    except Exception as e:
        notification.sent = False
        notification.failed_count += 1
        notification.save()
        logger.exception(e)
        raise NotificationTaskException('An exception occurred while sending a notification.')

    # Report that the notification sent properly
    if result:
        notification.sent = True
    else:
        notification.sent = False
        notification.failed_count += 1

    notification.save()

    # Disable the handler if we fail too many times
    if notification.failed_count > 5:
        notification.handler.disabled = True
        notification.handler.save()


@shared_task(name='notifications.send_bulk_notifications')
def send_bulk_notifications(notifier_name, notification_ids):
    notifier = utils.get_notifier_instance(notifier_name)

    notifications = models.Notification.objects.filter(id__in=notification_ids)

    # Need to pass in a list, not a QuerySet
    successful_notifications = notifier.send_notifications_in_bulk(list(notifications))

    successful_ids = [n.id for n in successful_notifications]

    # Report that the notifications sent properly
    for notification in notifications.filter(id__in=successful_ids):
        notification.sent = True
        notification.save()

    # Report that any other notifications failed
    for notification in notifications.exclude(id__in=successful_ids):
        notification.sent = False
        notification.failed_count += 1
        notification.save()
