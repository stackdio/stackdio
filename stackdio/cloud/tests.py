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

from rest_framework import status

from core.tests import StackdioTestCase


logger = logging.getLogger(__name__)


class CloudProviderTypeTestCase(StackdioTestCase):

    def setUp(self):
        super(CloudProviderTypeTestCase, self).setUp()
        self.client.login(username='test.admin', password='1234')

    def test_authenticated(self):
        # Ensure we are logged out before we try the first request
        self.client.logout()
        response = self.client.get('/api/provider_types/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Non - admins shouldn't be able to see this endpoint
        self.client.login(username='test.user', password='1234')
        response = self.client.get('/api/provider_types/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_provider_types(self):
        # Admins SHOULD be able to see this endpoint
        response = self.client.get('/api/provider_types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_provider_type(self):
        response = self.client.post('/api/provider_types/', {'title': 'new'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class CloudProviderTestCase(StackdioTestCase):

    def setUp(self):
        super(CloudProviderTestCase, self).setUp()
        self.client.login(username='test.admin', password='1234')
