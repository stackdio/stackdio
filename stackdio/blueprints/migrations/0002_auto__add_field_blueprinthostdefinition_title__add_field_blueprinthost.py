# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'BlueprintHostDefinition.title'
        db.add_column(u'blueprints_blueprinthostdefinition', 'title',
                      self.gf('django.db.models.fields.CharField')(default=u'AutoTitle', max_length=255),
                      keep_default=False)

        # Adding field 'BlueprintHostDefinition.slug'
        db.add_column(u'blueprints_blueprinthostdefinition', 'slug',
                      self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, default='', populate_from='title', overwrite=False),
                      keep_default=False)

        # Adding field 'BlueprintHostDefinition.description'
        db.add_column(u'blueprints_blueprinthostdefinition', 'description',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'BlueprintAccessRule.title'
        db.add_column(u'blueprints_blueprintaccessrule', 'title',
                      self.gf('django.db.models.fields.CharField')(default=u'AutoTitle', max_length=255),
                      keep_default=False)

        # Adding field 'BlueprintAccessRule.slug'
        db.add_column(u'blueprints_blueprintaccessrule', 'slug',
                      self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, default='', populate_from='title', overwrite=False),
                      keep_default=False)

        # Adding field 'BlueprintAccessRule.description'
        db.add_column(u'blueprints_blueprintaccessrule', 'description',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'BlueprintHostDefinition.title'
        db.delete_column(u'blueprints_blueprinthostdefinition', 'title')

        # Deleting field 'BlueprintHostDefinition.slug'
        db.delete_column(u'blueprints_blueprinthostdefinition', 'slug')

        # Deleting field 'BlueprintHostDefinition.description'
        db.delete_column(u'blueprints_blueprinthostdefinition', 'description')

        # Deleting field 'BlueprintAccessRule.title'
        db.delete_column(u'blueprints_blueprintaccessrule', 'title')

        # Deleting field 'BlueprintAccessRule.slug'
        db.delete_column(u'blueprints_blueprintaccessrule', 'slug')

        # Deleting field 'BlueprintAccessRule.description'
        db.delete_column(u'blueprints_blueprintaccessrule', 'description')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'blueprints.blueprint': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Blueprint'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blueprints'", 'to': u"orm['auth.User']"}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'blueprints.blueprintaccessrule': {
            'Meta': {'object_name': 'BlueprintAccessRule'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'from_port': ('django.db.models.fields.IntegerField', [], {}),
            'host': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'access_rules'", 'to': u"orm['blueprints.BlueprintHostDefinition']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'protocol': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'rule': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'to_port': ('django.db.models.fields.IntegerField', [], {})
        },
        u'blueprints.blueprinthostdefinition': {
            'Meta': {'object_name': 'BlueprintHostDefinition'},
            'blueprint': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'host_definitions'", 'to': u"orm['blueprints.Blueprint']"}),
            'cloud_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudProfile']"}),
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'formula_components': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['formulas.FormulaComponent']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'prefix': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'size': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudInstanceSize']"}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'zone': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudZone']"})
        },
        u'blueprints.blueprintproperty': {
            'Meta': {'unique_together': "(('blueprint', 'name'),)", 'object_name': 'BlueprintProperty'},
            'blueprint': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'properties'", 'to': u"orm['blueprints.Blueprint']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'cloud.cloudinstancesize': {
            'Meta': {'ordering': "['title']", 'object_name': 'CloudInstanceSize'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_id': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'provider_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudProviderType']"}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'cloud.cloudprofile': {
            'Meta': {'unique_together': "(('title', 'cloud_provider'),)", 'object_name': 'CloudProfile'},
            'cloud_provider': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudProvider']"}),
            'config_file': ('core.fields.DeletingFileField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'default_instance_size': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudInstanceSize']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_id': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'ssh_user': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'cloud.cloudprovider': {
            'Meta': {'unique_together': "(('title', 'provider_type'),)", 'object_name': 'CloudProvider'},
            'account_id': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'config_file': ('core.fields.DeletingFileField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'default_availability_zone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'default_zone'", 'null': 'True', 'to': u"orm['cloud.CloudZone']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'provider_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudProviderType']"}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'yaml': ('django.db.models.fields.TextField', [], {})
        },
        u'cloud.cloudprovidertype': {
            'Meta': {'object_name': 'CloudProviderType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        },
        u'cloud.cloudzone': {
            'Meta': {'unique_together': "(('title', 'provider_type'),)", 'object_name': 'CloudZone'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudProviderType']"}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'formulas.formula': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Formula'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'formulas'", 'to': u"orm['auth.User']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'root_path': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'status': ('model_utils.fields.StatusField', [], {'default': "'error'", 'max_length': '100', 'no_check_for_status': 'True'}),
            'status_changed': ('model_utils.fields.MonitorField', [], {'default': 'datetime.datetime.now', 'monitor': "'status'"}),
            'status_detail': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uri': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'formulas.formulacomponent': {
            'Meta': {'object_name': 'FormulaComponent'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'formula': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'components'", 'to': u"orm['formulas.Formula']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sls_path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['blueprints']