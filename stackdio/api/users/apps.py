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

from __future__ import print_function

import logging

from django.apps import AppConfig, apps
from django.core import exceptions
from django.db import DEFAULT_DB_ALIAS, router
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy as _

logger = logging.getLogger(__name__)


EXTRA_USER_PERMS = ('admin', 'create', 'view')
EXTRA_GROUP_PERMS = ('admin', 'create', 'update', 'view')


def create_extra_permissions(app_config, verbosity=2, interactive=True,
                             using=DEFAULT_DB_ALIAS, **kwargs):
    """
    Create the extra user & group permissions we need.  Pulled almost entirely from:

    django.contrib.auth.management:create_permissions
    """

    if not app_config.models_module:
        return

    try:
        Permission = apps.get_model('auth', 'Permission')
        User = apps.get_model('auth', 'User')
        Group = apps.get_model('auth', 'Group')
    except LookupError:
        return

    if not router.allow_migrate_model(using, Permission):
        return

    from django.contrib.contenttypes.models import ContentType

    # The list of perms we need to create
    perms = []

    for model, extra_perms in ((User, EXTRA_USER_PERMS), (Group, EXTRA_GROUP_PERMS)):
        # This will hold the permissions we're looking for as
        # (content_type, (codename, name))
        searched_perms = []

        # Grab the ctype for the model
        ctype = ContentType.objects.db_manager(using).get_for_model(model)

        model_name = model._meta.model_name

        for perm in extra_perms:
            searched_perms.append((ctype, ('%s_%s' % (perm, model_name),
                                           'Can %s %s' % (perm, model_name))))

        # Find all the Permissions that have a content_type for the model.
        # We don't need to check for codenames since we already have
        # a list of the ones we're going to create.
        all_perms = set(Permission.objects.using(using).filter(
            content_type=ctype,
        ).values_list(
            "content_type", "codename"
        ))

        perms += [
            Permission(codename=codename, name=name, content_type=ct)
            for ct, (codename, name) in searched_perms
            if (ct.pk, codename) not in all_perms
        ]

    # Validate the permissions before bulk_creation to avoid cryptic
    # database error when the verbose_name is longer than 50 characters
    permission_name_max_length = Permission._meta.get_field('name').max_length
    verbose_name_max_length = permission_name_max_length - 11  # len('Can change ') prefix
    for perm in perms:
        if len(perm.name) > permission_name_max_length:
            raise exceptions.ValidationError(
                "The verbose_name of %s.%s is longer than %s characters" % (
                    perm.content_type.app_label,
                    perm.content_type.model,
                    verbose_name_max_length,
                )
            )

    Permission.objects.using(using).bulk_create(perms)
    if verbosity >= 2:
        for perm in perms:
            print("Adding permission '%s'" % perm)


class UsersConfig(AppConfig):
    name = 'stackdio.api.users'
    verbose_name = _("Users")

    def ready(self):
        post_migrate.connect(create_extra_permissions, sender=self)
