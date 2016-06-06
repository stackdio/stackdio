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

from functools import reduce
from operator import or_

import django_filters
import six
from django.db.models import Q
from django_filters.fields import Lookup


class OrFieldsFilter(django_filters.Filter):

    def __init__(self, include_labels=False, *args, **kwargs):
        field_names = kwargs.pop('field_names', ())
        # Default distinct to true here, since this is a common issue with this filter
        kwargs.setdefault('distinct', True)
        self.field_names = field_names
        self.include_labels = include_labels
        super(OrFieldsFilter, self).__init__(*args, **kwargs)

    def filter(self, qs, value):  # pylint: disable=method-hidden
        if isinstance(value, Lookup):
            lookup = six.text_type(value.lookup_type)
            value = value.value
        else:
            lookup = self.lookup_type
        if value in ([], (), {}, None, ''):
            return qs

        q_objects = []
        for field in self.field_names:
            q_objects.append(Q(**{'%s__%s' % (field, lookup): value}))

        if self.include_labels:
            if ':' in value:
                k, v = value.split(':')
                v = v if v else None
            else:
                k, v = value, None

            if v is None:
                q_objects.append(Q(**{'labels__key__%s' % lookup: k}))
            else:
                q_objects.append(Q(**{
                    'labels__key': k,
                    'labels__value__%s' % lookup: v,
                }))

        qs = self.get_method(qs)(reduce(or_, q_objects))
        if self.distinct:
            qs = qs.distinct()
        return qs


class LabelFilterMixin(object):

    def filter_label(self, queryset, value):
        if ':' in value:
            k, v = value.split(':')
            v = v if v else None
        else:
            k, v = value, None

        if v is None:
            return queryset.filter(labels__key=k)
        else:
            return queryset.filter(labels__key=k, labels__value=v)
