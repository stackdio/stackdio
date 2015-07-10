# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import migrations

logger = logging.getLogger(__name__)


group_add_perms = ('admin', 'create', 'update')

def create_group_perms(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    content_type = ContentType.objects.get_for_model(Group)

    for perm in group_add_perms:
        Permission.objects.create(
            name='Can %s group' % perm,
            codename='%s_group' % perm,
            content_type=content_type,
        )

def remove_group_perms(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    content_type = ContentType.objects.get_for_model(Group)

    for perm in group_add_perms:
        try:
            p = Permission.objects.get(
                codename='%s_group' % perm,
                content_type=content_type,
            )
            p.delete()
        except Permission.DoesNotExist:
            logger.debug('Not deleting permission `%s_group`, it did not exist' % perm)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('auth', '__latest__'),
        ('contenttypes', '__latest__'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='usersettings',
            options={'default_permissions': (), 'verbose_name_plural': 'User settings'},
        ),
        migrations.RunPython(create_group_perms, remove_group_perms),
    ]
