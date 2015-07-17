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

from stackdio.api.blueprints.models import Blueprint
from stackdio.api.formulas.models import Formula
from stackdio.api.stacks.models import Stack

logger = logging.getLogger(__name__)


class SearchResultTypeField(serializers.Field):  # pylint: disable=abstract-method
    """
    Tricks a read-only field into returning the value we want
    it to return instead of leveraging a value on the model.
    """
    def __init__(self, result_type):
        self.result_type = result_type
        super(SearchResultTypeField, self).__init__(source='pk')

    def to_representation(self, value):
        return self.result_type


class BlueprintSearchSerializer(serializers.HyperlinkedModelSerializer):
    result_type = SearchResultTypeField('blueprint')

    class Meta:
        model = Blueprint
        fields = ('id', 'url', 'title', 'description', 'result_type')


class FormulaSearchSerializer(serializers.HyperlinkedModelSerializer):
    result_type = SearchResultTypeField('formula')

    class Meta:
        model = Formula
        fields = ('id', 'url', 'title', 'description', 'result_type')


class StackSearchSerializer(serializers.HyperlinkedModelSerializer):
    result_type = SearchResultTypeField('stack')

    class Meta:
        model = Stack
        fields = ('id', 'url', 'title', 'description', 'result_type')
