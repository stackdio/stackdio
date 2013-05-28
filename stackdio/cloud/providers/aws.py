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


    @staticmethod
    def create_provider_yaml(data):
        '''
        Takes a JSON dictionary and returns the yaml string for this 
        provider. The following are required keys in the dictionary:

        `aws_id`

        Requires the foll
        '''
        yaml_data = {
            'provider': SHORT_NAME,
            'id': data[AWS_ID],
            'key': data[AWS_SECRET_KEY], 
            'keyname': data[AWS_KEYPAIR],
            'securitygroup': data[AWS_SECURITY_GROUPS],
            'private_key': data[AWS_PRIVATE_KEY],
        }
