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

from django.core.mail import send_mail

from stackdio.core.notifications.notifiers import BaseNotifier


class EmailNotifier(BaseNotifier):

    # prefer_send_in_bulk = True

    def __init__(self, send_from):
        super(EmailNotifier, self).__init__()
        self.send_from = send_from

    @classmethod
    def get_required_options(cls):
        return [
            'email_address',
        ]

    def send_notification(self, notification):
        email_addr = notification.handler.options.get('email_address')

        if email_addr is None:
            raise ValueError('Handler is missing email address')

        send_mail(notification.event, notification.event, self.send_from, [email_addr])

    # def send_notifications_in_bulk(self, notifications):
    #     pass
