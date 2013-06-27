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

DEFAULT_ROUTE53_TTL = 30


class Route53Domain(object):
    def __init__(self, access_key, secret_key, domain):
        '''
        `access_key`
            The AWS access key id
        `secret_key`
            The AWS secret access key
        `domain`
            An existing Route53 domain to manage
        '''
        self.access_key = access_key
        self.secret_key = secret_key
        self.domain = domain

        # Loaded after connection is made
        self.hosted_zone = None
        self.zone_id = None
        
        self.conn = boto.connect_route53(self.access_key,
                                         self.secret_key)

        self._load_domain()

    def _load_domain(self):
        '''
        Attempts to look up a Route53 hosted zone given a domain name (they're
        much easier to remember than a zone id). Once loaded, pulls out the
        zone id and stores it in `zone_id`
        '''
        # look up the hosted zone based on the domain
        response = self.conn.get_hosted_zone_by_name(self.domain)
        self.hosted_zone = response['GetHostedZoneResponse']['HostedZone']

        # Get the zone id, but strip off the first part /hostedzone/
        self.zone_id = self.hosted_zone['Id'][len('/hostedzone/'):]

    def get_rrnames_set(self):
        '''
        Returns a set of resource record names for our zone id
        '''
        rr_sets = self.conn.get_all_rrsets(self.zone_id)
        return set([rr.name for rr in rr_sets])

    def start_rr_transcation(self):
        '''
        Creates a new Route53 ResourceRecordSets object that is used
        internally like a transaction of sorts. You may add or delete 
        many resource records using a single set by calling the
        `add_rr_cname` and `delete_rr_cname` methods. Finish the transcation
        with `finish_rr_transcation`

        NOTE: Calling this method again before finishing will not finish
        an existing transcation or delete it. To cancel an existing
        transaction use the `cancel_rr_transaction`.
        '''

        if not hasattr(self, '_rr_txn') or self._rr_txn is None:
            # Return a new ResourceRecordSets "transaction"
            self._rr_txn = ResourceRecordSets(self.conn, self.zone_id)

    def finish_rr_transaction(self):
        '''
        If a transcation exists, commit the changes to Route53
        '''
        if self._rr_txn is not None:
            self._rr_txn.commit()
            self._rr_txn = None

    def cancel_rr_transaction(self):
        '''
        Basically deletes the existing transaction.
        '''
        self._rr_txn = None

    def add_rr_cname(self, record_name, record_value, ttl=86400):
        '''
        NOTE: This method must be called after `start_rr_transcation`.

        Adds a new record to the existing resource record transaction.

        `record_name`
            The subdomain part of the CNAME record (e.g., web-1 for a domain
            like web-1.dev.example.com)

        `record_value`
            The host or IP the CNAME record will point to.

        `ttl`
            The TTL for the record in seconds, default is 24 hours
        '''
        # Update the record name to be fully qualified with the domain
        # for this instance. The period on the end is required.
        record_name += '.{}.'.format(self.domain)

        # Check for an existing CNAME record and remove it before
        # updating it
        rr_names = self.get_rrnames_set()
        if record_name in rr_names:
            self._delete_rr_record(record_name, [record_value], 'CNAME', ttl=ttl)

        self._add_rr_record(record_name, [record_value], 'CNAME', ttl=ttl)

    def delete_rr_cname(self, record_name, record_value, ttl=86400):
        '''
        Almost the same as `add_rr_cname` but it deletes the CNAME record

        NOTE: The name, value, and ttl must all match an existing CNAME record
        or Route53 will not allow it to be removed.
        '''
        # Update the record name to be fully qualified with the domain
        # for this instance. The period on the end is required.
        record_name += '.{}.'.format(self.domain)

        # Only remove the record if it exists
        rr_names = self.get_rrnames_set()
        if record_name in rr_names:
            self._delete_rr_record(record_name, [record_value], 'CNAME', ttl=ttl)

    def _add_rr_record(self, record_name, record_values, record_type, **kwargs):
        rr = self._rr_txn.add_change('CREATE', record_name, record_type, **kwargs)
        for v in record_values:
            rr.add_value(v)

    def _delete_rr_record(self, record_name, record_values, record_type, **kwargs):
        rr = self._rr_txn.add_change('DELETE', record_name, record_type, **kwargs)
        for v in record_values:
            rr.add_value(v)

class AWSCloudProvider(BaseCloudProvider):
    SHORT_NAME = 'ec2'
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

    def get_config(self):
        with open(self.get_config_file_path(), 'r') as f:
            config_data = yaml.safe_load(f)
        return config_data

    def get_credentials(self):
        config_data = self.get_config()
        return (config_data['id'], config_data['key'])

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
            'securitygroup': security_groups,
            'private_key': private_key_path,
            'append_domain': data[self.ROUTE53_DOMAIN],

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

    def connect_route53(self):

        # Load the configuration file to get a few things we'll need
        # to manage DNS
        config_data = self.get_config()

        access_key = config_data['id']
        secret_key = config_data['key']
        domain = config_data['append_domain']

        # load a new Route53Domain class and return it
        return Route53Domain(access_key, secret_key, domain)

    def connect_ec2(self):
        credentials = self.get_credentials()
        return boto.connect_ec2(*credentials)

    def register_dns(self, hosts):
        '''
        Given a list of 'stacks.Host' objects, this method's
        implementation should handle the registration of DNS
        for the given cloud provider (e.g., Route53 on AWS)
        '''

        # Start a resource record "transaction"
        r53_domain = self.connect_route53()
        r53_domain.start_rr_transcation()

        # for each host, create a CNAME record
        for host in hosts:
            r53_domain.add_rr_cname(host.hostname,
                                    host.provider_dns, 
                                    ttl=DEFAULT_ROUTE53_TTL)

        # Finish the transaction
        r53_domain.finish_rr_transaction()

        # update hosts to include fqdn
        for host in hosts:
            host.fqdn = '{}.{}'.format(host.hostname, r53_domain.domain)
            host.save()
        
    def unregister_dns(self, hosts):
        '''
        Given a list of 'stacks.Host' objects, this method's
        implementation should handle the de-registration of DNS
        for the given cloud provider (e.g., Route53 on AWS)
        '''

        # Start a resource record "transaction"
        r53_domain = self.connect_route53()
        r53_domain.start_rr_transcation()

        # for each host, delete the CNAME record
        for host in hosts:
            r53_domain.delete_rr_cname(host.hostname, 
                                       host.provider_dns,
                                       ttl=DEFAULT_ROUTE53_TTL)

        # Finish the transaction
        r53_domain.finish_rr_transaction()

        # update hosts to remove fqdn
        for host in hosts:
            host.fqdn = ''
            host.save()

    def register_volumes_for_delete(self, hosts):
        ec2 = self.connect_ec2()

        # for each host, modify the instance attribute to enable automatic
        # volume deletion automatically when the host is terminated
        for h in hosts:
            # get current block device mappings
            _, devices = ec2.get_instance_attribute(h.instance_id,
                                                    'blockDeviceMapping').popitem()

            # find those devices that aren't already registered for deletion
            # and build a list of the modify strings
            mods = []
            for device_name, device in devices.iteritems():
                if not device.delete_on_termination:
                    mods.append('{}=true'.format(device_name))

            # use the modify strings to change the existing volumes flag
            if mods:
                ec2.modify_instance_attribute(h.instance_id, 'blockDeviceMapping', mods)

