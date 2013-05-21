# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CloudProviderType'
        db.create_table(u'cloud_cloudprovidertype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32)),
        ))
        db.send_create_signal(u'cloud', ['CloudProviderType'])

        # Adding model 'CloudProvider'
        db.create_table(u'cloud_cloudprovider', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, populate_from='title', overwrite=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('provider_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloud.CloudProviderType'])),
            ('yaml', self.gf('django.db.models.fields.TextField')()),
            ('private_key_file', self.gf('core.fields.DeletingFileField')(max_length=255)),
        ))
        db.send_create_signal(u'cloud', ['CloudProvider'])

        # Adding model 'CloudProviderInstanceSize'
        db.create_table(u'cloud_cloudproviderinstancesize', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, populate_from='title', overwrite=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('provider_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloud.CloudProviderType'])),
            ('instance_id', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal(u'cloud', ['CloudProviderInstanceSize'])

        # Adding model 'CloudProfile'
        db.create_table(u'cloud_cloudprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, populate_from='title', overwrite=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('cloud_provider', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloud.CloudProvider'])),
            ('image_id', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('default_instance_size', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloud.CloudProviderInstanceSize'])),
            ('script', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('ssh_user', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal(u'cloud', ['CloudProfile'])


    def backwards(self, orm):
        # Deleting model 'CloudProviderType'
        db.delete_table(u'cloud_cloudprovidertype')

        # Deleting model 'CloudProvider'
        db.delete_table(u'cloud_cloudprovider')

        # Deleting model 'CloudProviderInstanceSize'
        db.delete_table(u'cloud_cloudproviderinstancesize')

        # Deleting model 'CloudProfile'
        db.delete_table(u'cloud_cloudprofile')


    models = {
        u'cloud.cloudprofile': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'CloudProfile'},
            'cloud_provider': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudProvider']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'default_instance_size': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudProviderInstanceSize']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_id': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'script': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'ssh_user': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'cloud.cloudprovider': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'CloudProvider'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'private_key_file': ('core.fields.DeletingFileField', [], {'max_length': '255'}),
            'provider_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudProviderType']"}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'yaml': ('django.db.models.fields.TextField', [], {})
        },
        u'cloud.cloudproviderinstancesize': {
            'Meta': {'object_name': 'CloudProviderInstanceSize'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_id': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'provider_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloud.CloudProviderType']"}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'cloud.cloudprovidertype': {
            'Meta': {'object_name': 'CloudProviderType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'})
        }
    }

    complete_apps = ['cloud']