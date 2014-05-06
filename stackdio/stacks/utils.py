import logging
import os
import random
import yaml
from django.conf import settings
from datetime import datetime

import salt.config as config
import salt.cloud
import salt.client
import salt.utils
import salt.key
import salt.utils.cloud

logger = logging.getLogger(__name__)


def get_salt_cloud_log_file(stack, suffix):
    '''
    suffix is a string (e.g, launch, overstate, highstate, error, etc)
    '''
    # Set up logging for this launch
    root_dir = stack.get_root_directory()
    log_dir = stack.get_log_directory()

    now = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_file = os.path.join(log_dir, '{0}.{1}.log'.format(now, suffix))
    log_symlink = os.path.join(root_dir, '{0}.log.latest'.format(suffix))

    # "touch" the log file and symlink it to the latest
    with open(log_file, 'w') as f:  # NOQA
        pass

    if os.path.isfile(log_symlink):
        os.remove(log_symlink)
    os.symlink(log_file, log_symlink)

    return log_file


def get_launch_command(stack, log_file, parallel=False):
    cmd_args = [
        'salt-cloud',
        '-y',                    # assume yes
        '-lquiet',               # no logging on console
        '--log-file {0}',        # where to log
        '--log-file-level debug',  # full logging
        '--out=yaml',            # return YAML formatted results
        '-m {1}',                # the map file to use for launching
        # Until environment variables work
        '--providers-config={2}',
        '--profiles={3}',
        '--cloud-config={4}',
    ]

    # parallize the salt-cloud launch
    if parallel:
        cmd_args.append('-P')

    return ' '.join(cmd_args).format(
        log_file,
        stack.map_file.path,
        settings.STACKDIO_CONFIG.salt_providers_dir,
        settings.STACKDIO_CONFIG.salt_profiles_dir,
        settings.STACKDIO_CONFIG.salt_cloud_config,
    )


def get_salt_cloud_opts():
    return config.cloud_config(
        settings.STACKDIO_CONFIG.salt_cloud_config
    )


def get_salt_master_opts():
    return config.cloud_config(
        settings.STACKDIO_CONFIG.salt_master_config
    )


def get_stack_map_data(stack):
    opts = get_salt_cloud_opts()
    opts.update({
        'map': stack.map_file.path,
        'hard': False,
    })
    mapper = salt.cloud.Map(opts)
    return mapper.map_data()


def regenerate_minion_keys(vm_, __opts__, **kwargs):
    logger.info('Generating minion keys for: {0}'.format(vm_['name']))

    # Kill existing master keys
    key_cli = salt.key.KeyCLI(__opts__)
    matches = key_cli.key.name_match(vm_['name'])
    if matches:
        key_cli.key.delete_key(match_dict=matches)

    # Kill remote master keys
    salt.utils.cloud.root_cmd('rm -rf /etc/salt/pki', **kwargs)

    # Generate new keys for the minion
    minion_pem, minion_pub = salt.utils.cloud.gen_keys(
        config.get_cloud_config_value('keysize', vm_, __opts__)
    )

    # Preauthorize the newly generated keys
    key_id = vm_.get('id', vm_['name'])
    salt.utils.cloud.accept_key(
        __opts__['pki_dir'], minion_pub, key_id
    )
    return minion_pem, minion_pub


def ping_stack_hosts(stack):
    '''
    Returns a set of hostnames in the stack that were reachable via
    a ping request.

    NOTE: This specifically targets the hosts in a stack instead of
    pinging all available hosts that salt is managing.
    '''
    client = salt.client.LocalClient(
        settings.STACKDIO_CONFIG.salt_master_config
    )
    target = ' or '.join(
        [hd.hostname_template.format(namespace=stack.namespace,
                                     index='*')
         for hd in stack.blueprint.host_definitions.all()])
    return set(client.cmd(target, 'test.ping', expr_form='compound'))


def find_zombie_hosts(stack):
    '''
    Returns a QuerySet of host objects in the given stack that were not
    reachable via a ping request.
    '''
    pinged_hosts = ping_stack_hosts(stack)
    hostnames = set([h[0] for h in stack.hosts.all().values_list('hostname')])
    zombies = hostnames - pinged_hosts
    if not zombies:
        return None

    return stack.hosts.filter(hostname=zombies.pop())
    # return stack.hosts.filter(hostname__in=zombies)


def bootstrap_hosts(stack, hosts):
    '''
    Iterates over the given `hosts` and executes the bootstrapping process
    via salt cloud.

    @param stack (stacks.models.Stack) - Stack object (should be the stack that
        owns the given `hosts`.
    @param hosts (QuerySet) - QuerySet of stacks.models.Host objects

    WARNING: This is not parallelized. My only hope is that the list is
    relatively small (e.g, only bootstrap hosts that were unsuccessful...see
    the `find_zombie_hosts` method)
    '''
    __opts__ = get_salt_cloud_opts()
    dmap = get_stack_map_data(stack)

    for host in hosts:
        vm_ = dmap['existing'].get(host.hostname)
        logger.info('Bootstrapping host {0}'.format(host.hostname))
        deploy_vm(host, vm_, __opts__)


def deploy_vm(host_obj, vm_, __opts__):
    '''
    Basically duplicating the deploy logic from `salt.cloud.clouds.ec2::create`
    so we can bootstrap minions whenever needed. Ideally, this would be handled
    in salt-cloud directly, but for now it's easier to handle this on our end.

    @param host_obj (stacks.models.Host) - a Django ORM Host object
    @param vm_ (dict) - the vm data structure that salt likes to use
    @param __opts__ (dict) - the big config object that salt passes around to
        all of its modules. See `get_salt_cloud_opts`
    '''

    # Start gathering the information we need to build up the deploy kwargs
    # object that will be handed to `salt.utils.cloud.deploy_script`

    # The SSH username we'll use for pushing files and remote execution. This
    # should already be defined in the cloud profile this host is using.
    username = config.get_cloud_config_value(
        'ssh_username', vm_, __opts__, search_global=False, default=None
    )

    # The private key, along with ssh_username above, is necessary for SSH
    key_filename = config.get_cloud_config_value(
        'private_key', vm_, __opts__, search_global=False, default=None
    )

    # Which deploy script will be run to bootstrap the minions. This is pre-
    # defined in the cloud profile for the host.
    deploy_script = salt.utils.cloud.os_script(
        config.get_cloud_config_value('script', vm_, __opts__),
        vm_,
        __opts__,
        salt.utils.cloud.salt_config_to_yaml(
            salt.utils.cloud.minion_config(__opts__, vm_)
        )
    )

    # Generate the master's public fingerprint
    master_finger = salt.utils.pem_finger(os.path.join(
        __opts__['pki_dir'], 'master.pub'
    ))
    vm_['master_finger'] = master_finger

    # The big deploy kwargs object. This is roughly the exact same as that
    # in the salt.cloud.clouds.ec2::create method.
    deploy_kwargs = {
        'host': host_obj.provider_dns,
        'hostname': host_obj.provider_dns,
        'username': username,
        'key_filename': key_filename,
        'tmp_dir': config.get_cloud_config_value(
            'tmp_dir', vm_, __opts__, default='/tmp/.saltcloud'
        ),
        'deploy_command': config.get_cloud_config_value(
            'deploy_command', vm_, __opts__,
            default='/tmp/.saltcloud/deploy.sh',
        ),
        'tty': config.get_cloud_config_value(
            'tty', vm_, __opts__, default=True
        ),
        'script': deploy_script,
        'name': vm_['name'],
        'sudo': config.get_cloud_config_value(
            'sudo', vm_, __opts__, default=(username != 'root')
        ),
        'sudo_password': config.get_cloud_config_value(
            'sudo_password', vm_, __opts__, default=None
        ),
        'start_action': __opts__['start_action'],
        'parallel': False,
        'conf_file': __opts__['conf_file'],
        'sock_dir': __opts__['sock_dir'],
        'keep_tmp': True,
        'preseed_minion_keys': vm_.get('preseed_minion_keys', None),
        'display_ssh_output': False,
        'minion_conf': salt.utils.cloud.minion_config(__opts__, vm_),
        'script_args': config.get_cloud_config_value(
            'script_args', vm_, __opts__
        ),
        'script_env': config.get_cloud_config_value(
            'script_env', vm_, __opts__
        ),
        'make_minion': config.get_cloud_config_value(
            'make_minion', vm_, __opts__, default=True
        ),
    }

    # Regenerate minion keys which will kill the keys for this host
    # on the master as well as the pki directory on the minion to
    # ensure we have the same keys in use or else the automatic
    # key acceptance will fail and the minion will still be in limbo
    minion_pem, minion_pub = regenerate_minion_keys(vm_,
                                                    __opts__,
                                                    **deploy_kwargs)
    deploy_kwargs.update({
        'minion_pem': minion_pem,
        'minion_pub': minion_pub,
    })

    logger.info('Executing deploy_script for {0}'.format(vm_['name']))

    # TODO(abemusic): log this to a file instead of dumping to celery
    deployed = salt.utils.cloud.deploy_script(**deploy_kwargs)
    if deployed:
        logger.info('Salt installed on {name}'.format(**vm_))
    else:
        logger.error('Failed to start Salt on Cloud VM {name}'.format(**vm_))

    # TODO(abemusic): the create method in the EC2 driver currently handles
    # the creation logic for EBS volumes. We should be checking for those
    # volumes and creating them if necessary here.

    return deployed


def load_map_file(stack):
    with open(stack.map_file.path, 'r') as f:
        map_yaml = yaml.safe_load(f)
    return map_yaml


def write_map_file(stack, data):
    with open(stack.map_file.path, 'w') as f:
        f.write(yaml.safe_dump(data, default_flow_style=False))


def mod_hosts_map(stack, n, **kwargs):
    '''
    Selects n random hosts for the given stack and modifies/adds
    the map entry for thoses hosts with the kwargs.
    '''
    map_yaml = load_map_file(stack)

    population = []
    for k, v in map_yaml.iteritems():
        population.extend(v)

    # randomly select n hosts
    hosts = random.sample(population, n)

    # modify the hosts
    for host in hosts:
        host[host.keys()[0]].update(kwargs)

    write_map_file(stack, map_yaml)


def unmod_hosts_map(stack, *args):
    '''
    For debug method purpose only
    '''
    map_yaml = load_map_file(stack)

    population = []
    for k, v in map_yaml.iteritems():
        population.extend(v)

    for host in population:
        host_data = host[host.keys()[0]]
        for k in args:
            if k in host_data:
                del host_data[k]

    write_map_file(stack, map_yaml)
