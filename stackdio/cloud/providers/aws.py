"""
Amazon Web Services provider for stackd.io
"""

import os
import stat
import logging
from uuid import uuid4
from time import sleep

import boto
import yaml
from boto.route53.record import ResourceRecordSets

from django.core.exceptions import ValidationError

from cloud.providers.base import (
    BaseCloudProvider,
    TimeoutException,
    MaxFailuresException,
)

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
        logger.debug(response)
        self.hosted_zone = response['GetHostedZoneResponse']['HostedZone']

        # Get the zone id, but strip off the first part /hostedzone/
        self.zone_id = self.hosted_zone['Id'][len('/hostedzone/'):]

    def get_rrnames_set(self):
        '''
        Returns a set of resource record names for our zone id
        '''
        rr_sets = self.conn.get_all_rrsets(self.zone_id)
        return set([rr.name for rr in rr_sets])

    def start_rr_transaction(self):
        '''
        Creates a new Route53 ResourceRecordSets object that is used
        internally like a transaction of sorts. You may add or delete 
        many resource records using a single set by calling the
        `add_rr_cname` and `delete_rr_cname` methods. Finish the transaction
        with `finish_rr_transaction`

        NOTE: Calling this method again before finishing will not finish
        an existing transaction or delete it. To cancel an existing
        transaction use the `cancel_rr_transaction`.
        '''

        if not hasattr(self, '_rr_txn') or self._rr_txn is None:
            # Return a new ResourceRecordSets "transaction"
            self._rr_txn = ResourceRecordSets(self.conn, self.zone_id)

    def finish_rr_transaction(self):
        '''
        If a transaction exists, commit the changes to Route53
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
        NOTE: This method must be called after `start_rr_transaction`.

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
            return True
        return False

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

    # Actions that may be executed. Implement these 
    # actions below
    ACTION_STOP = 'stop'
    ACTION_START = 'start'
    ACTION_TERMINATE = 'terminate'
    ACTION_LAUNCH = 'launch'
    ACTION_PROVISION = 'provision'

    STATE_STOPPED = 'stopped'
    STATE_RUNNING = 'running'
    STATE_TERMINATED = 'terminated'

    @classmethod
    def get_required_fields(self):
        return [
            self.ACCESS_KEY, 
            self.SECRET_KEY, 
            self.KEYPAIR,
            self.SECURITY_GROUPS
        ]

    @classmethod
    def get_available_actions(self):
        return [
            self.ACTION_STOP,
            self.ACTION_START,
            self.ACTION_TERMINATE,
            self.ACTION_LAUNCH,
            self.ACTION_PROVISION,
        ]

    def get_private_key_path(self):
        return os.path.join(self.provider_storage, 'id_rsa')

    def get_config_file_path(self):
        return os.path.join(self.provider_storage, 'config')

    def get_config(self):
        with open(self.get_config_file_path(), 'r') as f:
            config_data = yaml.safe_load(f)
        return config_data

    def get_credentials(self):
        config_data = self.get_config()
        return (config_data['id'], config_data['key'])

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
        if not hasattr(self, '_ec2_connection'):
            credentials = self.get_credentials()
            self._ec2_connection = boto.connect_ec2(*credentials)
        return self._ec2_connection

    def register_dns(self, hosts):
        '''
        Given a list of 'stacks.Host' objects, this method's
        implementation should handle the registration of DNS
        for the given cloud provider (e.g., Route53 on AWS)
        '''

        logger.debug('register_dns for hosts {0!r}'.format(hosts))

        # Start a resource record "transaction"
        r53_domain = self.connect_route53()
        r53_domain.start_rr_transaction()

        # for each host, create a CNAME record
        for host in hosts:
            logger.debug('add_rr_cname for host {0!r} -> {1} : {2}'.format(host, host.hostname, host.provider_dns))
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
        r53_domain.start_rr_transaction()

        # for each host, delete the CNAME record
        finish = False
        for host in hosts:
            if not host.provider_dns:
                continue
            logger.debug(host.hostname)
            logger.debug(host.provider_dns)
            if r53_domain.delete_rr_cname(host.hostname, 
                                          host.provider_dns,
                                          ttl=DEFAULT_ROUTE53_TTL):
                finish = True

        if finish:
            # Finish the transaction
            logger.debug(r53_domain)
            logger.debug(dir(r53_domain))
            r53_domain.finish_rr_transaction()

        # update hosts to remove fqdn
        hosts.update(fqdn='')

    def register_volumes_for_delete(self, hosts):
        ec2 = self.connect_ec2()

        # for each host, modify the instance attribute to enable automatic
        # volume deletion automatically when the host is terminated
        for h in hosts:
            if not h.instance_id:
                continue

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
                ec2.modify_instance_attribute(h.instance_id, 
                                              'blockDeviceMapping', 
                                              mods)

            # for each volume, rename them so we can create new volumes with
            # the same now, just in case
            for v in h.volumes.all():
                if not v.volume_id:
                    logger.warn('{0!r} missing volume_id. Skipping delete retag.'.format(v))
                    continue
                name = 'stackdio::volume::{0!s}-DEL-{1}'.format(v.id, uuid4().hex)
                logger.info('tagging volume {}: {}'.format(v.volume_id, name))
                ec2.create_tags([v.volume_id], {
                    'Name': name,
                })


    def tag_resources(self, stack, hosts=[], volumes=[]):
        ec2 = self.connect_ec2()

        # Tag each volume with a unique name. This makes it easier to view
        # the volumes in the AWS console
        for v in volumes:
            name = 'stackdio::volume::{0!s}'.format(v.id)
            logger.info('tagging volume {}: {}'.format(v.volume_id, name))
            ec2.create_tags([v.volume_id], {
                'Name': name,
            })

        # Next tag all resources with a set of common fields
        resource_ids = [v.volume_id for v in volumes] + \
                       [h.instance_id for h in hosts]

        # filter out empty strings
        resource_ids = filter(None, resource_ids)

        if resource_ids:
            logger.info('tagging {0!r}'.format(resource_ids))
            ec2.create_tags(resource_ids, {
                'stack_id': str(stack.id),
                'owner': stack.user.username,
            })

    def get_ec2_instances(self, hosts):
        ec2 = self.connect_ec2()

        instance_ids = [i.instance_id for i in hosts]
        return [i for r in ec2.get_all_instances(instance_ids) \
                     for i in r.instances]

    def _wait(self,
              fun,
              fun_args=None,
              fun_kwargs=None,
              timeout=5*60,
              interval=5,
              max_failures=5):
        '''
        Generic function that will call the given function `fun` with 
        `fun_args` and `fun_kwargs` until the function returns a valid result 
        or the `timeout` or `max_failures` is reached. A valid result is a 
        tuple with the first element being boolean True and the second element
        being the return value for `fun`. If False is the first element of the
        tuple it will *not* be considered a failure and the loop will continue
        waiting for a valid result. All exceptions from `fun` will be 
        considered failures.
        '''

        if fun_args is None:
            fun_args = ()
        if fun_kwargs is None:
            fun_kwargs = {}

        # start the loop
        while True:
            logger.debug(
                'Calling given method {0!r}. Giving up in 00:{1:02d}:{2:02d}'.format(
                    fun,
                    int(timeout // 60),
                    int(timeout % 60)
                )
            )
            try:
                ok, result = fun(*fun_args, **fun_kwargs)
                if ok:
                    return result
            except Exception, e:
                logger.exception('Function {0!r} threw exception. Remaining '
                                 'failures: {1}'.format(fun, max_failures))

                max_failures -= 1
                if max_failures <= 0:
                    raise MaxFailuresException(
                        'Too many failures occurred while waiting for '
                        'valid return value. Giving up.'
                    )

            if timeout < 0:
                raise TimeoutException(
                    'Unable to reach {0} state in {1}s'.format(
                        state,
                        timeout
                    )
                )
            sleep(interval)
            timeout -= interval

    def _wait_for_state(self, hosts, state):
        '''
        Checks if all hosts are in the given state. Returns a 2-element tuple
        with the first element a boolean representing if all hosts are in the
        required state and the second element being the list of EC2 instance
        objects. This method is suitable as a handler for the `_wait` method.
        '''
        instances = self.get_ec2_instances(hosts)
        if not instances:
            raise RuntimeError('get_ec2_instances returned zero results!')

        # get the state for all instances
        states = set(i.update() for i in instances)

        # Multiple states found, requirement failed
        if len(states) > 1:
            return False, instances

        # One state found, return true if the state requirement has been met
        return states.pop() == state, instances

    ##
    # ACTION IMPLEMENTATIONS BELOW
    ##

    def _execute_action(self, stack, status, success_state, state_fun, *args, **kwargs):
        '''
        Generic function to handle most all states accordingly. If you need
        custom logic in the state handling, do so in the _action* methods.
        '''
        stack.set_status(status, 
                         '%s all hosts in this stack.' % status.capitalize())

        hosts = stack.get_hosts()
        instance_ids = [h.instance_id for h in hosts]

        state_fun(instance_ids, *args, **kwargs)

        # Wait for success_state
        try:
            instances = self._wait(
                self._wait_for_state,
                fun_args=(hosts, success_state)
            )
            return True
        except MaxFailuresException, e:
            logger.error('Max number of failures reached while waiting '
                         'for state: %s' % success_state)
        except TimeoutException, e:
            logger.error('Timeout reached while waiting for state: '
                         '%s.' % success_state)

        return False

    def _action_stop(self, stack, *args, **kwargs):
        '''
        Stop all of the hosts on the given stack.
        '''
        ec2 = self.connect_ec2() 
        return self._execute_action(stack, 
                                    stack.STOPPING,
                                    self.STATE_STOPPED,
                                    ec2.stop_instances,
                                    *args,
                                    **kwargs)

    def _action_start(self, stack, *args, **kwargs):
        '''
        Starts all of the hosts on the given stack.
        '''
        ec2 = self.connect_ec2() 
        return self._execute_action(stack, 
                                    stack.STARTING,
                                    self.STATE_RUNNING,
                                    ec2.start_instances,
                                    *args,
                                    **kwargs)

    def _action_terminate(self, stack, *args, **kwargs):
        '''
        Terminates all of the hosts on the given stack.
        '''
        ec2 = self.connect_ec2() 
        return self._execute_action(stack, 
                                    stack.TERMINATING,
                                    self.STATE_TERMINATED,
                                    ec2.terminate_instances,
                                    *args,
                                    **kwargs)
    ##
    # END ACTION IMPLEMENTATIONS
    ##
