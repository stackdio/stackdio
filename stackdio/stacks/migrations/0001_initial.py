# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Stack'
        db.create_table(u'stacks_stack', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, populate_from='title', overwrite=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='stacks', to=orm['auth.User'])),
            ('cloud_provider', self.gf('django.db.models.fields.related.ForeignKey')(related_name='stacks', to=orm['cloud.CloudProvider'])),
            ('hosts_file', self.gf('core.fields.DeletingFileField')(default=None, max_length=255, null=True, blank=True)),
            ('map_file', self.gf('core.fields.DeletingFileField')(default=None, max_length=255, null=True, blank=True)),
            ('top_file', self.gf('core.fields.DeletingFileField')(default=None, max_length=255, null=True, blank=True)),
            ('pillar_file', self.gf('core.fields.DeletingFileField')(default=None, max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'stacks', ['Stack'])

        # Adding unique constraint on 'Stack', fields ['user', 'title']
        db.create_unique(u'stacks_stack', ['user_id', 'title'])

        # Adding model 'StackHistory'
        db.create_table(u'stacks_stackhistory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('stack', self.gf('django.db.models.fields.related.ForeignKey')(related_name='history', to=orm['stacks.Stack'])),
            ('event', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('status', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('level', self.gf('django.db.models.fields.CharField')(max_length=16)),
        ))
        db.send_create_signal(u'stacks', ['StackHistory'])

        # Adding model 'SaltRole'
        db.create_table(u'stacks_saltrole', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django_extensions.db.fields.AutoSlugField')(allow_duplicates=False, max_length=50, separator=u'-', blank=True, populate_from='title', overwrite=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('sls_path', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal(u'stacks', ['SaltRole'])

        # Adding model 'Host'
        db.create_table(u'stacks_host', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('status', self.gf('model_utils.fields.StatusField')(default='ok', max_length=100, no_check_for_status=True)),
            ('status_changed', self.gf('model_utils.fields.MonitorField')(default=datetime.datetime.now, monitor='status')),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('status_detail', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('stack', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hosts', to=orm['stacks.Stack'])),
            ('cloud_profile', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hosts', to=orm['cloud.CloudProfile'])),
            ('instance_size', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hosts', to=orm['cloud.CloudInstanceSize'])),
            ('availability_zone', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hosts', to=orm['cloud.CloudZone'])),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('state', self.gf('django.db.models.fields.CharField')(default='unknown', max_length=32)),
            ('provider_dns', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('fqdn', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('instance_id', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('sir_id', self.gf('django.db.models.fields.CharField')(default='unknown', max_length=32)),
            ('sir_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2)),
        ))
        db.send_create_signal(u'stacks', ['Host'])

        # Adding M2M table for field roles on 'Host'
        db.create_table(u'stacks_host_roles', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('host', models.ForeignKey(orm[u'stacks.host'], null=False)),
            ('saltrole', models.ForeignKey(orm[u'stacks.saltrole'], null=False))
        ))
        db.create_unique(u'stacks_host_roles', ['host_id', 'saltrole_id'])

        # Adding M2M table for field security_groups on 'Host'
        db.create_table(u'stacks_host_security_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('host', models.ForeignKey(orm[u'stacks.host'], null=False)),
            ('securitygroup', models.ForeignKey(orm[u'cloud.securitygroup'], null=False))
        ))
        db.create_unique(u'stacks_host_security_groups', ['host_id', 'securitygroup_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Stack', fields ['user', 'title']
        db.delete_unique(u'stacks_stack', ['user_id', 'title'])

        # Deleting model 'Stack'
        db.delete_table(u'stacks_stack')

        # Deleting model 'StackHistory'
        db.delete_table(u'stacks_stackhistory')

        # Deleting model 'SaltRole'
        db.delete_table(u'stacks_saltrole')

        # Deleting model 'Host'
        db.delete_table(u'stacks_host')

        # Removing M2M table for field roles on 'Host'
        db.delete_table('stacks_host_roles')

        # Removing M2M table for field security_groups on 'Host'
        db.delete_table('stacks_host_security_groups')


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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'stacks.host': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'Host'},
            'availability_zone': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': u"orm['cloud.CloudZone']"}),
            'cloud_profile': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': u"orm['cloud.CloudProfile']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'fqdn': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'instance_size': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': u"orm['cloud.CloudInstanceSize']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'provider_dns': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'roles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'hosts'", 'symmetrical': 'False', 'to': u"orm['stacks.SaltRole']"}),
            'security_groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'hosts'", 'symmetrical': 'False', 'to': u"orm['cloud.SecurityGroup']"}),
            'sir_id': ('django.db.models.fields.CharField', [], {'default': "'unknown'", 'max_length': '32'}),
            'sir_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2'}),
            'stack': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hosts'", 'to': u"orm['stacks.Stack']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'unknown'", 'max_length': '32'}),
            'status': ('model_utils.fields.StatusField', [], {'default': "'ok'", 'max_length': '100', 'no_check_for_status': 'True'}),
            'status_changed': ('model_utils.fields.MonitorField', [], {'default': 'datetime.datetime.now', 'monitor': "'status'"}),
            'status_detail': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'stacks.saltrole': {
            'Meta': {'ordering': "('-modified', '-created')", 'object_name': 'SaltRole'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'sls_path': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'stacks.stack': {
            'Meta': {'unique_together': "(('user', 'title'),)", 'object_name': 'Stack'},
            'cloud_provider': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stacks'", 'to': u"orm['cloud.CloudProvider']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hosts_file': ('core.fields.DeletingFileField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'map_file': ('core.fields.DeletingFileField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'pillar_file': ('core.fields.DeletingFileField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'slug': ('django_extensions.db.fields.AutoSlugField', [], {'allow_duplicates': 'False', 'max_length': '50', 'separator': "u'-'", 'blank': 'True', 'populate_from': "'title'", 'overwrite': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'top_file': ('core.fields.DeletingFileField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'stacks'", 'to': u"orm['auth.User']"})
        },
        u'stacks.stackhistory': {
            'Meta': {'ordering': "['-created', '-id']", 'object_name': 'StackHistory'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'event': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'stack': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'history'", 'to': u"orm['stacks.Stack']"}),
            'status': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['stacks']