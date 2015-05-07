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

from rest_framework import status
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class ResourceConflict(APIException):
    def __init__(self, detail):
        self.status_code = status.HTTP_409_CONFLICT
        self.detail = detail
        logger.debug('ResourceConflict: %s' % self.detail)
        super(ResourceConflict, self).__init__(self.detail)

    def __str__(self):
        return 'Resource Conflict: {0}'.format(self.detail)


class BadRequest(APIException):
    def __init__(self, detail):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = detail
        logger.debug('BadRequest: %s' % self.detail)
        super(BadRequest, self).__init__(self.detail)

    def __str__(self):
        return 'Bad Request: {0}'.format(self.detail)


class NotImplemented(APIException):
    def __init__(self, detail):
        self.status_code = status.HTTP_501_NOT_IMPLEMENTED
        self.detail = detail
        logger.debug('NotImplemented: %s' % self.detail)
        super(NotImplemented, self).__init__(self.detail)

    def __str__(self):
        return 'Not Implemented: {0}'.format(self.detail)


class InternalServerError(APIException):
    def __init__(self, detail):
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.detail = detail
        logger.debug('InternalServerError: %s' % self.detail)
        super(InternalServerError, self).__init__(self.detail)

    def __str__(self):
        return 'Internal Server Error: {0}'.format(self.detail)
