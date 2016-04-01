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

from rest_framework import status

from stackdio.core.tests.utils import StackdioTestCase
from stackdio.core.utils import get_urls
from stackdio.api.urls import urlpatterns


class AuthenticationTestCase(StackdioTestCase):
    """
    Test all list endpoints to ensure they throw a permission denied when a user isn't logged in
    """

    # These don't allow get requests
    EXEMPT_ENDPOINTS = (
        '/api/user/password/',
    )

    PERMISSION_MODELS = (
        'blueprints',
        'formulas',
        'stacks',
        'volumes',
        'cloud/accounts',
        'cloud/images',
        'cloud/snapshots',
        'users',
        'groups',
    )

    PERMISSIONS_ENDPOINTS = (
        '/api/%s/permissions/users/',
        '/api/%s/permissions/groups/',
    )

    # These should be only visible by admins
    ADMIN_ONLY = []

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
            if '.*' in url:
                continue
            if 'login' in url or 'logout' in url:
                # We don't care about login / logout views
                continue
            if url.endswith('/permissions/'):
                continue
            if url.endswith('cloud/'):
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

    def test_404_endpoints(self):
        self.client.login(username='test.user', password='1234')

        for url in ('/api/blah', '/api/foobar/', '/api/blah/', '/api/stacks/permissions/foo'):
            for method in ('get', 'post', 'put', 'patch', 'delete', 'head', 'trace'):
                for accept in ('application/json', 'text/html'):
                    func = getattr(self.client, method)
                    response = func(url, HTTP_ACCEPT=accept)

                    self.assertEqual(
                        response.status_code,
                        status.HTTP_404_NOT_FOUND,
                        'URL {0} did not return a 404, it returned {1}'.format(url,
                                                                               response.status_code)
                    )

                    # For some reason response.content_type is None, so this should work
                    content_type = response._headers['content-type'][1]

                    self.assertIn(accept, content_type)
