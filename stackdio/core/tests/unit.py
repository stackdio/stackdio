# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

from django.http import Http404
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework.serializers import ValidationError

from stackdio.api.cloud.models import CloudAccount
from stackdio.core import shortcuts, viewsets
from stackdio.core.tests.utils import StackdioTestCase, group_has_perm

logger = logging.getLogger(__name__)


class ModelPermissionSerializerTestCase(StackdioTestCase):

    def get_serializer(self, user_or_group):
        if user_or_group == 'user':
            view = viewsets.StackdioModelUserPermissionsViewSet()
        elif user_or_group == 'group':
            view = viewsets.StackdioModelGroupPermissionsViewSet()
        else:
            view = None
        view.model_cls = CloudAccount
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
                                 'model_cls': CloudAccount})

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['create'])

        true = ['create']

        for perm in CloudAccount._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudaccount' % perm)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudaccount' % perm)
            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def _test_update(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)

        assign_perm('cloud.create_cloudaccount', auth_obj)

        instance = {
            user_or_group: auth_obj,
            'permissions': ['create'],
        }

        validated_data = {
            user_or_group: auth_obj,
            'permissions': ['admin'],
            'model_cls': CloudAccount,
        }

        obj = serializer.update(instance, validated_data)

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['admin'])

        true = ['admin']

        for perm in CloudAccount._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudaccount' % perm)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudaccount' % perm)
            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def _test_partial_update(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)
        serializer.partial = True

        assign_perm('cloud.create_cloudaccount', auth_obj)

        instance = {
            user_or_group: auth_obj,
            'permissions': ['create'],
        }

        validated_data = {
            user_or_group: auth_obj,
            'permissions': ['admin'],
            'model_cls': CloudAccount,
        }

        obj = serializer.update(instance, validated_data)

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['admin'])

        true = ['admin', 'create']

        for perm in CloudAccount._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudaccount' % perm)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudaccount' % perm)
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

    @classmethod
    def setUpTestData(cls):
        super(ObjectPermissionSerializerTestCase, cls).setUpTestData()

        CloudAccount.objects.create(
            provider_id=1,
            title='test',
            description='test',
            vpc_id='vpc-blah',
            region_id=1,
        )

    def setUp(self):
        super(ObjectPermissionSerializerTestCase, self).setUp()
        self.account = CloudAccount.objects.get()

    def get_serializer(self, user_or_group):
        if user_or_group == 'user':
            view = viewsets.StackdioObjectUserPermissionsViewSet()
        elif user_or_group == 'group':
            view = viewsets.StackdioObjectGroupPermissionsViewSet()
        else:
            view = None
        view.get_permissioned_object = lambda: self.account
        view.request = None
        view.format_kwarg = None
        view.model_cls = CloudAccount
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
                                 'object': self.account})

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['view'])

        true = ['view']

        for perm in CloudAccount._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudaccount' % perm, self.account)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudaccount' % perm, self.account)
            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def _test_update(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)

        assign_perm('cloud.view_cloudaccount', auth_obj, self.account)

        instance = {
            user_or_group: auth_obj,
            'permissions': ['view'],
        }

        validated_data = {
            user_or_group: auth_obj,
            'permissions': ['admin'],
            'object': self.account,
        }

        obj = serializer.update(instance, validated_data)

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['admin'])

        true = ['admin']

        for perm in CloudAccount._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudaccount' % perm, self.account)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudaccount' % perm, self.account)
            if perm in true:
                self.assertTrue(has_perm)
            else:
                self.assertFalse(has_perm)

    def _test_partial_update(self, auth_obj, user_or_group):
        serializer = self.get_serializer(user_or_group)
        serializer.partial = True

        assign_perm('cloud.view_cloudaccount', auth_obj, self.account)

        instance = {
            user_or_group: auth_obj,
            'permissions': ['view'],
        }

        validated_data = {
            user_or_group: auth_obj,
            'permissions': ['admin'],
            'object': self.account,
        }

        obj = serializer.update(instance, validated_data)

        self.assertEqual(obj[user_or_group], auth_obj)
        self.assertEqual(obj['permissions'], ['admin'])

        true = ['admin', 'view']

        for perm in CloudAccount._meta.default_permissions:
            if user_or_group == 'user':
                has_perm = auth_obj.has_perm('cloud.%s_cloudaccount' % perm, self.account)
            elif user_or_group == 'group':
                has_perm = group_has_perm(auth_obj, '%s_cloudaccount' % perm, self.account)

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
        for perm in CloudAccount.model_permissions:
            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

            assign_perm('cloud.%s_cloudaccount' % perm, self.user)

            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 1)
            self.assertEqual(users.first(), self.user)

            remove_perm('cloud.%s_cloudaccount' % perm, self.user)

            # Make sure assigning the group permissions doesn't show up here
            assign_perm('cloud.%s_cloudaccount' % perm, self.group)

            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

    def test_users_with_model_perms_with_groups(self):
        for perm in CloudAccount.model_permissions:
            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=False,
                with_group_users=True,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

            assign_perm('cloud.%s_cloudaccount' % perm, self.group)

            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=False,
                with_group_users=True,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 1)
            self.assertEqual(users.first(), self.user)

            remove_perm('cloud.%s_cloudaccount' % perm, self.group)

    def test_users_with_model_perms_with_superusers(self):
        users = shortcuts.get_users_with_model_perms(
            CloudAccount,
            attach_perms=False,
            with_group_users=False,
            with_superusers=True,
        )

        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first(), self.admin)

    def test_users_with_model_perms_attach_perms(self):
        for perm in CloudAccount.model_permissions:
            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=True,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertIsInstance(users, dict)
            self.assertEqual(len(users), 0)

            assign_perm('cloud.%s_cloudaccount' % perm, self.user)

            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=True,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertIsInstance(users, dict)
            self.assertEqual(len(users), 1)
            self.assertTrue(self.user in users)
            self.assertEqual(users[self.user], ['%s_cloudaccount' % perm])

            remove_perm('cloud.%s_cloudaccount' % perm, self.user)

    def test_users_with_model_perms_wrong_model(self):
        for perm in CloudAccount.model_permissions:
            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

            assign_perm('cloud.%s_cloudimage' % perm, self.user)

            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

            # Make sure assigning the group permissions doesn't show up here
            assign_perm('cloud.%s_cloudimage' % perm, self.group)

            users = shortcuts.get_users_with_model_perms(
                CloudAccount,
                attach_perms=False,
                with_group_users=False,
                with_superusers=False,
            )

            self.assertEqual(users.count(), 0)

    def test_groups_with_model_perms(self):
        for perm in CloudAccount.model_permissions:
            groups = shortcuts.get_groups_with_model_perms(
                CloudAccount,
                attach_perms=False,
            )

            self.assertEqual(groups.count(), 0)

            assign_perm('cloud.%s_cloudaccount' % perm, self.group)

            groups = shortcuts.get_groups_with_model_perms(
                CloudAccount,
                attach_perms=False,
            )

            self.assertEqual(groups.count(), 1)
            self.assertEqual(groups.first(), self.group)

            remove_perm('cloud.%s_cloudaccount' % perm, self.group)

    def test_groups_with_model_perms_attach_perms(self):
        for perm in CloudAccount.model_permissions:
            groups = shortcuts.get_groups_with_model_perms(
                CloudAccount,
                attach_perms=True,
            )

            self.assertIsInstance(groups, dict)
            self.assertEqual(len(groups), 0)

            assign_perm('cloud.%s_cloudaccount' % perm, self.group)

            groups = shortcuts.get_groups_with_model_perms(
                CloudAccount,
                attach_perms=True,
            )

            self.assertIsInstance(groups, dict)
            self.assertEqual(len(groups), 1)
            self.assertTrue(self.group in groups)
            self.assertEqual(groups[self.group], ['%s_cloudaccount' % perm])

            remove_perm('cloud.%s_cloudaccount' % perm, self.group)


class BasePermissionsViewSetTestCase(StackdioTestCase):

    def get_viewset(self):
        view = viewsets.StackdioBasePermissionsViewSet()
        return view

    def test_filter_perms(self):
        avail_perms = CloudAccount._meta.default_permissions

        perms = ['foo', 'bar', 'blah', 'has', 'baz']

        new_perms = viewsets._filter_perms(avail_perms, perms)

        self.assertEqual(len(new_perms), 0)

    def test_switch_user_group(self):
        view = self.get_viewset()

        try:
            self.assertRaises(AssertionError, view.switch_user_group, 'user', 'group')
        except ValueError:
            raise AssertionError('`switch_user_group` should have raised an AssertionError, not '
                                 'a ValueError')

        view.user_or_group = 'user'
        self.assertEqual(view.switch_user_group('user', 'group'), 'user')

        view.user_or_group = 'group'
        self.assertEqual(view.switch_user_group('user', 'group'), 'group')

    def test_transform_perm(self):
        view = self.get_viewset()

        tranform_func = view._transform_perm('cloudaccount')

        self.assertCallable(tranform_func)

        self.assertEqual(tranform_func('blah_cloudaccount'), 'blah')
        self.assertEqual(tranform_func('blah_cloudimage'), 'blah_cloudimage')

    def test_get_object(self):
        view = self.get_viewset()

        queryset = [
            {'user': self.user, 'permissions': ['view', 'admin', 'create']},
            {'user': self.admin, 'permissions': ['delete', 'update', 'view']},
        ]

        view.user_or_group = 'user'
        view.lookup_field = 'username'
        view.get_queryset = lambda: queryset
        view.kwargs = {
            'username': 'test.user'
        }

        obj = view.get_object()

        self.assertTrue('user' in obj)
        self.assertTrue('permissions' in obj)

        self.assertEqual(obj['user'], self.user)
        self.assertEqual(obj['permissions'], ['view', 'admin', 'create'])

        view.kwargs['username'] = 'test.bahss'

        self.assertRaises(Http404, view.get_object)


class ModelPermissionsViewSetTestCase(StackdioTestCase):

    def _create_perms(self, auth_obj):
        for perm in CloudAccount._meta.default_permissions:
            assign_perm('cloud.%s_cloudaccount' % perm, auth_obj)

    def get_viewset(self, user_or_group):
        if user_or_group == 'user':
            view = viewsets.StackdioModelUserPermissionsViewSet()
        elif user_or_group == 'group':
            view = viewsets.StackdioModelGroupPermissionsViewSet()
        else:
            view = None
        view.model_cls = CloudAccount
        return view

    def _test_get_queryset(self, auth_obj, user_or_group):
        view = self.get_viewset(user_or_group)

        self._create_perms(auth_obj)

        queryset = view.get_queryset()

        self.assertEqual(len(queryset), 1)

        first = queryset[0]

        self.assertTrue(user_or_group in first)
        self.assertTrue('permissions' in first)

        self.assertEqual(first[user_or_group], auth_obj)
        self.assertEqual(first['permissions'], ['admin', 'create'])

    def test_user_get_queryset(self):
        self._test_get_queryset(self.user, 'user')

    def test_group_get_queryset(self):
        self._test_get_queryset(self.group, 'group')

    def test_perform_destroy(self):
        view = self.get_viewset('user')

        self._create_perms(self.user)

        view.perform_destroy({
            'user': self.user,
            'permissions': ['create', 'admin'],
        })

        for perm in CloudAccount.model_permissions:
            self.assertFalse(self.user.has_perm('cloud.%s_cloudaccount' % perm))


class ObjectPermissionsViewSetTestCase(StackdioTestCase):

    @classmethod
    def setUpTestData(cls):
        super(ObjectPermissionsViewSetTestCase, cls).setUpTestData()

        CloudAccount.objects.create(
            provider_id=1,
            title='test',
            description='test',
            vpc_id='vpc-blah',
            region_id=1,
        )

    def setUp(self):
        super(ObjectPermissionsViewSetTestCase, self).setUp()
        self.account = CloudAccount.objects.get()

    def _create_perms(self, auth_obj, obj):
        for perm in CloudAccount._meta.default_permissions:
            assign_perm('cloud.%s_cloudaccount' % perm, auth_obj, obj)

    def get_viewset(self, user_or_group):
        if user_or_group == 'user':
            view = viewsets.StackdioObjectUserPermissionsViewSet()
        elif user_or_group == 'group':
            view = viewsets.StackdioObjectGroupPermissionsViewSet()
        else:
            view = None
        view.get_permissioned_object = lambda: self.account
        return view

    def _test_get_queryset(self, auth_obj, user_or_group):
        view = self.get_viewset(user_or_group)

        self._create_perms(auth_obj, self.account)

        queryset = view.get_queryset()

        self.assertEqual(len(queryset), 1)

        first = queryset[0]

        self.assertTrue(user_or_group in first)
        self.assertTrue('permissions' in first)

        self.assertEqual(first[user_or_group], auth_obj)
        self.assertEqual(first['permissions'], ['admin', 'delete', 'update', 'view'])

    def test_user_get_queryset(self):
        self._test_get_queryset(self.user, 'user')

    def test_group_get_queryset(self):
        self._test_get_queryset(self.group, 'group')

    def test_perform_destroy(self):
        view = self.get_viewset('user')

        self._create_perms(self.user, self.account)

        view.perform_destroy({
            'user': self.user,
            'permissions': ['view', 'delete', 'update', 'admin'],
        })

        for perm in CloudAccount.object_permissions:
            self.assertFalse(self.user.has_perm('cloud.%s_cloudaccount' % perm, self.account))
