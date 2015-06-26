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

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import fields


class UserField(fields.Field):

    def __init__(self, **kwargs):
        super(UserField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return get_user_model().objects.get(username=data)

    def to_representation(self, value):
        return value.username


class GroupField(fields.Field):

    def __init__(self, **kwargs):
        super(GroupField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return Group.objects.get(name=data)

    def to_representation(self, value):
        return value.name
