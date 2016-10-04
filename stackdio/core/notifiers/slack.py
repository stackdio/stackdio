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
import time

import six
from django.conf import settings
from stackdio.core.config import StackdioConfigException
from stackdio.core.notifications import registry
from stackdio.core.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)


try:
    from slackclient import SlackClient
except ImportError:
    SlackClient = None


class SlackNotifier(BaseNotifier):

    needs_verification = False

    def __init__(self, slack_api_token, post_as_user=True):
        super(SlackNotifier, self).__init__()

        if SlackClient is None:
            raise StackdioConfigException('Could not load the slack client.  Be sure you have '
                                          'installed stackdio-server with the `slack` extra.  '
                                          '(pip install stackdio-server[slack])')

        self.slackclient = SlackClient(slack_api_token)
        self.post_as_user = post_as_user

    @classmethod
    def get_required_options(cls):
        return [
            'channel',
        ]

    def send_notification(self, notification):
        ui_url = registry.get_ui_url(notification.content_object)

        notification_text = 'Event {} triggered on {}'.format(notification.event.tag,
                                                              notification.content_object.title)

        fields = []

        health = getattr(notification.content_object, 'health')
        activity = getattr(notification.content_object, 'activity')

        if health is not None:
            fields.append({
                'title': 'Health',
                'value': health,
                'short': True,
            })

        if activity is not None:
            fields.append({
                'title': 'Activity',
                'value': activity or '-',
                'short': True,
            })

        chat_kwargs = {
            'channel': self.get_option(notification, 'channel'),
            'as_user': self.post_as_user,
            'attachments': [
                {
                    'fallback': notification_text,
                    'author_name': 'stackd.io',
                    'author_link': settings.STACKDIO_CONFIG.server_url,
                    'title': six.text_type(notification.content_object.title),
                    'title_link': ui_url,
                    'text': notification_text,
                    'fields': fields,
                    'ts': int(notification.created.strftime('%s')),
                }
            ]
        }
        time.time()

        result = self.slackclient.api_call('chat.postMessage', **chat_kwargs)

        return result['ok']
