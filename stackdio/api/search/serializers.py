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


import logging

from rest_framework import serializers

logger = logging.getLogger(__name__)


class PassThroughSerializer(serializers.Serializer):  # pylint: disable=abstract-method

    def to_representation(self, instance):
        return instance


class SearchSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    type = serializers.SlugRelatedField(slug_field='model', read_only=True)
    title = serializers.CharField()
    url = serializers.URLField()
    object = PassThroughSerializer()
