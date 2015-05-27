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

from guardian.shortcuts import assign_perm
from rest_framework import status

from core.tests import StackdioTestCase
from . import models


logger = logging.getLogger(__name__)


class CloudProviderTypeTestCase(StackdioTestCase):
    """
    Tests for CloudProviderType things
    """

    def setUp(self):
        super(CloudProviderTypeTestCase, self).setUp()
        self.client.login(username='test.admin', password='1234')

    def test_create_provider_type(self):
        # No creation should be allowed via the API, neither as an admin or non
        response = self.client.post('/api/provider_types/', {'title': 'new'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try as non-admin
        self.client.logout()
        self.client.login(username='test.user', password='1234')

        response = self.client.post('/api/provider_types/', {'title': 'new'})
        # Should just be forbidden now
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CloudProviderTestCase(StackdioTestCase):
    """
    Tests for CloudProvider things
    """

    fixtures = (
        'cloud/fixtures/initial_data.json',
    )

    @classmethod
    def setUpTestData(cls):
        super(CloudProviderTestCase, cls).setUpTestData()

        models.CloudProvider.objects.create(
            provider_type_id=1,
            title='test',
            description='test',
            account_id='blah',
            vpc_id='vpc-blah',
            region_id=1,
        )

    def setUp(self):
        super(CloudProviderTestCase, self).setUp()
        self.provider = models.CloudProvider.objects.get(pk=1)

    def test_view_provider_as_admin(self):
        self.client.login(username='test.admin', password='1234')

        response = self.client.get('/api/providers/1/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_provider_as_non_admin(self):
        self.client.login(username='test.user', password='1234')

        # Should fail now - no permission
        response = self.client.get('/api/providers/1/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Assign permission
        assign_perm('cloud.view_cloudprovider', self.user, self.provider)

        # Should work now - permission granted
        response = self.client.get('/api/providers/1/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CloudProfileTestCase(StackdioTestCase):
    """
    Tests for CloudProfile things
    """
