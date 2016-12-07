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

from django.contrib.contenttypes.fields import GenericRelation
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
from stackdio.core.fields import JSONField

logger = logging.getLogger(__name__)


_environment_model_permissions = (
    'create',
    'admin',
)

_environment_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


class Environment(TimeStampedModel, TitleSlugDescriptionModel):

    model_permissions = _environment_model_permissions
    object_permissions = _environment_object_permissions

    class Meta:
        ordering = ('title',)
        default_permissions = tuple(set(_environment_model_permissions +
                                        _environment_object_permissions))

    labels = GenericRelation('core.Label')

    formula_versions = GenericRelation('formulas.FormulaVersion')

    # The properties for this blueprint
    properties = JSONField('Properties')
