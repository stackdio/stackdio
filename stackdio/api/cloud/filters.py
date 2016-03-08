# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

from stackdio.core.filters import OrFieldsFilter
from . import models


class CloudAccountFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_type='icontains')
    region = django_filters.CharFilter(name='region__title')
    q = OrFieldsFilter(field_names=('title', 'description', 'region__title', 'vpc_id'),
                       lookup_type='icontains')

    class Meta:
        model = models.CloudAccount
        fields = (
            'title',
            'region',
            'q',
        )


class CloudImageFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_type='icontains')
    q = OrFieldsFilter(field_names=('title', 'description', 'image_id'),
                       lookup_type='icontains')

    class Meta:
        model = models.CloudImage
        fields = (
            'title',
            'q',
        )


class CloudInstanceSizeFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_type='icontains')
    instance_id = django_filters.CharFilter(lookup_type='icontains')

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
    title = django_filters.CharFilter(lookup_type='icontains')

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

    class Meta:
        model = models.SecurityGroup
        fields = (
            'name',
            'description',
            'default',
            'managed',
        )


class SnapshotFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_type='icontains')
    q = OrFieldsFilter(field_names=('title', 'description', 'snapshot_id', 'size_in_gb',
                                    'filesystem_type'),
                       lookup_type='icontains')

    class Meta:
        model = models.Snapshot
        fields = (
            'title',
            'q',
        )
