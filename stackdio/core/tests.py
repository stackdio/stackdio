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

from guardian.shortcuts import assign_perm
from rest_framework import status
from rest_framework.serializers import ValidationError

from api_v1.urls import urlpatterns
from cloud.models import CloudProvider
from .test_utils import StackdioTestCase, group_has_perm
from .utils import get_urls
from . import serializers, viewsets

logger = logging.getLogger(__name__)


class ModelPermissionSerializerTestCase(StackdioTestCase):

    def get_serializer(self, user_or_group):
        if user_or_group == 'user':
            serializer = serializers.StackdioUserModelPermissionsSerializer()
            view = viewsets.StackdioModelUserPermissionsViewSet()
        elif user_or_group == 'group':
            serializer = serializers.StackdioGroupModelPermissionsSerializer()
            view = viewsets.StackdioModelGroupPermissionsViewSet()
        else:
            serializer = None
            view = None
        view.model_cls = CloudProvider
        serializer.context['view'] = view
        return serializer

    def _test_validate(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)

        try:
            serializer.validate({user_or_group: auth_obj, 'permissions': ['blha', 'sfdf']})
            raise AssertionError('validate() should have thrown an exception')
        except ValidationError:
            pass

        try:
            serializer.validate({user_or_group: auth_obj, 'permissions': ['view']})
            raise AssertionError('validate() should have thrown an exception - view isn\'t a '
                                 'valid model permission')
        except ValidationError:
            pass

        try:
            serializer.validate({user_or_group: auth_obj, 'permissions': ['create']})
        except ValidationError:
            raise AssertionError('validate() should not have thrown an exception')

    def _test_create(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)

        obj = serializer.create({user_or_group: auth_obj,
                                 'permissions': ['create'],
                                 'model_cls': CloudProvider})

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['create'])

        true = ['create']

        for perm in CloudProvider._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudprovider' % perm)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudprovider' % perm)
            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def _test_update(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)

        assign_perm('cloud.create_cloudprovider', auth_obj)

        instance = {
            user_or_group: auth_obj,
            'permissions': ['create'],
        }

        validated_data = {
            user_or_group: auth_obj,
            'permissions': ['admin'],
            'model_cls': CloudProvider,
        }

        obj = serializer.update(instance, validated_data)

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['admin'])

        true = ['admin']

        for perm in CloudProvider._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudprovider' % perm)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudprovider' % perm)
            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def _test_partial_update(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)
        serializer.partial = True

        assign_perm('cloud.create_cloudprovider', auth_obj)

        instance = {
            user_or_group: auth_obj,
            'permissions': ['create'],
        }

        validated_data = {
            user_or_group: auth_obj,
            'permissions': ['admin'],
            'model_cls': CloudProvider,
        }

        obj = serializer.update(instance, validated_data)

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['admin'])

        true = ['admin', 'create']

        for perm in CloudProvider._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudprovider' % perm)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudprovider' % perm)
            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def test_user_validate(self):
        self._test_validate(self.user, 'user')

    def test_user_create(self):
        self._test_create(self.user, 'user')

    def test_user_update(self):
        self._test_update(self.user, 'user')

    def test_user_partial_update(self):
        self._test_partial_update(self.user, 'user')

    def test_group_validate(self):
        self._test_validate(self.group, 'group')

    def test_group_create(self):
        self._test_create(self.group, 'group')

    def test_group_update(self):
        self._test_update(self.group, 'group')

    def test_group_partial_update(self):
        self._test_partial_update(self.group, 'group')


class ObjectPermissionSerializerTestCase(StackdioTestCase):

    fixtures = (
        'cloud/fixtures/initial_data.json',
    )

    @classmethod
    def setUpTestData(cls):
        super(ObjectPermissionSerializerTestCase, cls).setUpTestData()

        CloudProvider.objects.create(
            provider_type_id=1,
            title='test',
            description='test',
            account_id='blah',
            vpc_id='vpc-blah',
            region_id=1,
        )

    def setUp(self):
        super(ObjectPermissionSerializerTestCase, self).setUp()
        self.provider = CloudProvider.objects.get(id=1)

    def get_serializer(self, user_or_group):
        if user_or_group == 'user':
            serializer = serializers.StackdioUserObjectPermissionsSerializer()
            view = viewsets.StackdioObjectUserPermissionsViewSet()
        elif user_or_group == 'group':
            serializer = serializers.StackdioGroupObjectPermissionsSerializer()
            view = viewsets.StackdioObjectGroupPermissionsViewSet()
        else:
            serializer = None
            view = None
        view.get_permissioned_object = lambda: self.provider
        view.model_cls = CloudProvider
        serializer.context['view'] = view
        return serializer

    def _test_validate(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)

        try:
            serializer.validate({user_or_group: auth_obj, 'permissions': ['blha', 'sfdf']})
            raise AssertionError('validate() should have thrown an exception')
        except ValidationError:
            pass

        try:
            serializer.validate({user_or_group: auth_obj, 'permissions': ['create']})
            raise AssertionError('validate() should have thrown an exception - create isn\'t a '
                                 'valid object permission')
        except ValidationError:
            pass

        try:
            serializer.validate({user_or_group: auth_obj, 'permissions': ['view']})
        except ValidationError:
            raise AssertionError('validate() should not have thrown an exception')

    def _test_create(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)

        obj = serializer.create({user_or_group: auth_obj,
                                 'permissions': ['view'],
                                 'object': self.provider})

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['view'])

        true = ['view']

        for perm in CloudProvider._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudprovider' % perm, self.provider)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudprovider' % perm, self.provider)
            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def _test_update(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)

        assign_perm('cloud.view_cloudprovider', auth_obj, self.provider)

        instance = {
            user_or_group: auth_obj,
            'permissions': ['view'],
        }

        validated_data = {
            user_or_group: auth_obj,
            'permissions': ['admin'],
            'object': self.provider,
        }

        obj = serializer.update(instance, validated_data)

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['admin'])

        true = ['admin']

        for perm in CloudProvider._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudprovider' % perm, self.provider)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudprovider' % perm, self.provider)
            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def _test_partial_update(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)
        serializer.partial = True

        assign_perm('cloud.view_cloudprovider', auth_obj, self.provider)

        instance = {
            user_or_group: auth_obj,
            'permissions': ['view'],
        }

        validated_data = {
            user_or_group: auth_obj,
            'permissions': ['admin'],
            'object': self.provider,
        }

        obj = serializer.update(instance, validated_data)

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['admin'])

        true = ['admin', 'view']

        for perm in CloudProvider._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudprovider' % perm, self.provider)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudprovider' % perm, self.provider)

            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def test_user_validate(self):
        self._test_validate(self.user, 'user')

    def test_user_create(self):
        self._test_create(self.user, 'user')

    def test_user_update(self):
        self._test_update(self.user, 'user')

    def test_user_partial_update(self):
        self._test_partial_update(self.user, 'user')

    def test_group_validate(self):
        self._test_validate(self.group, 'group')

    def test_group_create(self):
        self._test_create(self.group, 'group')

    def test_group_update(self):
        self._test_update(self.group, 'group')

    def test_group_partial_update(self):
        self._test_partial_update(self.group, 'group')


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
