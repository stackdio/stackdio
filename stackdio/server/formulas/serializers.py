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

from rest_framework import serializers

from . import models

logger = logging.getLogger(__name__)


class FormulaComponentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.FormulaComponent
        fields = (
            'id',
            'title',
            'description',
            'formula',
            'sls_path',
        )


class FormulaSerializer(serializers.HyperlinkedModelSerializer):
    # Plain read only fields
    title = serializers.ReadOnlyField()
    description = serializers.ReadOnlyField()
    private_git_repo = serializers.ReadOnlyField()
    root_path = serializers.ReadOnlyField()
    status = serializers.ReadOnlyField()
    status_detail = serializers.ReadOnlyField()

    # Special read only fields
    owner = serializers.ReadOnlyField(source='owner.username')
    components = FormulaComponentSerializer(many=True, read_only=True)

    # Other fields
    properties = serializers.HyperlinkedIdentityField(view_name='formula-properties')
    action = serializers.HyperlinkedIdentityField(view_name='formula-action')

    class Meta:
        model = models.Formula
        fields = (
            'id',
            'url',
            'title',
            'description',
            'owner',
            'uri',
            'public',
            'git_username',
            'private_git_repo',
            'access_token',
            'root_path',
            'created',
            'modified',
            'status',
            'status_detail',
            'action',
            'properties',
            'components',
        )


class FormulaPropertiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Formula
        fields = (
            'properties',
        )
