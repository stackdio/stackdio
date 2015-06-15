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

from rest_framework.generics import get_object_or_404

from . import models, permissions


class CloudProviderRelatedMixin(object):
    permission_classes = (permissions.CloudProviderParentObjectPermissions,)

    def get_cloudprovider(self):
        queryset = models.CloudProvider.objects.all()

        obj = get_object_or_404(queryset, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_cloudprovider()


class CloudProfileRelatedMixin(object):

    def get_cloudprofile(self):
        queryset = models.CloudProfile.objects.all()

        obj = get_object_or_404(queryset, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_cloudprofile()


class SnapshotRelatedMixin(object):

    def get_snapshot(self):
        queryset = models.Snapshot.objects.all()

        obj = get_object_or_404(queryset, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_snapshot()
