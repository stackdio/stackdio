import logging

logger = logging.getLogger(__name__)

class BaseCloudProvider(object):

    @classmethod
    def get_provider_data(self, data):
        raise NotImplementedError()
