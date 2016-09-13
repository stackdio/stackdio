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


class BaseNotifier(object):
    """
    Base class for all notifiers.
    Any overridden methods should NOT modify any Notification objects that are passed in.
    """

    # Set this to True if your notifier should have send_notifications_in_bulk() called instead
    # of send_notification().
    # Use this option if there is some overhead in starting up your notifier object that should
    # only be performed once before sending several notifications.
    prefer_send_in_bulk = False

    def __init__(self):
        super(BaseNotifier, self).__init__()

    def send_notification(self, notification):
        """
        Override this method with logic to send a single notification.  Should return False
        (or something False-y) if the notification fails to send, or True (or something Truth-y)
        if the notification sends successfully.
        :param notification: a stackdio.core.notifications.models.Notification object
        :rtype: bool
        :return: the success code
        """
        raise NotImplementedError()

    def send_notifications_in_bulk(self, notifications):
        """
        Optionally override this method to send multiple notifications in bulk.
        You probably also want to  set `prefer_send_in_bulk` to True on your class,
        so this method will actually get called.
        Should return a list of successfully sent Notification objects.  Any notifications
        not in the return list will be set to be retried at a later time.
        :param notifications: an iterable of stackdio.core.notifications.models.Notification objects
        :rtype: list
        :return: a list of successfully sent notifications
        """
        # provide a default implementation
        ret = []

        # Send each notification and add it to the list if it succeeds.
        for notification in notifications:
            if self.send_notification(notification):
                ret.append(notification)

        return ret
