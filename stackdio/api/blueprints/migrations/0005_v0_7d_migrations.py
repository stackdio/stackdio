# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blueprints', '0004_v0_7c_migrations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blueprintvolume',
            name='device',
            field=models.CharField(max_length=32, verbose_name=b'Device Name', choices=[(b'/dev/sdb', b'/dev/sdb'), (b'/dev/sdc', b'/dev/sdc'), (b'/dev/sdd', b'/dev/sdd'), (b'/dev/sde', b'/dev/sde'), (b'/dev/sdf', b'/dev/sdf'), (b'/dev/sdg', b'/dev/sdg'), (b'/dev/sdh', b'/dev/sdh'), (b'/dev/sdi', b'/dev/sdi'), (b'/dev/sdj', b'/dev/sdj'), (b'/dev/sdk', b'/dev/sdk'), (b'/dev/sdl', b'/dev/sdl')]),
        ),
    ]
