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
    StackdioParentObjectPermissions,
    StackdioPermissionsModelPermissions,
    StackdioPermissionsObjectPermissions,
)
from . import models


class StackParentObjectPermissions(StackdioParentObjectPermissions):
    parent_model_cls = models.Stack


class StackPermissionsModelPermissions(StackdioPermissionsModelPermissions):
    model_cls = models.Stack


class StackPermissionsObjectPermissions(StackdioPermissionsObjectPermissions):
    parent_model_cls = models.Stack


class StackActionObjectPermissions(StackParentObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.view_%(model_name)s'],
        'PUT': ['%(app_label)s.view_%(model_name)s'],
        'PATCH': ['%(app_label)s.view_%(model_name)s'],
        'DELETE': ['%(app_label)s.view_%(model_name)s'],
    }
