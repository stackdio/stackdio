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

from django.db.models.query import QuerySet
from rest_framework.generics import get_object_or_404
from rest_framework.settings import api_settings

from .permissions import StackdioParentObjectPermissions

logger = logging.getLogger(__name__)


class ParentRelatedMixin(object):
    """
    Meant to be used on models that have a parent.
    """
    parent_queryset = None

    parent_lookup_field = 'pk'
    parent_lookup_url_kwarg = None

    parent_permission_classes = (StackdioParentObjectPermissions,)
    parent_filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    def get_parent_queryset(self):
        """
        Like get_queryset, but for the parent object
        """
        assert self.parent_queryset is not None, (
            "'%s' should either include a `parent_queryset` attribute, "
            "or override the `get_parent_queryset()` method."
            % self.__class__.__name__
        )

        queryset = self.parent_queryset
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset

    def get_parent_object(self):
        """
        Like get_object, but for the parent object
        """
        queryset = self.filter_parent_queryset(self.get_parent_queryset())

        # Perform the lookup filtering.
        default_parent_lookup_url_kwarg = 'parent_{}'.format(self.parent_lookup_field)
        parent_lookup_url_kwarg = self.parent_lookup_url_kwarg or default_parent_lookup_url_kwarg

        assert parent_lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.parent_lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, parent_lookup_url_kwarg)
        )

        filter_kwargs = {self.parent_lookup_field: self.kwargs[parent_lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        self.check_parent_object_permissions(self.request, obj)
        return obj

    def get_parent_permissions(self):
        """
        Like get_permissions, but for the parent object instead
        """
        return [permission() for permission in self.parent_permission_classes]

    def check_parent_object_permissions(self, request, obj):
        """
        Like check_object_permissions, but for the parent object instead
        """
        for permission in self.get_parent_permissions():
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    def filter_parent_queryset(self, queryset):
        """
        Like filter_queryset, but for the parent object instead
        """
        for backend in list(self.parent_filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset


class CreateOnlyFieldsMixin(object):

    def get_fields(self):
        fields = super(CreateOnlyFieldsMixin, self).get_fields()
        if self.instance is not None and hasattr(self.Meta, 'create_only_fields'):
            # If this is an update request, we want to set all the create_only_fields
            # specified in the Meta class to be read_only
            for field, instance in fields.items():
                if field in self.Meta.create_only_fields:
                    instance.read_only = True
        return fields


class SuperuserFieldsMixin(object):
    """
    Filters out the serialized fields found in `superuser_fields` if
    the authenticated user is *not* a superuser. For example, with
    the following Meta definition, the 'foo' field would be removed
    from serialization if the user is not a superuser.

    class Meta:
        fields = ('foo', 'bar', baz')
        superuser_fields = ('foo',)

    """
    def get_fields(self, *args, **kwargs):
        # Get the current set of fields as defined in the Meta class
        fields = super(SuperuserFieldsMixin, self).get_fields(*args, **kwargs)

        # If user is a superuser, let all fields go through
        if 'request' in self.context and self.context['request'].user.is_superuser:
            return fields

        # If superuser_fields has not been defined, keep the original
        if not hasattr(self, 'Meta') or not hasattr(self.Meta, 'superuser_fields'):
            return fields

        # Remove superuser fields from outgoing serializable fields
        superuser_fields = set(self.Meta.superuser_fields)
        regular_fields = set(fields.keys())
        for field_name in superuser_fields & regular_fields:
            fields.pop(field_name)

        return fields
