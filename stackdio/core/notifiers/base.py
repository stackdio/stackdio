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

from abc import ABCMeta, abstractmethod

import six


NOTIFIER_REQUIRED_METHODS = (
    'get_required_options',
    'send_notification',
    'send_notifications_in_bulk',
    'needs_verification',
    'prefer_send_in_bulk',
    'split_group_notifications',
)


def _hasattr(klass, attr):
    try:
        return any(attr in superklass.__dict__ for superklass in klass.__mro__)
    except AttributeError:
        # Old-style class
        return hasattr(klass, attr)


def _has_all_attrs(klass, attr_list):
    return all(_hasattr(klass, attr) for attr in attr_list)


class BaseNotifier(six.with_metaclass(ABCMeta)):
    """
    Abstract Base class for all notifiers.
    Any overridden methods should NOT modify any Notification objects that are passed in.
    """

    # Set this to False if a handler with this notifier does not need to be verified
    # before sending notifications.
    needs_verification = True

    # Set this to True if your notifier should have send_notifications_in_bulk() called instead
    # of send_notification().
    # Use this option if there is some overhead in starting up your notifier object that should
    # only be performed once before sending several notifications.
    prefer_send_in_bulk = False

    # Set this to True if the notification system should generate one notification per user in
    # a group.  If set to True, it is guaranteed that the auth_object on every notification
    # passed in to your notifier will be a User object, otherwise you could get
    # a User or a Group. (useful when sending email)
    split_group_notifications = False

    def __init__(self):
        super(BaseNotifier, self).__init__()

    @classmethod
    def __subclasshook__(cls, subclass):
        """
        Allow any class that has all the required methods to be considered
        a subclass of BaseNotifier
        """
        if cls is BaseNotifier:
            if _has_all_attrs(subclass, NOTIFIER_REQUIRED_METHODS):
                return True
        return NotImplemented

    @classmethod
    def get_required_options(cls):
        """
        Override this method to get the required options for your handler instance
        :rtype: list
        :return: A list of required options
        """
        return []

    def get_option(self, notification, option):
        """
        Helper method to get an option value and raise an exception if it is required and missing.
        :param notification: the notification object
        :param option: the option to get the value for
        :return: the value of the option
        """
        value = notification.handler.options.get(option)

        if value is None and option in self.get_required_options():
            raise ValueError('Handler is missing a required option `{}`'.format(option))

        return value

    @abstractmethod
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
