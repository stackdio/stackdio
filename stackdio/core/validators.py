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
import re

from rest_framework.serializers import ValidationError

logger = logging.getLogger(__name__)

VALID_PROTOCOLS = ('tcp', 'udp', 'icmp')

HOSTNAME_REGEX = r'^[a-z0-9\-]+$'


class BaseValidator(object):
    """
    Used to set up some basic things useful for other validators
    """
    def __init__(self):
        super(BaseValidator, self).__init__()
        self.field = None
        self.serializer = None

    def set_context(self, serializer_field):
        self.field = serializer_field
        self.serializer = self.field.root

    def __call__(self, value):
        self.validate(value)

    def validate(self, value):
        raise NotImplementedError()


class CreateOnlyValidator(BaseValidator):
    """
    To be used on fields where the value can't be changed after the object has been created
    """
    def validate(self, value):
        if self.serializer.instance is not None:
            # This is an update request - this is not allowed, so we need to
            # raise a validation error
            raise ValidationError('This field may not be updated')


class PropertiesValidator(BaseValidator):
    """
    Make sure properties are a valid dict and that they don't contain `__stackdio__`
    """
    def validate(self, value):
        if not isinstance(value, dict):
            raise ValidationError({
                'properties': ['This field must be a JSON object.']
            })

        if '__stackdio__' in value:
            raise ValidationError({
                'properties': ['The `__stackdio__` key is reserved for system use.']
            })


class LabelValidator(BaseValidator):

    def validate(self, value):
        if ':' in value:
            raise ValidationError('This field may not contain the colon character `:`.')


def validate_hostname(value, raise_exception=False):
    errors = []

    if not re.match(HOSTNAME_REGEX, value):
        errors.append('May only contain lowercase letters, numbers, and hyphens.')

    if value[0] == '-' or value[-1] == '-':
        errors.append('May not start or end with a hyphen.')

    if errors and raise_exception:
        raise ValidationError(errors)

    return errors
