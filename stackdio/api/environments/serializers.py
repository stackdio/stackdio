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

from django.db import transaction
from rest_framework import serializers
from stackdio.api.formulas.serializers import FormulaComponentSerializer, FormulaVersionSerializer
from stackdio.core.serializers import (
    PropertiesField,
    StackdioHyperlinkedModelSerializer,
    StackdioLabelSerializer,
    StackdioLiteralLabelsSerializer,
)

from . import models

logger = logging.getLogger(__name__)


class EnvironmentSerializer(StackdioHyperlinkedModelSerializer):

    label_list = StackdioLiteralLabelsSerializer(read_only=True, many=True, source='labels')

    properties = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-properties')
    formula_versions = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-formula-versions',
        lookup_url_kwarg='parent_pk')
    labels = serializers.HyperlinkedIdentityField(
        view_name='api:environments:environment-label-list',
        lookup_url_kwarg='parent_pk')

    class Meta:
        model = models.Environment
        fields = (
            'url',
            'title',
            'description',
            'label_list',
            'properties',
            'labels',
            'formula_versions',
        )


class FullEnvironmentSerializer(EnvironmentSerializer):

    properties = PropertiesField(required=False)
    formula_versions = FormulaVersionSerializer(many=True, required=False)
    labels = StackdioLiteralLabelsSerializer(many=True, required=False)

    def create(self, validated_data):
        # Pull out the nested stuff
        formula_versions = validated_data.pop('formula_versions', [])
        labels = validated_data.pop('labels', [])

        with transaction.atomic(using=models.Environment.objects.db):
            # Create the environment
            environment = super(FullEnvironmentSerializer, self).create(validated_data)

            # Create the formula versions
            formula_version_field = self.fields['formula_versions']
            # Add in the environment to all the formula versions
            for formula_version in formula_versions:
                formula_version['content_object'] = environment
            formula_version_field.create(formula_versions)

            # Create the labels
            label_field = self.fields['labels']
            # Add in the environment to all the labels
            for label in labels:
                label['content_object'] = environment
            label_field.create(labels)

        # Add the other fields back in for deserialization
        validated_data['formula_versions'] = formula_versions
        validated_data['labels'] = labels

        return environment

    def to_representation(self, instance):
        super_serializer = EnvironmentSerializer(instance, context=self.context)
        return super_serializer.to_representation(instance)


class EnvironmentLabelSerializer(StackdioLabelSerializer):

    class Meta(StackdioLabelSerializer.Meta):
        app_label = 'environments'
        model_name = 'environment-label'
