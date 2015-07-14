# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import django_filters
from cloud import models


class CloudAccountFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_type='icontains')
    region = django_filters.CharFilter(name='region__title')

    class Meta:
        model = models.CloudAccount
        fields = (
            'title',
            'region',
        )


class CloudProfileFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_type='icontains')

    class Meta:
        model = models.CloudProfile
        fields = (
            'title',
        )


class CloudInstanceSizeFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_type='icontains')

    class Meta:
        model = models.CloudInstanceSize
        fields = (
            'title',
            'instance_id',
        )


class CloudRegionFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_type='icontains')

    class Meta:
        model = models.CloudRegion
        fields = (
            'title',
        )


class CloudZoneFilter(django_filters.FilterSet):

    class Meta:
        model = models.CloudZone
        fields = (
            'title',
        )


class SecurityGroupFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_type='icontains')
    description = django_filters.CharFilter(lookup_type='icontains')
    default = django_filters.BooleanFilter(name='is_default')
    managed = django_filters.BooleanFilter(name='is_managed')
    account = django_filters.CharFilter(name='account__title')

    class Meta:
        model = models.SecurityGroup
        fields = (
            'name',
            'description',
            'default',
            'managed',
            'account',
        )
