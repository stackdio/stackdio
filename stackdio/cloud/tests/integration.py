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

from core.tests.utils import PermissionsMixin, StackdioTestCase
from cloud import models


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


class CloudProviderTestCase(StackdioTestCase, PermissionsMixin):
    """
    Tests for CloudProvider things
    """

    fixtures = (
        'cloud/fixtures/initial_data.json',
    )

    permission_tests = {
        'model': models.CloudProvider,
        'create_data': {
            'provider_type_id': 1,
            'title': 'test',
            'description': 'test',
            'account_id': 'blah',
            'vpc_id': 'vpc-blah',
            'region_id': 1,
        },
        'endpoint': '/api/providers/{0}/',
        'permission': 'cloud.%s_cloudprovider',
        'permission_types': [
            {
                'perm': 'view', 'method': 'get'
            },
            {
                'perm': 'update', 'method': 'patch', 'data': {'title': 'test2'}
            },
            {
                'perm': 'delete', 'method': 'delete', 'code': status.HTTP_204_NO_CONTENT
            },
        ]
    }

    def test_view_provider_as_admin(self):
        self.client.login(username='test.admin', password='1234')

        response = self.client.get('/api/providers/{0}/'.format(self.obj.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CloudProfileTestCase(StackdioTestCase, PermissionsMixin):
    """
    Tests for CloudProvider things
    """

    fixtures = (
        'cloud/fixtures/initial_data.json',
    )

    permission_tests = {
        'model': models.CloudProfile,
        'create_data': {
            'cloud_provider_id': 1,
            'title': 'test',
            'description': 'test',
            'image_id': 'blah',
            'default_instance_size_id': 1,
            'ssh_user': 'root',
        },
        'endpoint': '/api/profiles/{0}/',
        'permission': 'cloud.%s_cloudprofile',
        'permission_types': [
            {
                'perm': 'view', 'method': 'get'
            },
            {
                'perm': 'update', 'method': 'patch', 'data': {'title': 'test2'}
            },
            {
                'perm': 'delete', 'method': 'delete', 'code': status.HTTP_204_NO_CONTENT
            },
        ]
    }

    @classmethod
    def setUpTestData(cls):
        super(CloudProfileTestCase, cls).setUpTestData()
        models.CloudProvider.objects.create(**CloudProviderTestCase.permission_tests['create_data'])


# class CloudInstanceSizeTestCase(StackdioTestCase, PermissionsMixin):
#     """
#     Tests for CloudProvider things
#     """
#
#     fixtures = (
#         'cloud/fixtures/initial_data.json',
#     )
#
#     permission_tests = {
#         'model': models.CloudInstanceSize,
#         'create_data': {
#             'title': 'test',
#             'description': 'test',
#             'provider_type_id': 1,
#             'instance_id': 'blah',
#         },
#         'endpoint': '/api/instance_sizes/{0}/',
#         'permission': 'cloud.%s_cloudinstancesize',
#         'permission_types': [
#             {
#                 'perm': 'view', 'method': 'get'
#             },
#             {
#                 'perm': 'update', 'method': 'patch', 'data': {'title': 'test2'}
#             },
#             {
#                 'perm': 'delete', 'method': 'delete', 'code': status.HTTP_204_NO_CONTENT
#             },
#         ]
#     }
