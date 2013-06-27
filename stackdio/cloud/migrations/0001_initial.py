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
        ))
        db.send_create_signal(u'cloud', ['CloudProvider'])

        # Adding unique constraint on 'CloudProvider', fields ['title', 'provider_type']
        db.create_unique(u'cloud_cloudprovider', ['title', 'provider_type_id'])

        # Adding model 'CloudInstanceSize'
        db.create_table(u'cloud_cloudinstancesize', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, populate_from='title', overwrite=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('provider_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloud.CloudProviderType'])),
            ('instance_id', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal(u'cloud', ['CloudInstanceSize'])

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
            ('default_instance_size', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloud.CloudInstanceSize'])),
            ('ssh_user', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal(u'cloud', ['CloudProfile'])

        # Adding unique constraint on 'CloudProfile', fields ['title', 'cloud_provider']
        db.create_unique(u'cloud_cloudprofile', ['title', 'cloud_provider_id'])

        # Adding model 'Snapshot'
        db.create_table(u'cloud_snapshot', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, populate_from='title', overwrite=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('cloud_provider', self.gf('django.db.models.fields.related.ForeignKey')(related_name='snapshots', to=orm['cloud.CloudProvider'])),
            ('snapshot_id', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('size_in_gb', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'cloud', ['Snapshot'])


    def backwards(self, orm):
        # Removing unique constraint on 'CloudProfile', fields ['title', 'cloud_provider']
        db.delete_unique(u'cloud_cloudprofile', ['title', 'cloud_provider_id'])

        # Removing unique constraint on 'CloudProvider', fields ['title', 'provider_type']
        db.delete_unique(u'cloud_cloudprovider', ['title', 'provider_type_id'])

        # Deleting model 'CloudProviderType'
        db.delete_table(u'cloud_cloudprovidertype')

        # Deleting model 'CloudProvider'
        db.delete_table(u'cloud_cloudprovider')

        # Deleting model 'CloudInstanceSize'
        db.delete_table(u'cloud_cloudinstancesize')

        # Deleting model 'CloudProfile'
        db.delete_table(u'cloud_cloudprofile')

        # Deleting model 'Snapshot'
        db.delete_table(u'cloud_snapshot')


    models = {
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
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
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
        u'cloud.snapshot': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Snapshot'},
            'cloud_provider': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'snapshots'", 'to': u"orm['cloud.CloudProvider']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'size_in_gb': ('django.db.models.fields.IntegerField', [], {}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'snapshot_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['cloud']