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

from guardian.shortcuts import get_groups_with_perms, get_users_with_perms

logger = logging.getLogger(__name__)


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
        if not hasattr(self, 'Meta') or not hasattr(self.Meta,
                                                    'superuser_fields'):
            return fields

        # Remove superuser fields from outgoing serializable fields
        superuser_fields = set(self.Meta.superuser_fields)
        regular_fields = set(fields.keys())
        for field_name in superuser_fields & regular_fields:
            fields.pop(field_name)

        return fields


class StackdioPermissionedObjectMixin(object):
    """
    Provides generic functions needed by permission API endpoints
    """
    user_or_group = None

    def get_user_or_group(self):
        assert self.user_or_group in ('user', 'group'), (
            "'%s' should include a `user_or_group` attribute that is one of 'user' or 'group'."
            % self.__class__.__name__
        )
        return self.user_or_group

    def switch_user_group(self, if_user, if_group):
        if self.get_user_or_group() == 'user':
            return if_user
        elif self.get_user_or_group() == 'group':
            return if_group
        else:
            raise ValueError(
                "'%s' should include a `user_or_group` attribute that is one of 'user' or 'group'."
                % self.__class__.__name__
            )

    def get_permissioned_object(self):
        raise NotImplementedError('`get_permissioned_object()` must be implemented.')

    def _transform_perm(self, model_name):
        def do_tranform(item):
            perm, sep, empty = item.partition('_' + model_name)
            return perm

        return do_tranform

    def get_queryset(self):
        obj = self.get_permissioned_object()
        model_name = obj._meta.model_name

        # Grab the perms for either the users or groups
        perm_map = self.switch_user_group(
            get_users_with_perms(obj, attach_perms=True),
            get_groups_with_perms(obj, attach_perms=True),
        )

        ret = []
        for auth_obj, perms in perm_map.items():
            ret.append({
                self.get_user_or_group(): auth_obj,
                'permissions': map(self._transform_perm(model_name), perms),
            })
        return ret
