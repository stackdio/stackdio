# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    replaces = [
        ('users', '0001_initial'),
        ('users', '0002_v0_7_migrations'),
        ('users', '0003_v0_7b_migrations'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('public_key', models.TextField(blank=True)),
                ('advanced_view', models.BooleanField(default=False, verbose_name='Advanced View')),
                ('user', models.OneToOneField(related_name='settings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'default_permissions': (),
                'verbose_name_plural': 'User settings',
            },
        ),
    ]
