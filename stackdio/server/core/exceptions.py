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


class BadRequest(APIException):
    def __init__(self, detail):
        self.status_code = status.HTTP_400_BAD_REQUEST
        self.detail = detail
        logger.debug('BadRequest: %s' % self.detail)
        super(BadRequest, self).__init__(self.detail)


class NotImplemented(APIException):
    def __init__(self, detail):
        self.status_code = status.HTTP_501_NOT_IMPLEMENTED
        self.detail = detail
        logger.debug('NotImplemented: %s' % self.detail)
        super(BadRequest, self).__init__(self.detail)


class InternalServerError(APIException):
    def __init__(self, detail):
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.detail = detail
        logger.debug('InternalServerError: %s' % self.detail)
        super(InternalServerError, self).__init__(self.detail)
