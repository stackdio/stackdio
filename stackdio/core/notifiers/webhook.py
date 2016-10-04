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

import requests

from stackdio.core.notifications import registry
from stackdio.core.notifiers.base import BaseNotifier


class WebhookNotifier(BaseNotifier):
    """
    A basic webhook notifier.  Takes a single timeout parameter.
    """

    needs_verification = False

    def __init__(self, default_method='POST', timeout=30):
        super(WebhookNotifier, self).__init__()
        self.default_method = default_method
        self.timeout = timeout

    @classmethod
    def get_required_options(cls):
        return [
            'url',
        ]

    def get_request_data(self, notification):
        return registry.get_notification_serializer(notification).data

    def send_notification(self, notification):
        # just post to a URL
        url = self.get_option(notification, 'url')

        # Grab the request method
        method = self.get_option(notification, 'method') or self.default_method

        r = requests.request(
            method,
            url,
            json=self.get_request_data(notification),
            timeout=self.timeout,
        )

        # define a failure as a non-200 response
        return r.status_code == 200
