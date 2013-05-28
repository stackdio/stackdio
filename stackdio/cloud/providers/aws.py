"""
Amazon Web Services provider for stackd.io
"""

import logging

from cloud.providers.base import BaseCloudProvider

logger = logging.getLogger(__name__)


##
# Required parameters that must be defined
##

class AWSCloudProvider(BaseCloudProvider):
    # Short and long names are used as choices in the cloud provider
    # model
    SHORT_NAME = 'aws'
    LONG_NAME  = 'Amazon Web Services' 
    CHOICE = (SHORT_NAME, LONG_NAME)

    # The AWS access key id
    AWS_ID = 'aws_id'

    # The AWS secret access key
    AWS_SECRET_KEY = 'aws_secret_key'

    # The AWS keypair name
    AWS_KEYPAIR = 'aws_keypair'

    # The AWS security groups
    AWS_SECURITY_GROUPS = 'aws_security_groups'

    # The path to the private key for SSH
    AWS_PRIVATE_KEY = 'private_key_path'


    @classmethod
    def get_provider_data(self, data):
        '''
        Takes a dict of the request data and returns a new dict of info
        relevant to this provider type. See salt cloud documentation for
        more info on what needs to be in this dict for the provider type
        you're implementing.
        '''
        security_groups = filter(None, data[self.AWS_SECURITY_GROUPS].split(','))
        yaml_data = {
            'provider': self.SHORT_NAME,
            'id': data[self.AWS_ID],
            'key': data[self.AWS_SECRET_KEY], 
            'keyname': data[self.AWS_KEYPAIR],
            'securitygroup': security_groups,
            'private_key': data[self.AWS_PRIVATE_KEY],
        }

        return yaml_data
