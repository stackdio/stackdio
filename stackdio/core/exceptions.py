from rest_framework import status
from rest_framework.exceptions import APIException

import logging

logger = logging.getLogger(__name__)

class ResourceConflict(APIException):
    def __init__(self, detail):
        self.status_code = status.HTTP_409_CONFLICT
        self.detail = detail
        logger.debug('ResourceConflict: %s' % self.detail)
        super(ResourceConflict, self).__init__(self.detail)
