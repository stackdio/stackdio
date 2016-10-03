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


from rest_framework.serializers import ValidationError

from . import models


class UniqueChannelValidator(object):
    """
    Validator that corresponds to `unique_together = (...)` on a model class.

    Should be applied to the serializer class, not to an individual field.
    """
    message = 'Must be a unique value.'

    def __init__(self, message=None):
        self.message = message or self.message

        # Give default values
        self.instance = None
        self.auth_object = None

    def set_context(self, serializer):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        # Determine the existing instance, if this is an update operation.
        self.instance = getattr(serializer, 'instance', None)
        self.auth_object = serializer.context.get('auth_object', None)

    def exclude_current_instance(self, queryset):
        """
        If an instance is being updated, then do not include
        that instance itself as a uniqueness conflict.
        """
        if self.instance is not None:
            return queryset.exclude(pk=self.instance.pk)
        return queryset

    def __call__(self, value):
        queryset = models.NotificationChannel.objects.filter(auth_object=self.auth_object)
        queryset = self.exclude_current_instance(queryset)

        if value is not None:
            try:
                queryset.get(name=value)
                raise ValidationError(self.message)
            except models.NotificationChannel.DoesNotExist:
                # Nothing exists with the new name, we're good
                pass


class UserChannelExistsValidator(object):

    message = 'No channel found with name={name}'

    def __init__(self, message=None):
        self.message = message or self.message

        # Give default values
        self.auth_object = None

    def set_context(self, serializer):
        self.auth_object = serializer.context.get('auth_object', None)

    def __call__(self, value):
        queryset = models.NotificationChannel.objects.filter(auth_object=self.auth_object)

        try:
            queryset.get(name=value)
        except models.NotificationChannel.DoesNotExist:
            raise ValidationError(self.message.format(name=value))
