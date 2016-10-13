# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

import git
import six
import yaml
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.cache import cache
from django.db import models
from django.dispatch import receiver
from django.utils.lru_cache import lru_cache
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
from model_utils import Choices
from model_utils.models import StatusModel

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

    def create(self, **kwargs):
        kwargs['status'] = Formula.IMPORTING
        kwargs['status_detail'] = 'Importing formula...this could take a while.'

        formula = super(FormulaQuerySet, self).create(**kwargs)

        # Fix circular import issue
        from . import tasks

        # Start up the task to import the formula
        tasks.import_formula.si(formula.id).apply_async()

        return formula

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
class Formula(TimeStampedModel, TitleSlugDescriptionModel, StatusDetailModel):
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
    ERROR = 'error'
    COMPLETE = 'complete'
    IMPORTING = 'importing'
    STATUS = Choices(ERROR, COMPLETE, IMPORTING)

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
            '{0}-{1}'.format(self.pk, self.get_repo_name()),
        )

        if not os.path.exists(root_dir):
            os.makedirs(root_dir)
        return root_dir

    def get_repos_dir(self):
        return os.path.join(
            self.get_root_dir(),
            'checkouts',
        )

    def get_repo_name(self):
        return os.path.splitext(os.path.split(self.uri)[-1])[0]

    def get_repo_env(self):
        repo_env = {}

        if self.ssh_private_key:
            ssh_key_file = os.path.join(self.get_root_dir(), 'id_rsa')
            with open(ssh_key_file, 'w') as f:
                f.write(self.ssh_private_key)

            # fix permissions on the private key
            os.chmod(ssh_key_file, 0o600)

            # Create our ssh wrapper script to make ssh w/ private key work
            git_wrapper = os.path.join(self.get_root_dir(), 'git.sh')
            with open(git_wrapper, 'w') as f:
                f.write('#!/bin/bash\n')
                f.write('SSH=$(which ssh)\n')
                f.write('exec $SSH -o StrictHostKeyChecking=no -i {} "$@"\n'.format(ssh_key_file))

            # Make the git wrapper executable
            os.chmod(git_wrapper, 0o755)

            repo_env['GIT_SSH'] = git_wrapper

        return repo_env

    def get_repo_from_directory(self, repo_dir):
        if not os.path.exists(repo_dir):
            return None

        repo = git.Repo(repo_dir)

        repo.git.update_environment(**self.get_repo_env())

        return repo

    @lru_cache()
    def get_repo(self, version=None):
        version = version or 'HEAD'

        repo_dir = os.path.join(self.get_repos_dir(), version)

        return self.get_repo_from_directory(repo_dir)

    def clone_to(self, to_path, *args, **kwargs):
        repo_env = self.get_repo_env()

        if 'env' in kwargs:
            kwargs['env'].update(repo_env)
        else:
            kwargs['env'] = repo_env

        repo = git.Repo.clone_from(self.uri, to_path, *args, **kwargs)

        # Now update the environment on the actual repo object
        repo.git.update_environment(**repo_env)

        return repo

    def get_valid_versions(self):
        main_repo = self.get_repo()

        if main_repo is None:
            return []

        remote = main_repo.remote()

        # This will grab all the remote branches & tags
        refs = set()

        # First get all the remote branches
        for r in remote.refs:
            refs.add(r.remote_head)

        # Then get all the tags
        for t in main_repo.tags:
            refs.add(t.name)

        # remove HEAD as a valid version
        refs.remove('HEAD')

        return list(refs)

    @property
    def default_version(self):
        default_repo = self.get_repo()

        if default_repo is None:
            return None

        # This will be the name of the default branch.
        return default_repo.remote().refs.HEAD.ref.remote_head

    def components(self, version=None):
        repo = self.get_repo(version)

        if repo is None:
            return {}

        cache_key = 'formula-{}-components-{}-{}'.format(self.id, version, repo.head.commit)

        cached_components = cache.get(cache_key)

        if cached_components:
            return cached_components

        with open(os.path.join(repo.working_dir, 'SPECFILE')) as f:
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
            cache.set(cache_key, ret, 10)
            return ret

    @classmethod
    def all_components(cls, versions=()):
        version_map = {}

        # Build the map of formula -> version
        for version in versions:
            version_map[version.formula] = version.version

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
        with open(os.path.join(self.get_repos_dir(), version, 'SPECFILE')) as f:
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


@receiver(models.signals.post_delete, sender=Formula)
def cleanup_formula(sender, instance, **kwargs):
    """
    Utility method to clean up the cloned formula repository when
    the formula is deleted.
    """

    repos_dir = instance.get_root_dir()
    logger.debug('cleanup_formula called. Path to remove: {0}'.format(repos_dir))
    if os.path.isdir(repos_dir):
        rmtree(repos_dir)
