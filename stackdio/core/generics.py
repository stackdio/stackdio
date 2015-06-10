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

from django.http import Http404
from guardian.shortcuts import remove_perm
from rest_framework import generics

from . import mixins


class StackdioObjectPermissionsListAPIView(mixins.StackdioPermissionedObjectMixin,
                                           generics.ListAPIView):

    def list(self, request, *args, **kwargs):
        response = super(StackdioObjectPermissionsListAPIView, self).list(request,
                                                                          *args,
                                                                          **kwargs)
        # add available permissions to the response
        obj = self.get_permissioned_object()
        response.data['available_permissions'] = sorted(obj.object_permissions)

        return response


class StackdioObjectPermissionsDetailAPIView(mixins.StackdioPermissionedObjectMixin,
                                             generics.RetrieveUpdateDestroyAPIView):

    @property
    def lookup_field(self):
        return self.switch_user_group('username', 'groupname')

    def get_object(self):
        queryset = self.get_queryset()

        for obj in queryset:
            auth_obj = obj[self.get_user_or_group()]
            name_attr = self.switch_user_group('username', 'name')

            if self.kwargs[self.lookup_field] == getattr(auth_obj, name_attr):
                return obj

        raise Http404('No permissions found for %s' % self.kwargs[self.lookup_field])

    def perform_update(self, serializer):
        serializer.save(object=self.get_permissioned_object())

    def perform_destroy(self, instance):
        obj = self.get_permissioned_object()
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name
        for perm in instance['permissions']:
            remove_perm('%s.%s_%s' % (app_label, perm, model_name),
                        instance[self.get_user_or_group()],
                        obj)
