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

from guardian.shortcuts import assign_perm, remove_perm
from rest_framework.serializers import ValidationError

from cloud.models import CloudProvider
from core.tests.utils import StackdioTestCase, group_has_perm
from core import serializers, shortcuts, viewsets

logger = logging.getLogger(__name__)


class ModelPermissionSerializerTestCase(StackdioTestCase):

    def get_serializer(self, user_or_group):
        if user_or_group == 'user':
            view = viewsets.StackdioModelUserPermissionsViewSet()
            view.serializer_class = serializers.StackdioUserModelPermissionsSerializer
        elif user_or_group == 'group':
            view = viewsets.StackdioModelGroupPermissionsViewSet()
            view.serializer_class = serializers.StackdioGroupModelPermissionsSerializer
        else:
            view = None
        view.model_cls = CloudProvider
        view.request = None
        view.format_kwarg = None
        return view.get_serializer()

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
            view = viewsets.StackdioObjectUserPermissionsViewSet()
            view.serializer_class = serializers.StackdioUserObjectPermissionsSerializer
        elif user_or_group == 'group':
            view = viewsets.StackdioObjectGroupPermissionsViewSet()
            view.serializer_class = serializers.StackdioGroupObjectPermissionsSerializer
        else:
            view = None
        view.get_permissioned_object = lambda: self.provider
        view.request = None
        view.format_kwarg = None
        view.model_cls = CloudProvider
        return view.get_serializer()

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


class PermissionsShortcutsTestCase(StackdioTestCase):

    def test_users_with_model_perms(self):
        for perm in CloudProvider.model_permissions:
            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

            assign_perm('cloud.%s_cloudprovider' % perm, self.user)

            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 1)
            self.assertEqual(users.first(), self.user)

            remove_perm('cloud.%s_cloudprovider' % perm, self.user)

            # Make sure assigning the group permissions doesn't show up here
            assign_perm('cloud.%s_cloudprovider' % perm, self.group)

            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

    def test_users_with_model_perms_with_groups(self):
        for perm in CloudProvider.model_permissions:
            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=False,
                with_group_users=True,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

            assign_perm('cloud.%s_cloudprovider' % perm, self.group)

            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=False,
                with_group_users=True,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 1)
            self.assertEqual(users.first(), self.user)

            remove_perm('cloud.%s_cloudprovider' % perm, self.group)

    def test_users_with_model_perms_with_superusers(self):
        users = shortcuts.get_users_with_model_perms(
            CloudProvider,
            attach_perms=False,
            with_group_users=False,
            with_superusers=True,
        )

        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.admin)

    def test_users_with_model_perms_attach_perms(self):
        for perm in CloudProvider.model_permissions:
            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=True,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertTrue(isinstance(users, dict))
            self.assertEqual(len(users), 0)

            assign_perm('cloud.%s_cloudprovider' % perm, self.user)

            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=True,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertTrue(isinstance(users, dict))
            self.assertEqual(len(users), 1)
            self.assertTrue(self.user in users)
            self.assertEqual(users[self.user], ['%s_cloudprovider' % perm])

            remove_perm('cloud.%s_cloudprovider' % perm, self.user)

    def test_users_with_model_perms_wrong_model(self):
        for perm in CloudProvider.model_permissions:
            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

            assign_perm('cloud.%s_cloudprofile' % perm, self.user)

            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

            # Make sure assigning the group permissions doesn't show up here
            assign_perm('cloud.%s_cloudprofile' % perm, self.group)

            users = shortcuts.get_users_with_model_perms(
                CloudProvider,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

    def test_groups_with_model_perms(self):
        for perm in CloudProvider.model_permissions:
            groups = shortcuts.get_groups_with_model_perms(
                CloudProvider,
                attach_perms=False,
            )

            self.assertEqual(groups.count(), 0)

            assign_perm('cloud.%s_cloudprovider' % perm, self.group)

            groups = shortcuts.get_groups_with_model_perms(
                CloudProvider,
                attach_perms=False,
            )

            self.assertEqual(groups.count(), 1)
            self.assertEqual(groups.first(), self.group)

            remove_perm('cloud.%s_cloudprovider' % perm, self.group)
            
    def test_groups_with_model_perms_attach_perms(self):
        for perm in CloudProvider.model_permissions:
            groups = shortcuts.get_groups_with_model_perms(
                CloudProvider,
                attach_perms=True,
            )

            self.assertTrue(isinstance(groups, dict))
            self.assertEqual(len(groups), 0)

            assign_perm('cloud.%s_cloudprovider' % perm, self.group)

            groups = shortcuts.get_groups_with_model_perms(
                CloudProvider,
                attach_perms=True,
            )

            self.assertTrue(isinstance(groups, dict))
            self.assertEqual(len(groups), 1)
            self.assertTrue(self.group in groups)
            self.assertEqual(groups[self.group], ['%s_cloudprovider' % perm])

            remove_perm('cloud.%s_cloudprovider' % perm, self.group)


class ModelPermissionsViewSetTestCase(StackdioTestCase):

    def get_viewset(self, user_or_group):
        if user_or_group == 'user':
            view = viewsets.StackdioModelUserPermissionsViewSet()
            view.serializer_class = serializers.StackdioUserModelPermissionsSerializer
        elif user_or_group == 'group':
            view = viewsets.StackdioModelGroupPermissionsViewSet()
            view.serializer_class = serializers.StackdioGroupModelPermissionsSerializer
        else:
            view = None
        view.model_cls = CloudProvider
        return view

    def _test_get_queryset(self, auth_obj, user_or_group):
        view = self.get_viewset(user_or_group)
