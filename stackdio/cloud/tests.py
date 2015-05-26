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
import sys

from django.test import TestCase
from rest_framework.test import APIClient


logger = logging.getLogger(__name__)


class CloudProviderTypeTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_authenticated(self):
        response = self.client.get('/api/provider_types/')
        self.assertEqual(response.status_code, 402)

    def test_create_provider_type(self):
        response = self.client.post('/api/provider_types/', {'title': 'new'})


class CloudProviderTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
