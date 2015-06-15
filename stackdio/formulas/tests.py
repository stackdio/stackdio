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

from rest_framework import status

from core.tests import PermissionsMixin, StackdioTestCase
from . import models


class FormulaTestCase(StackdioTestCase, PermissionsMixin):
    """
    Tests for CloudProvider things
    """

    permission_tests = {
        'model': models.Formula,
        'create_data': {
            'title': 'test',
            'description': 'test',
            'uri': 'https://github.com/stackdio-formulas/java-formula.git',
            'root_path': '~/.stackdio/storage/formulas/java-formula',
        },
        'endpoint': '/api/formulas/{0}/',
        'permission': 'formulas.%s_formula',
        'permission_types': [
            {
                'perm': 'view', 'method': 'get'
            },
            {
                'perm': 'delete', 'method': 'delete', 'code': status.HTTP_204_NO_CONTENT
            },
        ]
    }

    def test_update(self):
        endpoint = self.permission_tests['endpoint'].format(self.obj.pk)

        self.client.login(username='test.user', password='1234')

        # Test put and patch
        response = self.client.put(endpoint, {'title': 'test2'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.patch(endpoint, {'title': 'test2'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
