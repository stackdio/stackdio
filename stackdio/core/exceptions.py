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

from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class ResourceConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Resource Conflict')

    def __str__(self):
        return 'Resource Conflict: {0}'.format(self.detail)


class BadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Bad Request')

    def __str__(self):
        return 'Bad Request: {0}'.format(self.detail)


class NotImplemented(APIException):
    status_code = status.HTTP_501_NOT_IMPLEMENTED
    default_detail = _('Not Implemented')

    def __str__(self):
        return 'Not Implemented: {0}'.format(self.detail)


class InternalServerError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _('Server Error')

    def __str__(self):
        return 'Internal Server Error: {0}'.format(self.detail)
