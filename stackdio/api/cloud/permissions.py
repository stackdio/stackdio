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

from stackdio.core.permissions import (
    StackdioModelPermissions,
    StackdioParentObjectPermissions,
    StackdioPermissionsModelPermissions,
    StackdioPermissionsObjectPermissions,
)
from . import models


class CloudProviderParentObjectPermissions(StackdioParentObjectPermissions):
    parent_model_cls = models.CloudProvider


class CloudProviderPermissionsObjectPermissions(StackdioPermissionsObjectPermissions):
    parent_model_cls = models.CloudProvider


class CloudAccountParentObjectPermissions(StackdioParentObjectPermissions):
    parent_model_cls = models.CloudAccount


class CloudAccountPermissionsModelPermissions(StackdioPermissionsModelPermissions):
    model_cls = models.CloudAccount


class CloudAccountPermissionsObjectPermissions(StackdioPermissionsObjectPermissions):
    parent_model_cls = models.CloudAccount


class CloudImagePermissionsModelPermissions(StackdioPermissionsModelPermissions):
    model_cls = models.CloudImage


class CloudImagePermissionsObjectPermissions(StackdioPermissionsObjectPermissions):
    parent_model_cls = models.CloudImage


class SnapshotPermissionsModelPermissions(StackdioPermissionsModelPermissions):
    model_cls = models.Snapshot


class SnapshotPermissionsObjectPermissions(StackdioPermissionsObjectPermissions):
    parent_model_cls = models.Snapshot


class SecurityGroupPermissionsModelPermissions(StackdioPermissionsModelPermissions):
    model_cls = models.SecurityGroup


class SecurityGroupPermissionsObjectPermissions(StackdioPermissionsObjectPermissions):
    parent_model_cls = models.SecurityGroup


class StackdioReadOnlyModelPermissions(StackdioModelPermissions):

    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        # These shouldn't be used, but we'll put them here anyways
        'POST': ['%(app_label)s.create_%(model_name)s'],
        'PUT': ['%(app_label)s.update_%(model_name)s'],
        'PATCH': ['%(app_label)s.update_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
