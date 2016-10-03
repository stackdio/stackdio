# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def delete_anonymous_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    try:
        anon_user = User.objects.get(id=-1)
        anon_user.delete()
    except User.DoesNotExist:
        pass


def create_anonymous_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    try:
        User.objects.create(id=-1, username='AnonymousUser',
                            first_name='Anonymous', last_name='User')
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_0_8_initial'),
    ]

    operations = [
        migrations.RunPython(delete_anonymous_user, create_anonymous_user),
    ]
