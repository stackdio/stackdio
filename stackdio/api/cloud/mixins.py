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

import logging

from rest_framework.generics import get_object_or_404

from . import models, permissions

logger = logging.getLogger(__name__)


class CloudProviderRelatedMixin(object):
    permission_classes = (permissions.CloudProviderParentObjectPermissions,)

    def get_cloudprovider(self):
        queryset = models.CloudProvider.objects.all()

        obj = get_object_or_404(queryset, name=self.kwargs.get('name'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_cloudprovider()


class CloudRegionRelatedMixin(object):

    def get_cloudregion(self):
        queryset = models.CloudRegion.objects.all()

        obj = get_object_or_404(queryset, title=self.kwargs.get('title'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_cloudregion()


class CloudAccountRelatedMixin(object):
    permission_classes = (permissions.CloudAccountParentObjectPermissions,)

    def get_cloudaccount(self):
        queryset = models.CloudAccount.objects.all()

        obj = get_object_or_404(queryset, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_cloudaccount()


class CloudImageRelatedMixin(object):

    def get_cloudimage(self):
        queryset = models.CloudImage.objects.all()

        obj = get_object_or_404(queryset, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_cloudimage()


class SnapshotRelatedMixin(object):

    def get_snapshot(self):
        queryset = models.Snapshot.objects.all()

        obj = get_object_or_404(queryset, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_snapshot()


class SecurityGroupRelatedMixin(object):

    def get_securitygroup(self):
        queryset = models.SecurityGroup.objects.all()

        obj = get_object_or_404(queryset, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissioned_object(self):
        return self.get_securitygroup()
