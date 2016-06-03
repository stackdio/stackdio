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

import yaml
from rest_framework import status

from stackdio.core.tests.utils import PermissionsMixin, StackdioTestCase
from stackdio.api.cloud import models

logger = logging.getLogger(__name__)


class CloudProviderTestCase(StackdioTestCase):
    """
    Tests for CloudProvider things
    """

    def setUp(self):
        super(CloudProviderTestCase, self).setUp()
        self.client.login(username='test.admin', password='1234')

    def test_create_provider(self):
        # No creation should be allowed via the API, neither as an admin or non
        response = self.client.post('/api/cloud/providers/', {'title': 'new'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Try as non-admin
        self.client.logout()
        self.client.login(username='test.user', password='1234')

        response = self.client.post('/api/cloud/providers/', {'title': 'new'})
        # Should just be forbidden now
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CloudAccountTestCase(StackdioTestCase, PermissionsMixin):
    """
    Tests for CloudAccount things
    """

    permission_tests = {
        'model': models.CloudAccount,
        'create_data': {
            'provider_id': 1,
            'title': 'test',
            'description': 'test',
            'vpc_id': 'vpc-blah',
            'region_id': 1,
        },
        'endpoint': '/api/cloud/accounts/{0}/',
        'permission': 'cloud.%s_cloudaccount',
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

    def set_up_perms(self):
        super(CloudAccountTestCase, self).set_up_perms()

        # Generate the yaml and store in the database
        yaml_data = {
            self.obj.slug: {
                'securitygroupid': []
            }
        }
        self.obj.yaml = yaml.safe_dump(yaml_data, default_flow_style=False)
        self.obj.save()

        # Update the salt cloud providers file
        self.obj.update_config()

    def test_view_account_as_admin(self):
        self.client.login(username='test.admin', password='1234')

        response = self.client.get('/api/cloud/accounts/{0}/'.format(self.obj.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CloudImageTestCase(StackdioTestCase, PermissionsMixin):
    """
    Tests for CloudAccount things
    """

    permission_tests = {
        'model': models.CloudImage,
        'create_data': {
            'title': 'test',
            'description': 'test',
            'image_id': 'blah',
            'default_instance_size_id': 1,
            'ssh_user': 'root',
        },
        'endpoint': '/api/cloud/images/{0}/',
        'permission': 'cloud.%s_cloudimage',
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

    def set_up_perms(self):
        account = models.CloudAccount.objects.create(
            **CloudAccountTestCase.permission_tests['create_data']
        )
        self.obj = models.CloudImage.objects.create(account=account,
                                                    **self.permission_tests['create_data'])
