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
from unittest.util import safe_repr

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.test import TestCase
from guardian.shortcuts import assign_perm, remove_perm, get_perms
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIClient

logger = logging.getLogger(__name__)


def get_fake_request():
    django_request = HttpRequest()
    django_request.META['SERVER_NAME'] = 'localhost.localdomain'
    django_request.META['SERVER_PORT'] = 80

    return Request(django_request)


def group_has_perm(group, perm, obj=None):
    if obj:
        return perm in get_perms(group, obj)
    else:
        for gperm in group.permissions.all():
            if gperm.codename == perm:
                return True
        return False


class PermissionsMixin(object):
    permission_tests = {}

    @classmethod
    def _error_check_permissions(cls):
        # Error checking
        if not cls.permission_tests:
            # No tests, we'll just stop here - we don't want to fail
            return False

        if not isinstance(cls.permission_tests, dict):
            raise AssertionError('The `permission_tests` attribute must be a dict')

        if 'model' not in cls.permission_tests:
            raise AssertionError('You must specify a model to create an instance of')

        if 'endpoint' not in cls.permission_tests:
            raise AssertionError('You must specify an endpoint')

        # Things look OK
        return True

    def set_up_perms(self):
        # Create the object
        self.obj = self.permission_tests['model'](
            **self.permission_tests.get('create_data', {})
        )
        self.obj.save()

    def test_permissions(self):
        """
        Generic method to test permissions for each resource
        """
        if not self._error_check_permissions():
            # Just succeed immediately if necessary
            return

        self.client.login(username='test.user', password='1234')

        endpoint = self.permission_tests['endpoint'].format(self.obj.pk)

        # Iterate over the methods / permissions
        for perm_type in self.permission_tests['permission_types']:
            # Should fail now - no permission

            method = perm_type['method']

            response = getattr(self.client, method)(endpoint, perm_type.get('data', {}))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

            # Assign permission
            assign_perm(self.permission_tests['permission'] % perm_type['perm'],
                        self.user, self.obj)

            # Should work now - permission granted
            response = getattr(self.client, method)(endpoint, perm_type.get('data', {}))
            expected_code = perm_type.get('code', status.HTTP_200_OK)

            self.assertEqual(response.status_code, expected_code)

            # Remove permission
            remove_perm(self.permission_tests['permission'] % perm_type['perm'],
                        self.user, self.obj)

    def _add_admin_object_permission(self):
        endpoint = self.permission_tests['endpoint'].format(self.obj.pk)
        endpoint += 'permissions/users/'

        self.client.login(username='test.admin', password='1234')

        # Grant permissions to test.user via the API (but poorly - test to make sure
        # there is an array or perms)
        response = self.client.post(endpoint, {'user': 'test.user', 'permissions': 'admin'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Now actually grant permissions
        response = self.client.post(endpoint, {'user': 'test.user', 'permissions': ['admin']})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure the user now has admin permissions
        self.assertTrue(self.user.has_perm(self.permission_tests['permission'] % 'admin', self.obj))

        self.client.login(username='test.user', password='1234')

    def test_add_object_permissions(self):
        endpoint = self.permission_tests['endpoint'].format(self.obj.pk)
        endpoint += 'permissions/users/'

        self.client.login(username='test.user', password='1234')

        # Try hitting the user permissions endpoint
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Add admin permission
        self._add_admin_object_permission()

        # Now try again with permissions
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_object_permissions(self):
        orig_endpoint = self.permission_tests['endpoint'].format(self.obj.pk)
        endpoint = orig_endpoint + 'permissions/users/test.user/'

        self.client.login(username='test.user', password='1234')

        # Try hitting the user permissions endpoint
        response = self.client.put(endpoint, {'user': 'test.user', 'permissions': 'blah'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Add admin permission
        self._add_admin_object_permission()

        # Now try again with permissions, but try with an invalid permission
        response = self.client.put(endpoint, {'user': 'test.user', 'permissions': ['blah']})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Now try updating for real
        response = self.client.patch(endpoint, {'user': 'test.user', 'permissions': ['view']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.has_perm(self.permission_tests['permission'] % 'view', self.obj))

        # Try grabbing the object
        response = self.client.get(orig_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Make sure the endpoint properly shows the permissions
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['permissions'], ['admin', 'view'])


class StackdioTestCase(TestCase):
    """
    Base test case class for stackd.io.  We'll add a client object, and create an admin and a
    regular user.  We'll also create an 'everybody' group with permissions to view most of the
    endpoints.
    """

    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.get(username='test.user')
        self.admin = get_user_model().objects.get(username='test.admin')
        self.group = Group.objects.get(name='stackdio')
        self.user.groups.add(self.group)

        if hasattr(self, 'set_up_perms'):
            self.set_up_perms()

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        user_model.objects.create_superuser('test.admin', 'test.admin@stackd.io', '1234',
                                            first_name='Test', last_name='Admin')
        user_model.objects.create_user('test.user', 'test.user@stackd.io', '1234',
                                       first_name='Test', last_name='User')

        Group.objects.create(name='stackdio')

    def assertCallable(self, obj, msg=None):
        """Same as self.assertTrue(callable(obj)), with a nicer
        default message."""
        if not callable(obj):
            standardMsg = '%s is not callable' % (safe_repr(obj))
            self.fail(self._formatMessage(msg, standardMsg))
