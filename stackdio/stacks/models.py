import json
import os
import re
import logging
import socket


import envoy
import yaml
from core.exceptions import BadRequest
from django.conf import settings
from django.db import models, transaction
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django_extensions.db.models import (
    TimeStampedModel,
    TitleSlugDescriptionModel,
)
import model_utils.models
from model_utils import Choices

from core.fields import DeletingFileField
from core.utils import recursive_update
from cloud.models import SecurityGroup


PROTOCOL_CHOICES = [
    ('tcp', 'TCP'),
    ('udp', 'UDP'),
    ('icmp', 'ICMP'),
]

logger = logging.getLogger(__name__)

HOST_INDEX_PATTERN = re.compile('.*-.*-(\d+)')


def get_hostnames_from_hostdefs(hostdefs, username='', namespace=''):
    hostnames = []
    for hostdef in hostdefs:
        for i in xrange(hostdef.count):
            hostnames.append(
                hostdef.hostname_template.format(
                    namespace=namespace,
                    username=username,
                    index=i
                )
            )
    return hostnames


# Map, pillar, and properties files go into storage
def get_map_file_path(obj, filename):
    return "stacks/{0}/{1}/stack.map".format(obj.owner.username, obj.slug)


def get_pillar_file_path(obj, filename):
    return "stacks/{0}/{1}/stack.pillar".format(obj.owner.username, obj.slug)


def get_props_file_path(obj, filename):
    return "stacks/{0}/{1}/stack.props".format(obj.owner.username, obj.slug)


# Top and overstate files go into salt root
def get_top_file_path(obj, filename):
    return "stack_{0}_top.sls".format(obj.id)


def get_overstate_file_path(obj, filename):
    return "stack_{0}_overstate.sls".format(obj.id)


def get_global_overstate_file_path(obj, filename):
    return "stack_{0}_global_overstate.sls".format(obj.id)


class StackCreationException(Exception):
    def __init__(self, errors, *args, **kwargs):
        self.errors = errors
        super(StackCreationException, self).__init__(*args, **kwargs)


class Level(object):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARN = 'WARNING'
    ERROR = 'ERROR'


class StatusDetailModel(model_utils.models.StatusModel):
    status_detail = models.TextField(blank=True)

    class Meta:
        abstract = True

    def set_status(self, status, detail=''):
        self.status = status
        self.status_detail = detail
        return self.save()


class StackManager(models.Manager):

    @transaction.commit_on_success
    def create_stack(self, owner, blueprint, **data):
        """
        """
        title = data.get('title', '')
        description = data.get('description', '')
        public = data.get('public', False)

        if not title:
            raise ValueError("Stack 'title' is a required field.")

        stack = self.model(owner=owner,
                           blueprint=blueprint,
                           title=title,
                           description=description,
                           public=public)
        stack.save()

        # add the namespace
        namespace = data.get('namespace', '').strip()
        if not namespace:
            namespace = 'stack{0}'.format(stack.pk)
        stack.namespace = namespace
        stack.save()

        # manage the properties
        properties = blueprint.properties
        recursive_update(properties, data.get('properties', {}))
        props_json = json.dumps(properties, indent=4)
        if not stack.props_file:
            stack.props_file.save(stack.slug + '.props',
                                  ContentFile(props_json))
        else:
            with open(stack.props_file.path, 'w') as f:
                f.write(props_json)

        stack.create_security_groups()
        stack.create_hosts()

        # Generate configuration files for salt and salt-cloud
        # NOTE: The order is important here. pillar must be available before
        # the map file is rendered or else we'll miss important grains that
        # need to be set at launch time
        stack._generate_pillar_file()
        stack._generate_top_file()
        stack._generate_overstate_file()
        stack._generate_global_overstate_file()
        stack._generate_map_file()

        return stack


class Stack(TimeStampedModel, TitleSlugDescriptionModel,
            model_utils.models.StatusModel):

    # Launch workflow:
    PENDING = 'pending'
    LAUNCHING = 'launching'
    CONFIGURING = 'configuring'
    SYNCING = 'syncing'
    PROVISIONING = 'provisioning'
    ORCHESTRATING = 'orchestrating'
    FINALIZING = 'finalizing'
    FINISHED = 'finished'

    # Delete workflow:
    # PENDING
    DESTROYING = 'destroying'
    # FINISHED

    # Other actions
    # LAUNCHING
    STARTING = 'starting'
    STOPPING = 'stopping'
    TERMINATING = 'terminating'
    EXECUTING_ACTION = 'executing_action'

    # Errors
    ERROR = 'error'

    SAFE_STATES = [FINISHED, ERROR]

    # Not sure?
    OK = 'ok'
    RUNNING = 'running'
    REBOOTING = 'rebooting'

    STATUS = Choices(PENDING, LAUNCHING, CONFIGURING, SYNCING, PROVISIONING,
                     ORCHESTRATING, FINALIZING, DESTROYING, FINISHED,
                     STARTING, STOPPING, TERMINATING, EXECUTING_ACTION, ERROR)

    class Meta:
        unique_together = ('owner', 'title')
        ordering = ('title',)

    # The "owner" of the stack and all of its infrastructure
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='stacks')

    # What blueprint did this stack derive from?
    blueprint = models.ForeignKey('blueprints.Blueprint',
                                  related_name='stacks')

    # An arbitrary namespace for this stack. Mainly useful for Blueprint
    # hostname templates
    namespace = models.CharField(max_length=64, blank=True)

    # is this stack publicly available -- meaning it can be found by other
    # users and will remain in read-only mode to them
    public = models.BooleanField(default=False)

    # Where on disk is the salt-cloud map file stored
    map_file = DeletingFileField(
        max_length=255,
        upload_to=get_map_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    # Where on disk is the custom salt top.sls file stored
    top_file = DeletingFileField(
        max_length=255,
        upload_to=get_top_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(
            location=settings.STACKDIO_CONFIG.salt_core_states))

    # Where on disk is the custom overstate file stored
    overstate_file = DeletingFileField(
        max_length=255,
        upload_to=get_overstate_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(
            location=settings.STACKDIO_CONFIG.salt_core_states))

    # Where on disk is the global overstate file stored
    global_overstate_file = DeletingFileField(
        max_length=255,
        upload_to=get_global_overstate_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(
            location=settings.STACKDIO_CONFIG.salt_core_states))

    # Where on disk is the custom pillar file for custom configuration for
    # all salt states used by the top file
    pillar_file = DeletingFileField(
        max_length=255,
        upload_to=get_pillar_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    # storage for properties file
    props_file = DeletingFileField(
        max_length=255,
        upload_to=get_props_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    # Use our custom manager object
    objects = StackManager()

    def __unicode__(self):
        return u'{0} (id={1})'.format(self.title, self.pk)

    def set_status(self, event, status, detail, level=Level.INFO):
        self.status = status
        self.save()
        self.history.create(event=event, status=status,
                            status_detail=detail, level=level)

    def get_driver_hosts_map(self, host_ids=None):
        """
        Stacks are comprised of multiple hosts. Each host may be
        located in different cloud providers. This method returns
        a map of the underlying driver implementation and the hosts
        that running in the provider.

        @param host_ids (list); a list of primary keys for the hosts
            we're interested in
        @returns (dict); each key is a provider driver implementation
            with QuerySet value for the matching host objects
        """
        hosts = self.get_hosts(host_ids)
        providers = {}
        for h in hosts:
            providers.setdefault(h.get_provider(), []).append(h)

        result = {}
        for p, hosts in providers.iteritems():
            result[p.get_driver()] = self.hosts.filter(
                cloud_profile__cloud_provider=p,
                pk__in=[h.pk for h in hosts]
            )
        return result

    def get_hosts(self, host_ids=None):
        """
        Quick way of getting all hosts or a subset for this stack.

        @host_ids (list); list of primary keys of hosts in this stack
        @returns (QuerySet);
        """
        if not host_ids:
            return self.hosts.all()
        return self.hosts.filter(id__in=host_ids)

    @property
    def properties(self):
        if not self.props_file:
            return {}
        with open(self.props_file.path) as f:
            return json.loads(f.read())

    @properties.setter
    def properties(self, props):
        properties = self.properties
        recursive_update(properties, props)
        props_json = json.dumps(properties, indent=4)
        if not self.props_file:
            self.props_file.save(self.slug + '.props', ContentFile(props_json))
        else:
            with open(self.props_file.path, 'w') as f:
                f.write(props_json)

    def create_security_groups(self):
        for hostdef in self.blueprint.host_definitions.all():

            # create the managed security group for each host definition
            # and assign the rules to the group
            sg_name = 'managed-{0}-{1}-stack-{2}'.format(
                self.owner.username,
                hostdef.slug,
                self.pk)
            sg_description = 'stackd.io managed security group'

            # cloud provider and driver for the host definition
            cloud_provider = hostdef.cloud_profile.cloud_provider
            driver = cloud_provider.get_driver()

            try:

                sg_id = driver.create_security_group(sg_name,
                                                     sg_description,
                                                     delete_if_exists=True)
            except Exception, e:
                err_msg = 'Error creating security group: {0}'.format(str(e))
                self.set_status('create_security_groups', self.ERROR,
                                err_msg, Level.ERROR)

            logger.debug('Created security group {0}: {1}'.format(
                sg_name,
                sg_id
            ))

            for access_rule in hostdef.access_rules.all():
                driver.authorize_security_group(sg_id, {
                    'protocol': access_rule.protocol,
                    'from_port': access_rule.from_port,
                    'to_port': access_rule.to_port,
                    'rule': access_rule.rule,
                })

            # create the security group object that we can use for tracking
            self.security_groups.create(
                owner=self.owner,
                cloud_provider=cloud_provider,
                blueprint_host_definition=hostdef,
                name=sg_name,
                description=sg_description,
                group_id=sg_id,
                is_managed=True
            )

    def create_hosts(self, host_definition=None, count=None, backfill=False):
        """
        Creates host objects on this Stack. If no arguments are given, then
        all hosts available based on the Stack's blueprint host definitions
        will be created. If args are given, then only the `count` for the
        given `host_definition` will be created.

        @param host_definition (BlueprintHostDefinition object); the host
            definition to use for creating new hosts. If None, all host
            definitions for the stack's blueprint will be used.
        @param count (int); the number of hosts to create. If None, all
            hosts will be created.
        @param backfill (bool); If True, then hosts will be created with
            hostnames that fill in any gaps if necessary. If False, then
            hostnames will start at the end of the host list. This is only
            used when `host_definition` and `count` arguments are provided.
        """

        created_hosts = []

        if host_definition is None:
            host_definitions = self.blueprint.host_definitions.all()
        else:
            host_definitions = [host_definition]

        for hostdef in host_definitions:
            hosts = self.hosts.all()

            if count is None:
                start, end = 0, hostdef.count
                indexes = xrange(start, end)
            elif not hosts:
                start, end = 0, count
                indexes = xrange(start, end)
            else:
                if backfill:
                    hosts = hosts.order_by('index')

                    # The set of existing host indexes
                    host_indexes = set([h.index for h in hosts])

                    # The last index available
                    last_index = sorted(host_indexes)[-1]

                    # The set of expected indexes based on the last known
                    # index
                    expected_indexes = set(range(last_index + 1))

                    # Any gaps any the expected indexes?
                    gaps = expected_indexes - host_indexes

                    indexes = []
                    if gaps:
                        indexes = list(gaps)

                    count -= len(indexes)
                    start = sorted(host_indexes)[-1] + 1
                    end = start + count
                    indexes += range(start, end)
                else:
                    start = hosts.order_by('-index')[0].index + 1
                    end = start + count
                    indexes = xrange(start, end)

            # all components defined in the host definition
            components = hostdef.formula_components.all()

            # iterate over the host definition count and create individual
            # host records on the stack
            for i in indexes:
                hostname = hostdef.hostname_template.format(
                    namespace=self.namespace,
                    username=self.owner.username,
                    index=i
                )

                kwargs = dict(
                    index=i,
                    cloud_profile=hostdef.cloud_profile,
                    blueprint_host_definition=hostdef,
                    instance_size=hostdef.size,
                    hostname=hostname,
                    sir_price=hostdef.spot_price,
                    state=Host.PENDING
                )

                if hostdef.cloud_profile.cloud_provider.vpc_enabled:
                    kwargs['subnet_id'] = hostdef.subnet_id
                else:
                    kwargs['availability_zone'] = hostdef.zone

                host = self.hosts.create(**kwargs)

                # Add in the cloud provider default security groups as
                # defined by an admin.
                provider_groups = set(list(
                    host.cloud_profile.cloud_provider.security_groups.filter(
                        is_default=True
                    )
                ))

                host.security_groups.add(*provider_groups)

                # Add in the security group provided by this host definition
                security_group = SecurityGroup.objects.get(
                    stack=self,
                    blueprint_host_definition=hostdef
                )
                host.security_groups.add(security_group)

                # add formula components
                host.formula_components.add(*components)

                for volumedef in hostdef.volumes.all():
                    self.volumes.create(
                        host=host,
                        snapshot=volumedef.snapshot,
                        hostname=hostname,
                        device=volumedef.device,
                        mount_point=volumedef.mount_point
                    )

                created_hosts.append(host)

        return created_hosts

    def _generate_map_file(self):
        # TODO: Figure out a way to make this provider agnostic

        # TODO: Should we store this somewhere instead of assuming
        # the master will always be this box?
        master = socket.getfqdn()

        profiles = {}

        hosts = self.hosts.all()
        cluster_size = len(hosts)

        for host in hosts:
            # load provider yaml to extract default security groups
            cloud_provider = host.cloud_profile.cloud_provider
            cloud_provider_yaml = yaml.safe_load(
                cloud_provider.yaml)[cloud_provider.slug]

            # pull various stuff we need for a host
            roles = [c.component.sls_path for
                     c in host.formula_components.all()]
            instance_size = host.instance_size.title
            security_groups = set([
                sg.group_id for sg in host.security_groups.all()
            ])
            volumes = host.volumes.all()

            domain = cloud_provider_yaml['append_domain']
            fqdn = '{0}.{1}'.format(host.hostname, domain)

            # The volumes will be defined on the map as well as in the grains.
            # Those in the map are used by salt-cloud to create and attach
            # the volumes (using the snapshot), whereas those on the grains
            # are available for states and modules to play with (e.g., to
            # mount the devices)
            map_volumes = []
            for vol in volumes:
                v = {
                    'device': vol.device,
                    'mount_point': vol.mount_point,
                    'filesystem_type': vol.snapshot.filesystem_type,
                }
                if vol.volume_id:
                    v['volume_id'] = vol.volume_id
                else:
                    v['snapshot'] = vol.snapshot.snapshot_id

                map_volumes.append(v)

            host_metadata = {
                host.hostname: {
                    # The parameters in the minion dict will be passed on
                    # to the minion and set in its default configuration
                    # at /etc/salt/minion. This is where you would override
                    # any default values set by salt-minion
                    'minion': {
                        'master': master,
                        'log_level': 'debug',
                        'log_level_logfile': 'debug',
                        'mine_functions': {
                            'grains.items': []
                        },

                        # Grains are very useful when you need to set some
                        # static information about a machine (e.g., what stack
                        # id its registered under or how many total machines
                        # are in the cluster)
                        'grains': {
                            'roles': roles,
                            'stack_id': int(self.pk),
                            'fqdn': fqdn,
                            'domain': domain,
                            'cluster_size': cluster_size,
                            'stack_pillar_file': self.pillar_file.path,
                            'volumes': map_volumes,
                        },
                    },

                    # The rest of the settings in the map are salt-cloud
                    # specific and control the VM in various ways
                    # depending on the cloud provider being used.
                    'size': instance_size,
                    'securitygroupid': list(security_groups),
                    'volumes': map_volumes,
                }
            }

            if cloud_provider.vpc_enabled:
                host_metadata[host.hostname]['subnetid'] = host.subnet_id
            else:
                host_metadata[host.hostname]['availability_zone'] \
                    = host.availability_zone.title

            # Add in spot instance config if needed
            if host.sir_price:
                host_metadata[host.hostname]['spot_config'] = {
                    'spot_price': str(host.sir_price)  # convert to string
                }

            profiles.setdefault(host.cloud_profile.slug, []) \
                .append(host_metadata)

        map_file_yaml = yaml.safe_dump(profiles,
                                       default_flow_style=False)

        if not self.map_file:
            self.map_file.save(self.slug + '.map', ContentFile(map_file_yaml))
        else:
            with open(self.map_file.path, 'w') as f:
                f.write(map_file_yaml)

    def _generate_top_file(self):
        top_file_data = {
            'base': {
                'G@stack_id:{0}'.format(self.pk): [
                    {'match': 'compound'},
                    'core.*',
                ]
            }
        }

        top_file_yaml = yaml.safe_dump(top_file_data, default_flow_style=False)
        if not self.top_file:
            self.top_file.save('stack_{0}_top.sls'.format(self.pk),
                               ContentFile(top_file_yaml))
        else:
            with open(self.top_file.path, 'w') as f:
                f.write(top_file_yaml)

    def _generate_overstate_file(self):
        hosts = self.hosts.all()
        stack_target = 'G@stack_id:{0}'.format(self.pk)

        def _matcher(sls_set):
            return ' and '.join(
                [stack_target] + ['G@roles:{0}'.format(i) for i in sls_set]
            )

        groups = {}
        for host in hosts:
            for c in host.formula_components.all():
                groups.setdefault(
                    c.order, set()
                ).add(c.component.sls_path)

        overstate = {}
        for order in sorted(groups.keys()):
            for role in groups[order]:
                overstate[role] = {
                    'match': _matcher([role]),
                    'sls': list([role]),
                }
                depend = order - 1
                while depend >= 0:
                    if depend in groups.keys():
                        overstate[role]['require'] = list(groups[depend])
                        break
                    depend -= 1

        yaml_data = yaml.safe_dump(overstate, default_flow_style=False)
        if not self.overstate_file:
            self.overstate_file.save(
                'stack_{0}_overstate.sls'.format(self.pk),
                ContentFile(yaml_data))
        else:
            with open(self.overstate_file.path, 'w') as f:
                f.write(yaml_data)

    def _generate_overstate_file_bak(self):
        hosts = self.hosts.all()

        # Get the unique set of components for this stack
        components = set()
        for host in hosts:
            components.update(list(
                host.formula_components.all().order_by('order')
            ))

        # build a data structure more suitable for helping us build
        # the overstate dict
        groups = {}
        for c in components:
            """
            {
                order_0: {
                    host_0: [sls, sls, ...],
                    host_1: [sls, sls, ...],
                    ...
                },
                order_1: {
                    ...
                }
                ...
            }
            """
            groups.setdefault(
                c.order, {}
            ).setdefault(
                '{0}-{1}'.format(c.order, c.host.slug), []
            ).append(
                c.component.sls_path
            )

        # now we know what order each defined blueprint host is in and
        # the corresponding components to be installed. We will match
        # hosts based on the stack_id and all roles/SLS. Each group of
        # hosts beyond the first will have a requirement on the group
        # before it
        overstate = {}
        for i in sorted(groups.keys()):
            for host, sls in groups[i].iteritems():
                matches = ' and '.join(['G@roles:{0}'.format(r) for r in sls])
                overstate[host] = {
                    'match': 'G@stack_id:{0} and {1}'.format(self.pk, matches),
                    'sls': sls
                }

                if i > 0:
                    overstate[host]['require'] = groups[i - 1].keys()

        # Dump the overstate dict into yaml for salt
        yaml_data = yaml.safe_dump(overstate, default_flow_style=False)
        if not self.overstate_file:
            self.overstate_file.save(
                'stack_{0}_overstate.sls'.format(self.pk),
                ContentFile(yaml_data))
        else:
            with open(self.overstate_file.path, 'w') as f:
                f.write(yaml_data)

    def _generate_global_overstate_file(self):
        providers_map = {}
        for host in self.hosts.all():
            providers_map.setdefault(host.cloud_profile.cloud_provider, []).append(host.hostname)

        overstate = {}

        for provider, hosts in providers_map.items():

            target = ' or '.join(hosts)

            groups = {}
            for c in provider.global_formula_components.all():
                groups.setdefault(
                    c.order, set()
                ).add(c.component.sls_path)

            for order in sorted(groups.keys()):
                for role in groups[order]:
                    state_title = '{0}_{1}'.format(provider.slug, role)
                    overstate[state_title] = {
                        'match': target,
                        'sls': list([role]),
                    }
                    depend = order - 1
                    while depend >= 0:
                        if depend in groups.keys():
                            overstate[role]['require'] = list(groups[depend])
                            break
                        depend -= 1

        yaml_data = yaml.safe_dump(overstate, default_flow_style=False)
        if not self.global_overstate_file:
            self.global_overstate_file.save(
                get_global_overstate_file_path(self, None),
                ContentFile(yaml_data))
        else:
            with open(self.global_overstate_file.path, 'w') as f:
                f.write(yaml_data)

    def _generate_pillar_file(self):
        from blueprints.models import BlueprintHostFormulaComponent

        # pull the ssh_user property from the stackd.io config file and
        # if the username value is $USERNAME, we'll substitute the stack
        # owner's username instead
        username = settings.STACKDIO_CONFIG.ssh_user
        if username == '$USERNAME':
            username = self.owner.username

        pillar_props = {
            '__stackdio__': {
                'username': username,
                'publickey': self.owner.settings.public_key,
            }
        }

        # If any of the formulas we're using have default pillar
        # data defined in its corresponding SPECFILE, we need to pull
        # that into our stack pillar file.

        # First get the unique set of formulas
        hosts = self.hosts.all()
        formulas = set(
            [c.component.formula for
             c in BlueprintHostFormulaComponent.objects.filter(
                 hosts__in=hosts)]
        )

        # for each unique formula, pull the properties from the SPECFILE
        for formula in formulas:
            recursive_update(pillar_props, formula.properties)

        # Add in properties that were supplied via the blueprint and during
        # stack creation
        recursive_update(pillar_props, self.properties)

        pillar_file_yaml = yaml.safe_dump(pillar_props,
                                          default_flow_style=False)

        if not self.pillar_file:
            self.pillar_file.save('{0}.pillar'.format(self.slug),
                                  ContentFile(pillar_file_yaml))
        else:
            with open(self.pillar_file.path, 'w') as f:
                f.write(pillar_file_yaml)

    def query_hosts(self):
        """
        Uses salt-cloud to query all the hosts for the given stack id.
        """
        try:
            if not self.map_file:
                return {}

            logger.info('get_hosts_info: {0!r}'.format(self))

            # salt-cloud command to pull host information with
            # a yaml output
            query_cmd = ' '.join([
                'salt-cloud',
                '--full-query',             # execute a full query
                '--out=yaml',               # output in yaml format
                '--config-dir={0}',         # salt config dir
                '--map={1}',                # map file to use
            ]).format(
                settings.STACKDIO_CONFIG.salt_config_root,
                self.map_file.path,
            )

            result = envoy.run(query_cmd)

            # Run the envoy stdout through the yaml parser. The format
            # will always be a dictionary with one key (the provider type)
            # and a value that's a dictionary containing keys for every
            # host in the stack.
            yaml_result = yaml.safe_load(result.std_out)

            if not yaml_result:
                return {}

            # yaml_result contains all host information in the stack, but
            # we have to dig a bit to get individual host metadata out
            # of provider and provider type dictionaries
            host_result = {}
            for host in self.hosts.all():
                cloud_provider = host.cloud_profile.cloud_provider
                provider_type = cloud_provider.provider_type

                # each host is buried in a cloud provider type dict that's
                # inside a cloud provider name dict
                host_result[host.hostname] = yaml_result \
                    .get(cloud_provider.slug, {}) \
                    .get(provider_type.type_name, {}) \
                    .get(host.hostname, None)

            return host_result

        except Exception:
            logger.exception('Unhandled exception')
            raise

    def get_root_directory(self):
        if self.map_file:
            return os.path.dirname(self.map_file.path)
        if self.props_file:
            return os.path.dirname(self.props_file.path)
        return None

    def get_log_directory(self):
        root_dir = self.get_root_directory()
        log_dir = os.path.join(root_dir, 'logs')
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        return log_dir

    def get_security_groups(self):
        groups = SecurityGroup.objects.filter(is_managed=True,
                                              hosts__stack=self)
        ret = []
        for group in groups:
            if group not in ret:
                ret.append(group)

        return ret

    def get_role_list(self):
        roles = set()
        for bhd in self.blueprint.host_definitions.all():
            for formula_component in bhd.formula_components.all():
                roles.add(formula_component.component.sls_path)
        return list(roles)


class StackHistory(TimeStampedModel, StatusDetailModel):

    class Meta:
        verbose_name_plural = 'stack history'
        ordering = ['-created', '-id']

    STATUS = Stack.STATUS

    stack = models.ForeignKey('Stack', related_name='history')

    # What 'event' (method name, task name, etc) that caused
    # this status update
    event = models.CharField(max_length=128)

    # The human-readable description of the event
    # status = models.TextField(blank=True)

    # Optional: level (DEBUG, INFO, WARNING, ERROR, etc)
    level = models.CharField(max_length=16, choices=(
        (Level.DEBUG, Level.DEBUG),
        (Level.INFO, Level.INFO),
        (Level.WARN, Level.WARN),
        (Level.ERROR, Level.ERROR),
    ))


class StackAction(TimeStampedModel, model_utils.models.StatusModel):
    WAITING = 'waiting'
    RUNNING = 'running'
    FINISHED = 'finished'
    ERROR = 'error'
    STATUS = Choices(WAITING, RUNNING, FINISHED, ERROR)

    class Meta:
        verbose_name_plural = 'stack actions'

    stack = models.ForeignKey('Stack', related_name='actions')

    # The started executing
    start = models.DateTimeField()

    # Type of action (custom, launch, etc)
    type = models.CharField(max_length=50)

    # Which hosts we want to target
    host_target = models.CharField(max_length=255)

    # The command to be run (for custom actions)
    command = models.TextField()

    # The output from the action
    std_out_storage = models.TextField()

    # The error output from the action
    std_err_storage = models.TextField()

    def std_out(self):
        if self.std_out_storage != "":
            return json.loads(self.std_out_storage)
        else:
            return []

    def std_err(self):
        return self.std_err_storage

    def submit_time(self):
        return self.created

    def start_time(self):
        if self.status in (self.RUNNING, self.FINISHED):
            return self.start
        else:
            return ""

    def finish_time(self):
        if self.status == self.FINISHED:
            return self.modified
        else:
            return ""


class Host(TimeStampedModel, StatusDetailModel):
    PENDING = 'pending'
    OK = 'ok'
    DELETING = 'deleting'
    STATUS = Choices(PENDING, OK, DELETING)

    class Meta:
        ordering = ['blueprint_host_definition', '-index']

    # TODO: We should be using generic foreign keys here to a cloud provider
    # specific implementation of a Host object. I'm not exactly sure how this
    # will work, but I think by using Django's content type system we can make
    # it work...just not sure how easy it will be to extend, maintain, etc.

    stack = models.ForeignKey('Stack',
                              related_name='hosts')

    cloud_profile = models.ForeignKey('cloud.CloudProfile',
                                      related_name='hosts')

    instance_size = models.ForeignKey('cloud.CloudInstanceSize',
                                      related_name='hosts')

    availability_zone = models.ForeignKey('cloud.CloudZone',
                                          null=True,
                                          related_name='hosts')

    subnet_id = models.CharField(max_length=32, blank=True, default='')

    blueprint_host_definition = models.ForeignKey(
        'blueprints.BlueprintHostDefinition',
        related_name='hosts')

    formula_components = models.ManyToManyField(
        'blueprints.BlueprintHostFormulaComponent',
        related_name='hosts')

    hostname = models.CharField(max_length=64)

    index = models.IntegerField()

    security_groups = models.ManyToManyField('cloud.SecurityGroup',
                                             related_name='hosts')

    # The machine state as provided by the cloud provider
    state = models.CharField(max_length=32, default='unknown')
    state_reason = models.CharField(max_length=255, default='', blank=True)

    # This must be updated automatically after the host is online.
    # After salt-cloud has launched VMs, we will need to look up
    # the DNS name set by whatever cloud provider is being used
    # and set it here
    provider_dns = models.CharField(max_length=64, blank=True)
    provider_private_dns = models.CharField(max_length=64, blank=True)
    provider_private_ip = models.CharField(max_length=64, blank=True)

    # The FQDN for the host. This includes the hostname and the
    # domain if it was registered with DNS
    fqdn = models.CharField(max_length=255, blank=True)

    # Instance id of the running host. This is provided by the cloud
    # provider
    instance_id = models.CharField(max_length=32, blank=True)

    # Spot instance request ID will be populated when metadata is refreshed
    # if the host has been configured to launch spot instances. By default,
    # it will be unknown and will be set to NA if spot instances were not
    # used.
    sir_id = models.CharField(max_length=32,
                              default='unknown')

    # The spot instance price for this host if using spot instances
    sir_price = models.DecimalField(max_digits=5,
                                    decimal_places=2,
                                    null=True)

    def __unicode__(self):
        return self.hostname

    def get_provider(self):
        return self.cloud_profile.cloud_provider

    def get_provider_type(self):
        return self.cloud_profile.cloud_provider.provider_type

    def get_driver(self):
        return self.cloud_profile.get_driver()
