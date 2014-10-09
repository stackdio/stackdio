# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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
            ('default_availability_zone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='default_zone', null=True, to=orm['cloud.CloudZone'])),
            ('account_id', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('config_file', self.gf('core.fields.DeletingFileField')(default=None, max_length=255, null=True, blank=True)),
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
            ('config_file', self.gf('core.fields.DeletingFileField')(default=None, max_length=255, null=True, blank=True)),
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
            ('filesystem_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
        ))
        db.send_create_signal(u'cloud', ['Snapshot'])

        # Adding unique constraint on 'Snapshot', fields ['snapshot_id', 'cloud_provider']
        db.create_unique(u'cloud_snapshot', ['snapshot_id', 'cloud_provider_id'])

        # Adding model 'CloudZone'
        db.create_table(u'cloud_cloudzone', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, populate_from='title', overwrite=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('provider_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cloud.CloudProviderType'])),
        ))
        db.send_create_signal(u'cloud', ['CloudZone'])

        # Adding unique constraint on 'CloudZone', fields ['title', 'provider_type']
        db.create_unique(u'cloud_cloudzone', ['title', 'provider_type_id'])

        # Adding model 'SecurityGroup'
        db.create_table(u'cloud_securitygroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('group_id', self.gf('django.db.models.fields.CharField')(max_length=16, blank=True)),
            ('cloud_provider', self.gf('django.db.models.fields.related.ForeignKey')(related_name='security_groups', to=orm['cloud.CloudProvider'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='security_groups', to=orm['auth.User'])),
            ('is_default', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'cloud', ['SecurityGroup'])

        # Adding unique constraint on 'SecurityGroup', fields ['name', 'cloud_provider']
        db.create_unique(u'cloud_securitygroup', ['name', 'cloud_provider_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'SecurityGroup', fields ['name', 'cloud_provider']
        db.delete_unique(u'cloud_securitygroup', ['name', 'cloud_provider_id'])

        # Removing unique constraint on 'CloudZone', fields ['title', 'provider_type']
        db.delete_unique(u'cloud_cloudzone', ['title', 'provider_type_id'])

        # Removing unique constraint on 'Snapshot', fields ['snapshot_id', 'cloud_provider']
        db.delete_unique(u'cloud_snapshot', ['snapshot_id', 'cloud_provider_id'])

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

        # Deleting model 'CloudZone'
        db.delete_table(u'cloud_cloudzone')

        # Deleting model 'SecurityGroup'
        db.delete_table(u'cloud_securitygroup')


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
        u'cloud.securitygroup': {
            'Meta': {'unique_together': "(('name', 'cloud_provider'),)", 'object_name': 'SecurityGroup'},
            'cloud_provider': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'security_groups'", 'to': u"orm['cloud.CloudProvider']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'group_id': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'security_groups'", 'to': u"orm['auth.User']"})
        },
        u'cloud.snapshot': {
            'Meta': {'unique_together': "(('snapshot_id', 'cloud_provider'),)", 'object_name': 'Snapshot'},
            'cloud_provider': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'snapshots'", 'to': u"orm['cloud.CloudProvider']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'filesystem_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'size_in_gb': ('django.db.models.fields.IntegerField', [], {}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'snapshot_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['cloud']