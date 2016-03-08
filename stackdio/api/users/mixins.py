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

from rest_framework.generics import get_object_or_404

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class UserRelatedMixin(object):

    def get_user(self):
        queryset = get_user_model().objects.all()

        obj = get_object_or_404(queryset, username=self.kwargs.get('username'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_user()


class GroupRelatedMixin(object):

    def get_group(self):
        queryset = Group.objects.all()

        obj = get_object_or_404(queryset, name=self.kwargs.get('name'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_group()
