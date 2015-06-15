# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging

from django.contrib.auth import get_user_model
from django.test import TestCase
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework import status
from rest_framework.test import APIClient

from api_v1.urls import urlpatterns
from .utils import get_urls


logger = logging.getLogger(__name__)


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
        self.obj = self.permission_tests['model'].objects.create(
            **self.permission_tests.get('create_data', {})
        )

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

        if hasattr(self, 'set_up_perms'):
            self.set_up_perms()

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        user_model.objects.create_superuser('test.admin',
                                            'test.admin@stackd.io', '1234')
        user_model.objects.create_user('test.user',
                                       'test.user@stackd.io', '1234')


class AuthenticationTestCase(StackdioTestCase):
    """
    Test all list endpoints to ensure they throw a permission denied when a user isn't logged in
    """

    # These don't allow get requests
    EXEMPT_ENDPOINTS = (
        '/api/settings/change_password/',
    )

    PERMISSION_MODELS = (
        'blueprints',
        'formulas',
        'stacks',
        'volumes',
        'providers',
        'profiles',
        'snapshots',
    )

    PERMISSIONS_ENDPOINTS = (
        '/api/%s/permissions/users/',
        '/api/%s/permissions/groups/',
    )

    # These should be only visible by admins
    ADMIN_ONLY = [
        '/api/users/',
        '/api/provider_types/',
        '/api/instance_sizes/',
        '/api/regions/',
        '/api/zones/',
    ]

    def setUp(self):
        super(AuthenticationTestCase, self).setUp()

        # Build up a list of all list endpoints

        # Start out with just the root endpoint
        self.list_endpoints = ['/api/']

        for url in list(get_urls(urlpatterns)):
            # Filter out the urls with format things in them
            if not url:
                continue
            if 'format' in url:
                continue
            if '(?P<' in url:
                continue
            if url.endswith('/permissions/'):
                continue

            self.list_endpoints.append('/api/' + url)

        # Dynamically update the admin only endpoints
        for model in self.PERMISSION_MODELS:
            for url in self.PERMISSIONS_ENDPOINTS:
                self.ADMIN_ONLY.append(url % model)

    def test_permission_denied(self):
        for url in self.list_endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_success_admin(self):
        self.client.login(username='test.admin', password='1234')

        for url in self.list_endpoints:
            response = self.client.get(url)
            expected = status.HTTP_200_OK
            if url in self.EXEMPT_ENDPOINTS:
                expected = status.HTTP_405_METHOD_NOT_ALLOWED

            self.assertEqual(response.status_code, expected, 'URL {0} failed'.format(url))

    def test_success_non_admin(self):
        self.client.login(username='test.user', password='1234')

        for url in self.list_endpoints:
            response = self.client.get(url)
            expected = status.HTTP_200_OK
            if url in self.EXEMPT_ENDPOINTS:
                expected = status.HTTP_405_METHOD_NOT_ALLOWED
            elif url in self.ADMIN_ONLY:
                expected = status.HTTP_403_FORBIDDEN

            self.assertEqual(response.status_code, expected,
                             'URL {0} failed.  Expected {1}, was {2}.'.format(url,
                                                                              expected,
                                                                              response.status_code))
