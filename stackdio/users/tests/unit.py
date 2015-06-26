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

import logging

from django.conf import settings
from rest_framework.serializers import ValidationError

from core.tests.utils import StackdioTestCase
from users import serializers

logger = logging.getLogger(__name__)


class UserSerializerTestCase(StackdioTestCase):

    def get_serializer(self):
        serializer = serializers.UserSerializer(self.user)
        return serializer

    def test_validate_ldap(self):
        serializer = self.get_serializer()

        # Preserver old setting
        old_ldap = settings.LDAP_ENABLED

        settings.LDAP_ENABLED = True

        attrs = {
            'username': 'test.user12',
            'first_name': 'TestF',
            'last_name': 'User',
            'email': 'test.user@stackd.io',
            'settings': {
                'public_key': 'lshdfsdlf'
            }
        }

        try:
            serializer.validate(attrs)
            raise AssertionError('`serializer.validate()` should have thrown a ValidationError')
        except ValidationError as e:
            self.assertIsInstance(e.detail, dict)
            self.assertIn('username', e.detail)
            self.assertIn('first_name', e.detail)
            self.assertNotIn('last_name', e.detail)
            self.assertNotIn('email', e.detail)
            self.assertNotIn('settings', e.detail)

        settings.LDAP_ENABLED = old_ldap

    def test_validate_no_ldap(self):
        serializer = self.get_serializer()

        # Preserver old setting
        old_ldap = settings.LDAP_ENABLED

        settings.LDAP_ENABLED = False

        attrs = {
            'username': 'test.user12',
            'first_name': 'TestF',
            'last_name': 'UserY',
            'email': 'test.ussder@stackd.io',
            'settings': {
                'public_key': 'lssdfhdfsdlf'
            }
        }

        try:
            new_attrs = serializer.validate(attrs)
            self.assertEqual(new_attrs, attrs)

        except ValidationError:
            raise AssertionError('`serializer.validate()` threw an exception, and shouldn\'t have')

        settings.LDAP_ENABLED = old_ldap
