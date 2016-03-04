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

import django_filters

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from stackdio.core.filters import OrFieldsFilter


class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_type='icontains')
    first_name = django_filters.CharFilter(lookup_type='icontains')
    last_name = django_filters.CharFilter(lookup_type='icontains')
    q = OrFieldsFilter(field_names=('username', 'first_name', 'last_name', 'email'),
                       lookup_type='icontains')

    class Meta:
        model = get_user_model()
        fields = (
            'username',
            'first_name',
            'last_name',
            'q',
        )


class GroupFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_type='icontains')
    q = OrFieldsFilter(field_names=('name',), lookup_type='icontains')

    class Meta:
        model = Group
        fields = (
            'name',
            'q',
        )
