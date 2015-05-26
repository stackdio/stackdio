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


"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import logging

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


logger = logging.getLogger(__name__)


class CloudProviderTypeTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        user_model.objects.create_superuser('test.admin', 'test.admin@digitalreasoning.com', '1234')
        user_model.objects.create_user('test.user', 'test.user@digitalreasoning.com', '1234')
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
        logger.debug(response.data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class CloudProviderTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
