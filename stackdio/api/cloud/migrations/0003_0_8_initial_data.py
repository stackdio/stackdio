# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    """
    This migration is now a no-op.  The logic was moved into a post-migrate signal.
    """
    initial = True

    dependencies = [
        ('cloud', '0002_0_8_initial'),
    ]

    replaces = [
        ('cloud', '0003_initial_data'),
    ]

    operations = [
        migrations.RunPython(lambda a, s: None, lambda a, s: None),
    ]
