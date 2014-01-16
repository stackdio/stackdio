import logging
import yaml

from django.conf import settings
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

from django_extensions.db.models import (
    TimeStampedModel,
    TitleSlugDescriptionModel,
)
from queryset_transform import TransformManager, TransformQuerySet

from core.fields import DeletingFileField
from cloud.utils import get_provider_type_and_class
from .utils import get_cloud_provider_choices

logger = logging.getLogger(__name__)

FILESYSTEM_CHOICES = (
    ('ext2', 'ext2'),
    ('ext3', 'ext3'),
    ('ext4', 'ext4'),
    ('fuse', 'fuse'),
    ('xfs', 'xfs'),
)


def get_config_file_path(obj, filename):
    return obj.slug + '.conf'


class CloudProviderType(models.Model):
    PROVIDER_CHOICES = get_cloud_provider_choices()
    type_name = models.CharField(max_length=32,
                                 choices=PROVIDER_CHOICES,
                                 unique=True)

    def __unicode__(self):
        return self.type_name


class CloudProvider(TimeStampedModel, TitleSlugDescriptionModel):
    class Meta:
        unique_together = ('title', 'provider_type')

    # What is the type of provider (e.g., AWS, Rackspace, etc)
    provider_type = models.ForeignKey('CloudProviderType')

    # Used to store the provider-specifc YAML that will be written
    # to disk in settings.SALT_CLOUD_PROVIDERS_FILE
    yaml = models.TextField()

    # The default availability zone for this account, may be overridden
    # by the user at stack creation time
    default_availability_zone = models.ForeignKey('CloudZone',
                                                  related_name='default_zone',
                                                  null=True)

    # the account/owner id of the provider
    account_id = models.CharField(max_length=64)

    # salt-cloud provider configuration file
    config_file = DeletingFileField(
        max_length=255,
        upload_to=get_config_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.SALT_CLOUD_PROVIDERS_DIR))

    def __unicode__(self):
        return self.title

    def get_driver(self):
        # determine the type and implementation class for this provider
        ptype, pclass = get_provider_type_and_class(self.provider_type.id)

        # instantiate the implementation class and return it
        return pclass(self)

    def update_config(self):
        '''
        Writes the yaml configuration file for the given provider object.
        '''
        # update the provider object's security group information
        security_groups = [sg.name for sg in self.security_groups.filter(
            is_default=True
        )]
        provider_yaml = yaml.safe_load(self.yaml)
        provider_yaml[self.slug]['securitygroup'] = security_groups
        self.yaml = yaml.safe_dump(provider_yaml, default_flow_style=False)
        self.save()

        if not self.config_file:
            self.config_file.save(self.slug + '.conf',
                                  ContentFile(self.yaml))
        else:
            with open(self.config_file.path, 'w') as f:
                # update the yaml to include updated security group information
                f.write(self.yaml)


class CloudInstanceSize(TitleSlugDescriptionModel):
    class Meta:
        ordering = ['id']

    # `title` field will be the type used by salt-cloud for the `size`
    # parameter in the providers yaml file (e.g., 'Micro Instance' or
    # '512MB Standard Instance'

    # link to the type of provider for this instance size
    provider_type = models.ForeignKey('CloudProviderType')

    # The underlying size ID of the instance (e.g., t1.micro)
    instance_id = models.CharField(max_length=64)

    def __unicode__(self):

        return '{0} ({1})'.format(self.title, self.instance_id)


class CloudProfile(TimeStampedModel, TitleSlugDescriptionModel):
    class Meta:
        unique_together = ('title', 'cloud_provider')

    # What cloud provider is this under?
    cloud_provider = models.ForeignKey('CloudProvider',
                                       related_name='profiles')

    # The underlying image id of this profile (e.g., ami-38df83a')
    image_id = models.CharField(max_length=64)

    # The default instance size of this profile, may be overridden
    # by the user at creation time
    default_instance_size = models.ForeignKey('CloudInstanceSize')

    # The SSH user that will have default access to the box. Salt-cloud
    # needs this to provision the box as a salt-minion and connect it
    # up to the salt-master automatically.
    ssh_user = models.CharField(max_length=64)

    # salt-cloud profile configuration file
    config_file = DeletingFileField(
        max_length=255,
        upload_to=get_config_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.SALT_CLOUD_PROFILES_DIR))

    def __unicode__(self):
        return self.title

    def update_config(self):
        '''
        Writes the salt-cloud profile configuration file
        '''

        profile_yaml = {}
        profile_yaml[self.slug] = {
            'provider': self.cloud_provider.slug,
            'image': self.image_id,
            'size': self.default_instance_size.title,
            'ssh_username': self.ssh_user,
            'script': settings.STACKDIO_CONFIG['SALT_CLOUD_BOOTSTRAP_SCRIPT'],
            'script_args': settings.STACKDIO_CONFIG['SALT_CLOUD_BOOTSTRAP_ARGS'],  # NOQA
            'sync_after_install': 'all',
            # PI-44: Need to add an empty minion config until salt-cloud/701
            # is fixed.
            'minion': {},
        }
        profile_yaml = yaml.safe_dump(profile_yaml,
                                      default_flow_style=False)

        if not self.config_file:
            self.config_file.save(self.slug + '.conf',
                                  ContentFile(profile_yaml))
        else:
            with open(self.config_file.path, 'w') as f:
                # update the yaml to include updated security group information
                f.write(profile_yaml)

    def get_driver(self):
        return self.cloud_provider.get_driver()


class Snapshot(TimeStampedModel, TitleSlugDescriptionModel):

    class Meta:
        unique_together = ('snapshot_id', 'cloud_provider')

    # The cloud provider that has access to this snapshot
    cloud_provider = models.ForeignKey('cloud.CloudProvider',
                                       related_name='snapshots')

    # The snapshot id. Must exist already, be preformatted, and available
    # to the associated cloud provider
    snapshot_id = models.CharField(max_length=32)

    # How big the snapshot is...this doesn't actually affect the actual
    # volume size, but mainly a useful hint to the user
    size_in_gb = models.IntegerField()

    # the type of file system the volume uses
    filesystem_type = models.CharField(max_length=16,
                                       choices=FILESYSTEM_CHOICES)


class CloudZone(TitleSlugDescriptionModel):

    class Meta:
        unique_together = ('title', 'provider_type')

    # link to the type of provider for this zone
    provider_type = models.ForeignKey('cloud.CloudProviderType')

    def __unicode__(self):
        return self.title


class SecurityGroupQuerySet(TransformQuerySet):

    def with_rules(self):
        logger.debug('SecurityGroupQuerySet::with_rules called...')
        return self.transform(self._inject_rules)

    def _inject_rules(self, queryset):
        '''
        Pull all the security group rules using the cloud provider's
        implementation.
        '''
        by_provider = {}
        for group in queryset:
            by_provider.setdefault(group.cloud_provider, []).append(group)

        for provider, groups in by_provider.iteritems():
            names = [group.name for group in groups]
            driver = provider.get_driver()
            provider_groups = driver.get_security_groups(names)

            # add in the rules
            for group in groups:
                group.rules = provider_groups[group.name]['rules']


class SecurityGroupManager(TransformManager):

    def get_query_set(self):
        return SecurityGroupQuerySet(self.model)


class SecurityGroup(TimeStampedModel, models.Model):

    class Meta:
        unique_together = ('name', 'cloud_provider')
    objects = SecurityGroupManager()

    # Name of the security group (REQUIRED)
    name = models.CharField(max_length=255)

    # Description of the security group (REQUIRED)
    description = models.CharField(max_length=255)

    # ID given by the provider
    # NOTE: This will be set automatically after it has been created on the
    # provider and will be ignored if passed in
    group_id = models.CharField(max_length=16, blank=True)

    # the cloud provider for this group
    cloud_provider = models.ForeignKey('cloud.CloudProvider',
                                       related_name='security_groups')

    # the owner of this security group
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              related_name='security_groups')

    # ADMIN-ONLY: setting this to true will cause this security group
    # to be added automatically to all machines that get started in
    # the related cloud provider
    is_default = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def get_active_hosts(self):
        return self.hosts.count()

    def rules(self):
        '''
        Pulls the security groups using the cloud provider
        '''
        logger.debug('SecurityGroup::rules called...')
        driver = self.cloud_provider.get_driver()
        return driver.get_security_groups([self.name])[self.name]['rules']
