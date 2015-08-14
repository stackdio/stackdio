# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django_extensions.db.fields


def forwards(apps, schema_editor):
    BlueprintHostFormulaComponent = apps.get_model('blueprints', 'BlueprintHostFormulaComponent')
    GlobalOrchestrationFormulaComponent = apps.get_model('cloud',
                                                         'GlobalOrchestrationFormulaComponent')

    FormulaComponent = apps.get_model('formulas', 'FormulaComponentTEMP')

    ContentType = apps.get_model('contenttypes', 'ContentType')
    BlueprintHostDefinition = apps.get_model('blueprints', 'BlueprintHostDefinition')
    CloudAccount = apps.get_model('cloud', 'CloudAccount')

    bhd_ctype = ContentType.objects.get_for_model(BlueprintHostDefinition)
    ca_ctype = ContentType.objects.get_for_model(CloudAccount)

    for bhfc in BlueprintHostFormulaComponent.objects.all():
        FormulaComponent.objects.create(
            formula=bhfc.component.formula,
            sls_path=bhfc.component.sls_path,
            order=bhfc.order,
            content_type=bhd_ctype,
            object_id=bhfc.host.id,
        )

    for gofc in GlobalOrchestrationFormulaComponent.objects.all():
        FormulaComponent.objects.create(
            formula=gofc.component.formula,
            sls_path=gofc.component.sls_path,
            order=gofc.order,
            content_type=ca_ctype,
            object_id=gofc.account.id,
        )


def backwards(apps, schema_editor):
    BlueprintHostFormulaComponent = apps.get_model('blueprints', 'BlueprintHostFormulaComponent')
    GlobalOrchestrationFormulaComponent = apps.get_model('cloud',
                                                         'GlobalOrchestrationFormulaComponent')

    FormulaComponent = apps.get_model('formulas', 'FormulaComponentTEMP')

    ContentType = apps.get_model('contenttypes', 'ContentType')
    BlueprintHostDefinition = apps.get_model('blueprints', 'BlueprintHostDefinition')
    CloudAccount = apps.get_model('cloud', 'CloudAccount')

    bhd_ctype = ContentType.objects.get_for_model(BlueprintHostDefinition)
    ca_ctype = ContentType.objects.get_for_model(CloudAccount)


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('blueprints', '0003_v0_7b_migrations'),
        ('cloud', '0005_v0_7b_migrations'),
        ('formulas', '0003_v0_7b_migrations'),
    ]

    operations = [
        # Create a TEMPORARY model.
        migrations.CreateModel(
            name='FormulaComponentTEMP',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('sls_path', models.CharField(max_length=255)),
                ('object_id', models.PositiveIntegerField()),
                ('order', models.IntegerField(default=0, verbose_name=b'Order')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('formula', models.ForeignKey(to='formulas.Formula')),
            ],
            options={
                'ordering': ['order'],
                'default_permissions': (),
                'verbose_name_plural': 'formula components',
            },
        ),
        migrations.RunPython(forwards, backwards),
    ]
