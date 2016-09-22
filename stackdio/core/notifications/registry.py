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

from django.db.models.base import ModelBase
from rest_framework.serializers import BaseSerializer

from stackdio.core.config import StackdioConfigException

NotifiableModelConfig = namedtuple('NotifiableModelConfig', ['serializer_class'])


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

    def register(self, model_class, serializer_class):
        model_class = validate_model_class(model_class)
        serializer_class = validate_serializer_class(serializer_class)
        if model_class not in self:
            self[model_class] = NotifiableModelConfig(serializer_class)

registry = NotifiableModelRegistry()
register = registry.register
get = registry.get
