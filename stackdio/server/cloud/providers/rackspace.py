"""
Rackspace provider for stackd.io
"""

import logging

from cloud.providers.base import BaseCloudProvider

logger = logging.getLogger(__name__)


##
# Required parameters that must be defined
##

class RackspaceCloudProvider(BaseCloudProvider):
    # Notice we're using openstack as the shortname here, as this is
    # the appropriate provider type for dealing with Rackspace
    SHORT_NAME = 'openstack'
    LONG_NAME  = 'Rackspace' 

    # Identity URL
    IDENTITY_URL = 'identity_url'

    # Compute name
    COMPUTE_NAME = 'compute_name'

    # Compute region
    COMPUTE_REGION = 'compute_region'

    # Protocol
    PROTOCOL = 'protocol'

    # Authentication
    USERNAME = 'username'
    TENANT_ID = 'tenant_id'
    API_KEY = 'api_key'

    @classmethod
    def get_provider_data(self, data):
        yaml_data = {
            'provider': self.SHORT_NAME,
            'identity_url': data[self.IDENTITY_URL],
            'compute_name': data[self.COMPUTE_NAME], 
            'compute_region': data[self.COMPUTE_REGION],
            'protocol': data[self.PROTOCOL],
            'user': data[self.USERNAME],
            'tenant': data[self.TENANT_ID],
            'apikey': data[self.API_KEY],
        }

        return yaml_data

    @classmethod
    def get_required_fields(self):
        return [
            self.IDENTITY_URL, 
            self.COMPUTE_NAME, 
            self.COMPUTE_REGION,
            self.PROTOCOL,
            self.USERNAME,
            self.TENANT_ID,
            self.API_KEY,
        ]
