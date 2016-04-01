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

"""
Some shortcuts for getting model permissions for users.
Adapted from the `guardian.shortcuts` module.
"""


from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def get_users_with_model_perms(model_cls, attach_perms=False, with_superusers=False,
                               with_group_users=True):
    """
    Returns queryset of all ``User`` objects with *any* model permissions for
    the given ``model_cls``.

    :param model_cls: persisted Django's ``Model`` class

    :param attach_perms: Default: ``False``. If set to ``True`` result would be
      dictionary of ``User`` instances with permissions' codenames list as
      values. This would fetch users eagerly!

    :param with_superusers: Default: ``False``. If set to ``True`` result would
      contain all superusers.

    :param with_group_users: Default: ``True``. If set to ``False`` result would
      **not** contain those users who have only group permissions for given
      ``obj``.

    Example::

        >>> from django.contrib.flatpages.models import FlatPage
        >>> from django.contrib.auth.models import User
        >>> from guardian.shortcuts import assign_perm, get_users_with_perms
        >>>
        >>> page = FlatPage.objects.create(title='Some page', path='/some/page/')
        >>> joe = User.objects.create_user('joe', 'joe@example.com', 'joesecret')
        >>> assign_perm('change_flatpage', joe, page)
        >>>
        >>> get_users_with_perms(page)
        [<User: joe>]
        >>>
        >>> get_users_with_perms(page, attach_perms=True)
        {<User: joe>: [u'change_flatpage']}

    """
    ctype = ContentType.objects.get_for_model(model_cls)
    if not attach_perms:
        # It's much easier without attached perms so we do it first if that is
        # the case
        user_filters = {
            'user_permissions__content_type': ctype
        }
        qset = Q(**user_filters)
        if with_group_users:
            group_filters = {
                'groups__permissions__content_type': ctype
            }
            qset = qset | Q(**group_filters)
        if with_superusers:
            qset = qset | Q(is_superuser=True)
        return get_user_model().objects.filter(qset).distinct()
    else:
        # TODO: Do not hit db for each user!
        users = {}
        for user in get_users_with_model_perms(model_cls, with_group_users=with_group_users):
            users[user] = sorted([perm.codename for perm in
                                  user.user_permissions.filter(content_type=ctype)])
        return users


def get_groups_with_model_perms(model_cls, attach_perms=False):
    """
    Returns queryset of all ``Group`` objects with *any* model permissions for
    the given ``model_cls``.

    :param model_cls: persisted Django's ``Model`` class

    :param attach_perms: Default: ``False``. If set to ``True`` result would be
      dictionary of ``Group`` instances with permissions' codenames list as
      values. This would fetch groups eagerly!

    Example::

        >>> from django.contrib.flatpages.models import FlatPage
        >>> from guardian.shortcuts import assign_perm, get_groups_with_perms
        >>> from guardian.models import Group
        >>>
        >>> page = FlatPage.objects.create(title='Some page', path='/some/page/')
        >>> admins = Group.objects.create(name='Admins')
        >>> assign_perm('change_flatpage', admins, page)
        >>>
        >>> get_groups_with_perms(page)
        [<Group: admins>]
        >>>
        >>> get_groups_with_perms(page, attach_perms=True)
        {<Group: admins>: [u'change_flatpage']}

    """
    ctype = ContentType.objects.get_for_model(model_cls)
    if not attach_perms:
        # It's much easier without attached perms so we do it first if that is
        # the case
        group_filters = {
            'permissions__content_type': ctype
        }
        return Group.objects.filter(**group_filters).distinct()
    else:
        # TODO: Do not hit db for each group!
        groups = {}
        for group in get_groups_with_model_perms(model_cls):
            if group not in groups:
                groups[group] = sorted([perm.codename for perm in
                                        group.permissions.filter(content_type=ctype)])
        return groups
