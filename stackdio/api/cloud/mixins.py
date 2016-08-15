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

from stackdio.core.mixins import ParentRelatedMixin
from stackdio.core.permissions import StackdioPermissionsPermissions
from . import models

logger = logging.getLogger(__name__)


class CloudProviderRelatedMixin(ParentRelatedMixin):
    parent_queryset = models.CloudProvider.objects.all()
    parent_lookup_field = 'name'

    def get_cloudprovider(self):
        return self.get_parent_object()


class CloudProviderPermissionsMixin(CloudProviderRelatedMixin):
    permission_classes = (StackdioPermissionsPermissions,)

    def get_permissioned_object(self):
        return self.get_parent_object()


class CloudAccountRelatedMixin(ParentRelatedMixin):
    parent_queryset = models.CloudAccount.objects.all()

    def get_cloudaccount(self):
        return self.get_parent_object()


class CloudAccountPermissionsMixin(CloudAccountRelatedMixin):
    permission_classes = (StackdioPermissionsPermissions,)

    def get_permissioned_object(self):
        return self.get_parent_object()


class CloudImageRelatedMixin(ParentRelatedMixin):
    parent_queryset = models.CloudImage.objects.all()

    def get_cloudimage(self):
        return self.get_parent_object()


class CloudImagePermissionsMixin(CloudImageRelatedMixin):
    permission_classes = (StackdioPermissionsPermissions,)

    def get_permissioned_object(self):
        return self.get_parent_object()


class SnapshotRelatedMixin(ParentRelatedMixin):
    parent_queryset = models.Snapshot.objects.all()

    def get_snapshot(self):
        return self.get_parent_object()


class SnapshotPermissionsMixin(SnapshotRelatedMixin):
    permission_classes = (StackdioPermissionsPermissions,)

    def get_permissioned_object(self):
        return self.get_parent_object()


class SecurityGroupRelatedMixin(ParentRelatedMixin):
    parent_queryset = models.SecurityGroup.objects.all()

    def get_securitygroup(self):
        return self.get_parent_object()


class SecurityGroupPermissionsMixin(SecurityGroupRelatedMixin):
    permission_classes = (StackdioPermissionsPermissions,)

    def get_permissioned_object(self):
        return self.get_parent_object()
