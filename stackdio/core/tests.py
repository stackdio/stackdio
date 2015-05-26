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

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class StackdioTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        user_model.objects.create_superuser('test.admin', 'test.admin@digitalreasoning.com', '1234')
        user_model.objects.create_user('test.user', 'test.user@digitalreasoning.com', '1234')
