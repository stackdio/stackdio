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
from django.http.request import HttpRequest
from django.utils.encoding import iri_to_uri
from rest_framework.request import Request
from six.moves.urllib_parse import urljoin, urlsplit  # pylint: disable=import-error

from stackdio.core.notifications import registry
from stackdio.core.notifiers.base import BaseNotifier


class DummyRequest(Request):

    def __init__(self, prod_url):
        super(DummyRequest, self).__init__(HttpRequest())
        self.prod_url = prod_url

    def build_absolute_uri(self, location=None):
        if location is None:
            return None

        bits = urlsplit(location)
        if not (bits.scheme and bits.netloc):
            location = urljoin(self.prod_url, location)
        return iri_to_uri(location)


class WebhookNotifier(BaseNotifier):
    """
    A basic webhook notifier.  Takes a single timeout parameter.
    """

    def __init__(self, prod_url, default_method='POST', timeout=30):
        super(WebhookNotifier, self).__init__()
        self.default_method = default_method
        self.timeout = timeout
        from stackdio.core.notifications.serializers import AbstractNotificationSerializer
        self.abstract_serializer_class = AbstractNotificationSerializer
        self.serializer_context = {
            'request': DummyRequest(prod_url),
        }

    @classmethod
    def get_required_options(cls):
        return [
            'url',
        ]

    def get_request_data(self, notification):
        registry_config = registry.get(notification.content_type.model_class())

        class NotificationSerializer(self.abstract_serializer_class):

            object = registry_config.serializer_class(source='content_object')

        return NotificationSerializer(notification, context=self.serializer_context).data

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
