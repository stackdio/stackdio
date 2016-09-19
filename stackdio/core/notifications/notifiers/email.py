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

from django.conf import settings
from django.core import mail

from stackdio.core.notifications.notifiers import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """
    A notifier that sends emails.  If you prefer to send with a different email backend,
    just set the `email_backend` attribute to the dotted path to your backend class or
    override the `get_connection()` method to return an EmailBackend instance.
    """

    prefer_send_in_bulk = True

    # Override this to change how email is sent
    email_backend = settings.EMAIL_BACKEND

    def __init__(self, from_email):
        super(EmailNotifier, self).__init__()
        self.from_email = from_email

    @classmethod
    def get_required_options(cls):
        return [
            'email_address',
        ]

    def get_email_subject(self, notification):
        return notification.event.tag

    def get_email_body(self, notification):
        return notification.event.tag

    def get_email_message(self, notification):
        """
        Must return a django.core.mail.EmailMessage instance
        :param notification:
        :rtype: django.core.mail.EmailMessage
        :return: the email message
        """
        email_addr = self.get_option(notification, 'email_address')

        message = mail.EmailMessage(
            subject=self.get_email_subject(notification),
            body=self.get_email_body(notification),
            from_email=self.from_email,
            to=[email_addr],
            connection=self.get_connection(),
        )

        logger.debug('Sending email notification to {}'.format(', '.join(message.recipients())))

        return message

    def get_connection(self):
        """
        Return a django email backend instance.  Either override this or change the
        `email_backend` class attribute to change the mail backend.
        :return:
        """
        return mail.get_connection(backend=self.email_backend)

    def send_notification(self, notification):
        # Get the message
        message = self.get_email_message(notification)

        # This will open & close the connection automatically.
        num_sent = message.send()

        logger.debug('Successfully delivered {} message(s)'.format(num_sent))

        # Success means 1 email was sent.
        return num_sent == 1

    def send_notifications_in_bulk(self, notifications):
        successful_notifications = []

        logger.debug('Attempting to send {} notifications in bulk'.format(len(notifications)))

        # Send them all on the same connection object
        with self.get_connection() as conn:
            for notification in notifications:
                message = self.get_email_message(notification)

                # We need to call once for each message since we need to know which messages
                # sent successfully, not just the number of successfully sent messages.
                # This is still more efficient than calling send_notification() since we're
                # using a single connection object here.
                num_sent = conn.send_messages([message])

                # Add it to the success list
                if num_sent == 1:
                    successful_notifications.append(notification)

        logger.debug('Successfully delivered {} message(s)'.format(len(successful_notifications)))

        return successful_notifications
