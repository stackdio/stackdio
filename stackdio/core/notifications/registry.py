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

from collections import namedtuple

from django.conf import settings
from django.db.models.base import ModelBase
from django.http.request import HttpRequest
from django.utils.encoding import iri_to_uri
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework.serializers import BaseSerializer
from six.moves.urllib_parse import urljoin, urlsplit  # pylint: disable=import-error

from stackdio.core.config import StackdioConfigException

NotifiableModelConfig = namedtuple('NotifiableModelConfig', ['serializer_class', 'url_name'])


class DummyRequest(HttpRequest):

    def __init__(self, prod_url):
        super(DummyRequest, self).__init__()
        self.prod_url = prod_url

    def build_absolute_uri(self, location=None):
        if location is None:
            return None

        bits = urlsplit(location)
        if not (bits.scheme and bits.netloc):
            location = urljoin(self.prod_url, location)
        return iri_to_uri(location)


def validate_model_class(model_class):
    if not isinstance(model_class, ModelBase):
        raise StackdioConfigException(
            'Object %r is not a Model class.' % model_class)
    if model_class._meta.abstract:
        raise StackdioConfigException(
            'The model %r is abstract, so it cannot be registered with '
            'actstream.' % model_class)
    if not model_class._meta.installed:
        raise StackdioConfigException(
            'The model %r is not installed, please put the app "%s" in your '
            'INSTALLED_APPS setting.' % (model_class,
                                         model_class._meta.app_label))
    return model_class


def validate_serializer_class(serializer_class):
    if not issubclass(serializer_class, BaseSerializer):
        raise StackdioConfigException(
            'Object %r is not a Serializer class.' % serializer_class)
    return serializer_class


class NotifiableModelRegistry(dict):

    serializer_context = {
        'request': Request(DummyRequest(settings.STACKDIO_CONFIG.server_url)),
    }

    def register(self, model_class, serializer_class, url_name):
        model_class = validate_model_class(model_class)
        serializer_class = validate_serializer_class(serializer_class)
        if model_class not in self:
            self[model_class] = NotifiableModelConfig(serializer_class, url_name)

    def get_notification_serializer(self, notification):
        from stackdio.core.notifications.serializers import AbstractNotificationSerializer

        model_class = notification.content_type.model_class()

        object_serializer_class = self.get_model_serializer_class(model_class)

        # Create a dynamic class that has the object set to the appropriate serializer
        class NotificationSerializer(AbstractNotificationSerializer):

            object = object_serializer_class(source='content_object')

        return NotificationSerializer(notification, context=self.serializer_context)

    def get_model_serializer_class(self, model_class):
        if model_class not in self:
            raise StackdioConfigException('Model %r is not registered with the '
                                          'notification registry.' % model_class)
        return self[model_class].serializer_class

    def get_object_serializer(self, content_object):
        serializer_class = self.get_model_serializer_class(content_object._meta.model)
        return serializer_class(content_object, context=self.serializer_context)

    def get_ui_url(self, content_object):
        model_class = content_object._meta.model
        if model_class not in self:
            raise StackdioConfigException('Model %r is not registered with the '
                                          'notification registry.' % model_class)

        url_name = self[model_class].url_name
        return reverse(url_name,
                       request=self.serializer_context['request'],
                       kwargs={'pk': content_object.pk})


registry = NotifiableModelRegistry()
register = registry.register
get_notification_serializer = registry.get_notification_serializer
get_object_serializer = registry.get_object_serializer
get_ui_url = registry.get_ui_url
