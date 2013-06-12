"""
Amazon Web Services provider for stackd.io
"""

import os
import stat
import logging
import yaml

import boto
from boto.route53.record import ResourceRecordSets
from django.core.exceptions import ValidationError

from cloud.providers.base import BaseCloudProvider

logger = logging.getLogger(__name__)


##
# Required parameters that must be defined
##

class AWSCloudProvider(BaseCloudProvider):
    SHORT_NAME = 'aws'
    LONG_NAME  = 'Amazon Web Services' 

    # The AWS access key id
    ACCESS_KEY = 'access_key_id'

    # The AWS secret access key
    SECRET_KEY = 'secret_access_key'

    # The AWS keypair name
    KEYPAIR = 'keypair'

    # The AWS security groups
    SECURITY_GROUPS = 'security_groups'

    # The path to the private key for SSH
    PRIVATE_KEY_FILE = 'private_key_file'

    # The route53 zone to use for managing DNS
    ROUTE53_DOMAIN = 'route53_domain'

    @classmethod
    def get_required_fields(self):
        return [
            self.ACCESS_KEY, 
            self.SECRET_KEY, 
            self.KEYPAIR,
            self.SECURITY_GROUPS
        ]

    def get_private_key_path(self):
        return os.path.join(self.provider_storage, 'id_rsa')

    def get_config_file_path(self):
        return os.path.join(self.provider_storage, 'config')

    def get_provider_data(self, data, files):
        # write the private key to the proper location
        private_key_path = self.get_private_key_path()
        with open(private_key_path, 'w') as f:
            f.write(files[self.PRIVATE_KEY_FILE].read())

        # change the file permissions of the RSA key
        os.chmod(private_key_path, stat.S_IRUSR)

        security_groups = filter(None, data[self.SECURITY_GROUPS].split(','))
        config_data = {
            'provider': self.SHORT_NAME,
            'id': data[self.ACCESS_KEY],
            'key': data[self.SECRET_KEY], 
            'keyname': data[self.KEYPAIR],
            'route53_domain': data[self.ROUTE53_DOMAIN],
            'securitygroup': security_groups,
            'private_key': private_key_path,

            'ssh_interface': 'public_ips',
            'rename_on_destroy': True,
            'delvol_on_destroy': True,
        }

        # Save the data out to a file that can be reused by this provider
        # later if necessary
        with open(self.get_config_file_path(), 'w') as f:
            f.write(yaml.safe_dump(config_data, default_flow_style=False))

        return config_data

    def validate_provider_data(self, data, files):

        result, errors = super(AWSCloudProvider, self) \
            .validate_provider_data(data, files)

        # check security groups
        if result:
            ec2 = boto.connect_ec2(data[self.ACCESS_KEY], data[self.SECRET_KEY])

            try:
                security_groups = filter(None, data[self.SECURITY_GROUPS].split(','))
                security_groups = ec2.get_all_security_groups(security_groups)
            except boto.exception.EC2ResponseError, e:
                result = False
                errors['AWS'].append(e.error_message)

        # check for required files
        if not files or self.PRIVATE_KEY_FILE not in files:
            result = False
            errors[self.PRIVATE_KEY_FILE].append(self.REQUIRED_MESSAGE)
        
        return result, errors

    def register_dns(self, hosts):
        '''
        Given a list of 'stacks.Host' objects, this method's
        implementation should handle the registration of DNS
        for the given cloud provider (e.g., Route53 on AWS)
        '''

        # Load the configuration file to get a few things we'll need
        # to manage DNS
        with open(self.get_config_file_path(), 'r') as f:
            config_data = yaml.safe_load(f)

        access_key = config_data['id']
        secret_key = config_data['key']
        domain = config_data['route53_domain']

        # make sure the domain ends in a period
        #if not domain.endswith('.'):
        #    domain += '.'

        logger.debug('%s', access_key)
        logger.debug('%s', secret_key)
        logger.debug('%s', domain)

        # connect to Route53
        conn = boto.connect_route53(access_key, secret_key)

        # look up the zone id based on the domain
        hosted_zone = conn.get_hosted_zone_by_name(domain)['GetHostedZoneResponse']['HostedZone']
        logger.debug('HOSTED ZONE: %r', hosted_zone)

        # Get the zone id, but strip off the first part /hostedzone/
        zone_id = hosted_zone['Id'][len('/hostedzone/'):]
        logger.debug('ZONE ID: %s', zone_id)

        # All the current resource records for the zone
        rr_sets = conn.get_all_rrsets(zone_id)
        rr_names = set([rr.name for rr in rr_sets])

        # Start a resource record "transaction"
        rr_changes = ResourceRecordSets(conn, zone_id)

        # for each host, add an entry to the resource record set
        for host in hosts:
            # TODO: What do we do if the CNAME does exist? We can't assume it's not
            # valid, right or do we depend on the hostname being unique in the DB
            # before we ever get here???
            name = host.hostname + '.' + domain
            logger.debug('Setting CNAME for {}'.format(name))

            # If the CNAME record already exists, delete it
            if name in rr_names:
                logger.debug('CNAME alread exists for {}. Deleting.'.format(name))
                rr = rr_changes.add_change('DELETE', name, 'CNAME')
                rr.add_value(host.public_dns)
            
            # Add the CNAME record and point it at the public DNS of the instance
            rr = rr_changes.add_change('CREATE', name, 'CNAME', ttl=30)
            rr.add_value(host.public_dns)

        # Commit the resource set changes
        logger.debug(repr(rr_changes))
        rr_changes.commit()
