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
#


import logging
from os.path import join, isdir, split, splitext
from shutil import rmtree

import yaml
from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
from model_utils import Choices

from stacks.models import StatusDetailModel


logger = logging.getLogger(__name__)


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
    we're proposing a SPECIFILE that would allow formulas to define
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
    ERROR       = 'error'
    COMPLETE    = 'complete'
    IMPORTING   = 'importing'
    STATUS      = Choices(ERROR, COMPLETE, IMPORTING)

    class Meta:
        ordering = ['pk']

    # owner of the formula
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              related_name='formulas')

    # publicly available to other users?
    public = models.BooleanField(default=False)

    # uri to the repository for this formula
    uri = models.CharField(max_length=255)

    # root path of where this formula exists
    root_path = models.CharField(max_length=64)

    git_username = models.CharField(max_length=64, blank=True)

    access_token = models.BooleanField(default=False)

    def __unicode__(self):
        return '{0} ({1})'.format(self.title, self.owner.username)

    def get_repo_dir(self):
        return join(settings.STACKDIO_CONFIG.salt_user_states,
                    self.owner.username,
                    self.get_repo_name())

    def get_repo_name(self):
        return splitext(split(self.uri)[-1])[0]

    @property
    def private_git_repo(self):
        return self.git_username != ''

    @property
    def properties(self):
        with open(join(self.get_repo_dir(), 'SPECFILE')) as f:
            yaml_data = yaml.safe_load(f)
            return yaml_data.get('pillar_defaults', {})


class FormulaComponent(TitleSlugDescriptionModel):
    """
    Mapping of individual components of a formula
    """

    class Meta:
        ordering = ['pk']

    formula = models.ForeignKey('formulas.Formula',
                                related_name='components')

    # Formula packaging is a convention set by saltstack directly, so
    # please see the URL above on the documentation for Formulas
    sls_path = models.CharField(max_length=255)

    def __unicode__(self):
        return u'{0} : {1}'.format(self.title, self.sls_path)


##
# Signal events and handlers
##

@receiver(models.signals.post_delete, sender=Formula)
def cleanup_formula(sender, instance, **kwargs):
    """
    Utility method to clean up the cloned formula repository when
    the formula is deleted.
    """

    repo_dir = instance.get_repo_dir()
    logger.debug('cleanup_formula called. Path to remove: {0}'.format(repo_dir))
    if isdir(repo_dir):
        rmtree(repo_dir)

