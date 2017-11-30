# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
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
#

from __future__ import unicode_literals

import logging
import os
from collections import OrderedDict
from shutil import rmtree

import salt.config
import six
import yaml
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.dispatch import receiver
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
from model_utils.models import StatusModel
from stackdio.api.formulas import utils
from stackdio.core.models import SearchQuerySet

logger = logging.getLogger(__name__)


@six.python_2_unicode_compatible
class FormulaVersion(models.Model):
    class Meta:
        default_permissions = ()

    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    formula = models.ForeignKey('formulas.Formula')
    version = models.CharField('Formula Version', max_length=100)

    def __str__(self):
        return six.text_type('{}, version {}'.format(self.formula, self.version))


class StatusDetailModel(StatusModel):
    status_detail = models.TextField(blank=True)

    class Meta:
        abstract = True

        default_permissions = ()

    def set_status(self, status, detail=''):
        self.status = status
        self.status_detail = detail
        return self.save()


_formula_model_permissions = (
    'create',
    'admin',
)

_formula_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


class FormulaQuerySet(SearchQuerySet):
    """
    Override create to automatically kick off a celery task to clone the formula repository.
    """
    searchable_fields = ('title', 'description', 'uri')

    def search(self, query):
        result = super(FormulaQuerySet, self).search(query)

        # Find formula component matches
        formula_ids = []
        for formula in self.all():
            for sls_path, component in formula.components(formula.default_version).items():
                if query.lower() in sls_path.lower():
                    formula_ids.append(formula.id)
                elif query.lower() in component['title'].lower():
                    formula_ids.append(formula.id)
                elif query.lower() in component['description'].lower():
                    formula_ids.append(formula.id)

        component_matches = self.filter(id__in=formula_ids)

        # Or them together and return
        return (result or component_matches).distinct()


@six.python_2_unicode_compatible
class Formula(TimeStampedModel, TitleSlugDescriptionModel):
    """
    The intention here is to be able to install an entire formula along
    with identifying the individual components that may be installed
    with the formula. For example, a simple formula like EPEL may
    only have one SLS file that sets up the EPEL repository, while a
    more complicated formula for Hadoop should be able to install
    the complete set of Hadoop components on a single machine or
    install the individual NameNode, DataNode, etc on to individual
    machines.

    The problem right now is that salt formula (a packaging convention
    defined by saltstack) doesn't make it easy to pick out those
    individual components. So, to make things easier for stackd.io
    we're proposing a SPECFILE that would allow formulas to define
    a mapping of their components, with a name, description, etc. Then,
    when stackd.io is importing a formula from an external repository,
    we can read that SPECFILE and build up the entries in the database
    for allowing users to choose the entire formula or the installable
    components in the formula. For more on Formula and the packaging
    please see the following link:

        http://docs.saltstack.com/topics/conventions/formulas.html

    The SPECFILE we're proposing is simple, it maps the top-level
    formula to all of its individual components that may be installed
    separately. Formula must still be written in a way that these
    componenets are useful across multiple machines. The SPECFILE
    is a YAML file that looks like:

    formula_name:                   # the top-level formula identifier
      name: <string>                # a human-readable name of the formula
      description: <string>         # a description of the formula
      root_path: <string>           # the root directory of the formula
      components:                   # a list of components that may be
                                    # installed separately
        - name: <string>
          description: <string>
          sls_path: <string>        # the path to the SLS for this component
                                    # using standard stal dot notation
        - name: <string>
          description: <string>
          sls_path: <string>
        ...
        more components
        ...

    ##
    # Example to install CDH4 or its components
    ##

    name: CDH4
    description: Formula to install a complete CDH4 system on a
                 single machine, or use the individual components to
                 install them on separate machines for a distributed
                 Hadoop system.
    root_path: cdh4
    components:
      - name: Hadoop
        description: This component installs the entire Hadoop system.
        sls_path: cdh4.hadoop
      - name: Hadoop NameNode
        description: The NameNode component of the CDH4 formula.
        sls_path: cdh4.hadoop.namenode
      - name: Hadoop DataNode
        description: The DataNode component of the CDH4 formula.
        sls_path: cdh4.hadoop.datanode
      - name: HBase
        description: This component installs the entire HBase system.
        sls_path: cdh4.hbase
      - name: HBase Master
        description: The Master component of the CDH4 formula.
        sls_path: cdh4.hbase.master
      - name: HBase RegionServer
        description: The RegionServer component of the CDH4 formula.
        sls_path: cdh4.hbase.regionserver

    """
    model_permissions = _formula_model_permissions
    object_permissions = _formula_object_permissions

    class Meta:
        ordering = ['title']

        default_permissions = tuple(set(_formula_model_permissions + _formula_object_permissions))

    objects = FormulaQuerySet.as_manager()

    # uri to the repository for this formula
    uri = models.URLField('Repository URI', unique=True)

    # All components in this formula should start with this prefix
    root_path = models.CharField('Root Path', max_length=64)

    ssh_private_key = models.TextField('SSH Private Key', blank=True)

    def __str__(self):
        return six.text_type('{} ({})'.format(self.title, self.uri))

    def get_root_dir(self):
        root_dir = os.path.join(
            settings.FILE_STORAGE_DIRECTORY,
            'formulas',
            six.text_type(self.pk),
        )

        if not os.path.exists(root_dir):
            os.makedirs(root_dir)
        return root_dir

    def get_gitfs(self):
        return utils.get_gitfs(self.uri, self.ssh_private_key, self)

    def get_valid_versions(self):
        gitfs = self.get_gitfs()
        return gitfs.envs()

    @property
    def default_version(self):
        return 'base'

    def components(self, version=None):
        gitfs = self.get_gitfs()

        version = version or self.default_version

        fnd = gitfs.find_file('SPECFILE', tgt_env=version)

        if not os.path.exists(fnd['path']):
            # If the path doesn't exist, update & retry
            gitfs.update()
            fnd = gitfs.find_file('SPECFILE', tgt_env=version)

        with open(fnd['path']) as f:
            yaml_data = yaml.safe_load(f)
            ret = OrderedDict()
            # Create a map of sls_path -> component pairs
            sorted_components = sorted(yaml_data.get('components', []), key=lambda x: x['title'])
            for component in sorted_components:
                ret[component['sls_path']] = OrderedDict((
                    ('title', component['title']),
                    ('description', component['description']),
                    ('sls_path', component['sls_path']),
                ))
            return ret

    @classmethod
    def all_components(cls, version_map=None):
        version_map = version_map or {}

        ret = {}
        for formula in cls.objects.all():
            if formula in version_map:
                # Use the specified version
                components = formula.components(version_map[formula])
            else:
                # Otherwise use the default version
                components = formula.components(formula.default_version)

            for component in components:
                ret.setdefault(component, []).append(formula)
        return ret

    def properties(self, version):
        gitfs = self.get_gitfs()

        version = version or self.default_version

        fnd = gitfs.find_file('SPECFILE', tgt_env=version)

        if not os.path.exists(fnd['path']):
            # If the path doesn't exist, update & retry
            gitfs.update()
            fnd = gitfs.find_file('SPECFILE', tgt_env=version)

        with open(fnd['path']) as f:
            yaml_data = yaml.safe_load(f)
            return yaml_data.get('pillar_defaults', {})


@six.python_2_unicode_compatible
class FormulaComponent(TimeStampedModel):
    """
    An extension of an existing FormulaComponent to add additional metadata
    for those components based on this blueprint. In particular, this is how
    we track the order in which the formula should be provisioned in a
    blueprint.
    """

    class Meta:
        verbose_name_plural = 'formula components'
        ordering = ['order']

        default_permissions = ()

    # The formula component we're extending
    formula = models.ForeignKey('formulas.Formula')
    sls_path = models.CharField(max_length=255)

    # The host definition / cloud account this formula component is associated with
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    # The order in which the component should be provisioned
    order = models.IntegerField('Order', default=0)

    def __str__(self):
        return six.text_type('{0}:{1}'.format(
            self.sls_path,
            self.content_object,
        ))

    @property
    def title(self):
        if not hasattr(self, '_full_component'):
            version = self.formula.default_version
            self._full_component = self.formula.components(version)[self.sls_path]
        return self._full_component['title']

    @property
    def description(self):
        if not hasattr(self, '_full_component'):
            version = self.formula.default_version
            self._full_component = self.formula.components(version)[self.sls_path]
        return self._full_component['description']

    def get_metadata_for_host(self, host):
        """
        Get the current status of a given host
        """
        return self.metadatas.filter(host=host).order_by('-modified').first()


##
# Signal events and handlers
##


@receiver(models.signals.post_save, sender=Formula)
def formula_post_save(sender, instance, **kwargs):
    """
    Utility method to clone the formula once it is saved.  We do this here so that the POST
    request to create the formula returns immediately, letting the update wait
    """
    # Go ahead and update the gitfs
    instance.get_gitfs().update()


@receiver(models.signals.post_delete, sender=Formula)
def cleanup_formula(sender, instance, **kwargs):
    """
    Utility method to clean up the cloned formula repository when
    the formula is deleted.
    """

    repos_dir = instance.get_root_dir()
    if os.path.isdir(repos_dir):
        rmtree(repos_dir)

    opts = salt.config.client_config(settings.STACKDIO_CONFIG.salt_master_config)

    gitfs_cachedir = os.path.join(opts['cachedir'],
                                  'stackdio',
                                  'formulas',
                                  six.text_type(instance.id))

    if os.path.isdir(gitfs_cachedir):
        rmtree(gitfs_cachedir)
