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

import six
from django.conf import settings
from stackdio.core.config import StackdioConfigException
from stackdio.core.notifications import registry
from stackdio.core.notifiers.base import BaseNotifier

logger = logging.getLogger(__name__)


try:
    from slackclient import SlackClient
except ImportError as e:
    logger.exception(e)
    raise StackdioConfigException('Could not load the slack client.  Be sure you have '
                                  'installed stackdio-server with the `slack` extra.  '
                                  '(pip install stackdio-server[slack])')


class SlackNotifier(BaseNotifier):

    def __init__(self, slack_api_token, post_as_user=True):
        super(SlackNotifier, self).__init__()
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
                    'fields': [
                        {
                            'title': 'Health',
                            'value': notification.content_object.health,
                            'short': True
                        },
                        {
                            'title': 'Activity',
                            'value': notification.content_object.activity,
                            'short': True
                        },
                    ],
                    'footer': 'sent from stackd.io',
                    # 'ts': 123456789  # TODO add the notification timestamp
                }
            ]
        }

        result = self.slackclient.api_call('chat.postMessage', **chat_kwargs)

        return result['ok']
