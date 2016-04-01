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

from rest_framework.generics import get_object_or_404

from . import models, permissions


class StackRelatedMixin(object):
    permission_classes = (permissions.StackParentObjectPermissions,)

    def get_stack(self, check_permissions=True):
        queryset = models.Stack.objects.all()

        obj = get_object_or_404(queryset, id=self.kwargs.get('pk'))
        if check_permissions:
            self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_stack()
