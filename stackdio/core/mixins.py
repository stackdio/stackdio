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
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .permissions import StackdioParentPermissions

logger = logging.getLogger(__name__)


class ParentRelatedMixin(object):
    """
    Meant to be used on models that have a parent.
    """
    parent_queryset = None

    parent_lookup_field = 'pk'
    parent_lookup_url_kwarg = None

    permission_classes = (StackdioParentPermissions,)

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
        queryset = self.get_parent_queryset()

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

        # NOTE:  NOT GOING TO CHECK PERMISSIONS HERE
        # The permission class *should* call get_parent_object and check permissions on it.

        return get_object_or_404(queryset, **filter_kwargs)


class BulkUpdateModelMixin(object):
    """
    Mixin to allow for bulk updates on list endpoints
    """

    # Things for bulk updates
    def bulk_update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        # restrict the update to the filtered queryset
        serializer = self.get_serializer(
            self.filter_queryset(self.get_queryset()),
            data=request.data,
            many=True,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_bulk_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.bulk_update(request, *args, **kwargs)

    def perform_bulk_update(self, serializer):
        return self.perform_update(serializer)


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
