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

from django.conf import settings
from django.http import HttpRequest
from rest_framework.request import Request
from rest_framework.serializers import ValidationError

from stackdio.core.tests.utils import StackdioTestCase, get_fake_request
from stackdio.api.users import serializers

logger = logging.getLogger(__name__)


class UserSerializerTestCase(StackdioTestCase):

    def setUp(self):
        super(UserSerializerTestCase, self).setUp()
        self.ldap_orig = settings.LDAP_ENABLED

    def get_serializer(self):
        serializer = serializers.UserSerializer(
            self.user,
            context={'request': Request(HttpRequest())}
        )
        return serializer

    def test_validate_ldap(self):
        serializer = self.get_serializer()

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

        settings.LDAP_ENABLED = self.ldap_orig

    def test_validate_no_ldap(self):
        serializer = self.get_serializer()

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

        settings.LDAP_ENABLED = self.ldap_orig

    def test_update(self):
        settings.LDAP_ENABLED = False

        serializer = self.get_serializer()

        validated_data = {
            'username': 'test.user12',
            'first_name': 'TestF',
            'last_name': 'UserY',
            'superuser': True,
            'email': 'test.ussder@stackd.io',
            'settings': {
                'public_key': 'lssdfhdfsdlf'
            }
        }

        instance = serializer.update(self.user, validated_data)

        self.assertEqual(instance.username, 'test.user12')
        self.assertEqual(instance.first_name, 'TestF')
        self.assertEqual(instance.last_name, 'UserY')
        self.assertEqual(instance.email, 'test.ussder@stackd.io')
        self.assertEqual(instance.is_superuser, False)

        self.assertEqual(instance.settings.public_key, 'lssdfhdfsdlf')

        settings.LDAP_ENABLED = self.ldap_orig


class ChangePasswordSerializerTestCase(StackdioTestCase):

    def setUp(self):
        super(ChangePasswordSerializerTestCase, self).setUp()
        self.ldap_orig = settings.LDAP_ENABLED

    def get_serializer(self, **kwargs):
        context = {
            'request': get_fake_request()
        }

        serializer = serializers.ChangePasswordSerializer(self.user, context=context, **kwargs)
        return serializer

    def test_to_representation(self):
        serializer = self.get_serializer()

        user_dict = serializer.to_representation(serializer.instance)

        self.assertIsInstance(user_dict, dict)

        self.assertIn('username', user_dict)
        self.assertIn('first_name', user_dict)
        self.assertIn('last_name', user_dict)
        self.assertIn('email', user_dict)
        self.assertIn('settings', user_dict)

    def test_validate_ldap(self):
        serializer = self.get_serializer()

        settings.LDAP_ENABLED = True

        attrs = {
            'current_password': '1234',
            'new_password': 'blah',
        }

        self.assertRaises(ValidationError, serializer.validate, attrs)

        settings.LDAP_ENABLED = self.ldap_orig

    def test_validate_no_ldap(self):
        serializer = self.get_serializer()

        settings.LDAP_ENABLED = False

        attrs = {
            'current_password': 'blah',
            'new_password1': 'blah',
            'new_password2': 'blahg',
        }

        # Try with a bad password first
        try:
            serializer.validate(attrs)
            raise AssertionError('`serializer.validate()` should have thrown a ValidationError')
        except ValidationError as e:
            self.assertIn('current_password', e.detail)

        # Fix the password
        attrs['current_password'] = '1234'

        # Try with non-matching passwords
        try:
            serializer.validate(attrs)
            raise AssertionError('`serializer.validate()` should have thrown a ValidationError')
        except ValidationError as e:
            self.assertIn('new_password2', e.detail)

        # Fix the password, now everything should validate correctly
        attrs['new_password2'] = 'blah'

        try:
            new_attrs = serializer.validate(attrs)
            self.assertEqual(new_attrs, attrs)

        except ValidationError:
            raise AssertionError('`serializer.validate()` threw an exception, and shouldn\'t have')

        settings.LDAP_ENABLED = self.ldap_orig

    def test_save(self):
        # This will fail if this isn't false
        settings.LDAP_ENABLED = False

        data = {
            'current_password': '1234',
            'new_password1': 'blah',
            'new_password2': 'blah',
        }

        serializer = self.get_serializer(data=data)

        # Ensure the save() method fails if is_valid() hasn't been called
        self.assertRaises(AssertionError, serializer.save)

        serializer.is_valid()

        new_user = serializer.save()

        # Make sure the new password is set
        self.assertTrue(new_user.check_password('blah'))

        settings.LDAP_ENABLED = self.ldap_orig
