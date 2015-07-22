# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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

from rest_framework.fields import SkipField
from rest_framework.serializers import ValidationError

VALID_PROTOCOLS = ('tcp', 'udp', 'icmp')


class ValidationErrors(object):
    REQUIRED_FIELD = 'Required field.'
    BOOLEAN_REQUIRED = 'Boolean type required.'
    OBJECT_REQUIRED = 'Object type required.'
    LIST_REQUIRED = 'List type required.'
    INT_REQUIRED = 'Non-negative integer required.'
    STRING_REQUIRED = 'String required.'
    DECIMAL_REQUIRED = 'Non-negative decimal value required.'

    DUP_BLUEPRINT = 'A Blueprint with this value already exists.'
    DUP_HOST_TITLE = 'Duplicate title. Each host title must be unique.'
    MULTIPLE_COMPONENTS = 'Multiple components found.'

    STACKDIO_RESTRICTED_KEY = ('The __stackdio__ key is reserved for '
                               'system use.')

    DOES_NOT_EXIST = 'Object does not exist.'
    INVALID_INT = 'Value could not be converted to an integer.'
    MIN_HOSTS = 'Must have at least one host.'
    MIN_ONE = 'Must be greater than zero.'

    UNHANDLED_ERROR = 'An unhandled error occurred.'


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
