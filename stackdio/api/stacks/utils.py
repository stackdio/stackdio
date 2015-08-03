# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import print_function

import logging
import multiprocessing
import os
import random
from datetime import datetime

import salt.client
import salt.cloud
import salt.config as config
import salt.key
import salt.utils
import yaml
from django.conf import settings


logger = logging.getLogger(__name__)


def filter_actions(user, stack, actions):
    ret = []
    for action in actions:
        the_action = action
        if action == 'command':
            the_action = 'execute'
        elif action == 'propagate-ssh':
            the_action = 'admin'
        if user.has_perm('stacks.{0}_stack'.format(the_action.lower()), stack):
            ret.append(action)

    return ret


def get_salt_cloud_log_file(stack, suffix):
    """
    suffix is a string (e.g, launch, overstate, highstate, error, etc)
    """
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
        '--assume-yes',
        '--log-level=quiet',        # no logging on console
        '--log-file={0}',           # where to log
        '--log-file-level=debug',   # full logging
        '--config-dir={1}',         # salt config dir
        '--out=yaml',               # return YAML formatted results
        '--map={2}',                # the map file to use for launching
    ]

    # parallize the salt-cloud launch
    if parallel:
        cmd_args.append('--parallel')

    return ' '.join(cmd_args).format(
        log_file,
        settings.STACKDIO_CONFIG.salt_config_root,
        stack.map_file.path,
    )


def get_salt_cloud_opts():
    return config.cloud_config(
        settings.STACKDIO_CONFIG.salt_cloud_config
    )


def get_salt_master_opts():
    return config.cloud_config(
        settings.STACKDIO_CONFIG.salt_master_config
    )


def get_stack_mapper(stack):
    opts = get_salt_cloud_opts()
    opts.update({
        'map': stack.map_file.path,
        'hard': False,
    })
    return salt.cloud.Map(opts)


def get_stack_map_data(stack):
    mapper = get_stack_mapper(stack)
    return mapper.map_data()


def get_stack_vm_map(stack):
    dmap = get_stack_map_data(stack)
    vms = {}
    for k in ('create', 'existing',):
        if k in dmap:
            vms.update(dmap[k])
    return vms


def get_ssh_kwargs(host, vm_, __opts__):
    return {
        'host': host.provider_private_dns,
        'hostname': host.provider_private_dns,
        'timeout': 3,
        'display_ssh_output': False,
        'key_filename': config.get_cloud_config_value(
            'private_key', vm_, __opts__, search_global=False, default=None
        ),
        'username': config.get_cloud_config_value(
            'ssh_username', vm_, __opts__, search_global=False, default=None
        )

    }


def regenerate_minion_keys(host, vm_, __opts__):
    logger.info('Regenerating minion keys for: {0}'.format(vm_['name']))

    # Kill existing master keys
    key_cli = salt.key.KeyCLI(__opts__)
    matches = key_cli.key.name_match(vm_['name'])
    if matches:
        key_cli.key.delete_key(match_dict=matches)

    # Kill remote master keys
    kwargs = get_ssh_kwargs(host, vm_, __opts__)
    tty = config.get_cloud_config_value(
        'tty', vm_, __opts__, default=True
    )
    sudo = config.get_cloud_config_value(
        'sudo', vm_, __opts__, default=True
    )
    salt.utils.cloud.root_cmd('rm -rf /etc/salt/pki', tty, sudo, **kwargs)

    # Generate new keys for the minion
    minion_pem, minion_pub = salt.utils.cloud.gen_keys(
        config.get_cloud_config_value('keysize', vm_, __opts__)
    )

    # Preauthorize the minion
    logger.info('Accepting key for {0}'.format(vm_['name']))
    key_id = vm_.get('id', vm_['name'])
    salt.utils.cloud.accept_key(
        __opts__['pki_dir'], minion_pub, key_id
    )

    return minion_pem, minion_pub


def ping_stack_hosts(stack):
    """
    Returns a set of hostnames in the stack that were reachable via
    a ping request.

    NOTE: This specifically targets the hosts in a stack instead of
    pinging all available hosts that salt is managing.
    """
    client = salt.client.LocalClient(
        settings.STACKDIO_CONFIG.salt_master_config
    )
    target = ' or '.join(
        [hd.hostname_template.format(namespace=stack.namespace,
                                     index='*')
         for hd in stack.blueprint.host_definitions.all()])
    return set(client.cmd(target, 'test.ping', expr_form='compound'))


def find_zombie_hosts(stack):
    """
    Returns a QuerySet of host objects in the given stack that were not
    reachable via a ping request.
    """
    pinged_hosts = ping_stack_hosts(stack)
    hostnames = set([h[0] for h in stack.hosts.all().values_list('hostname')])
    zombies = hostnames - pinged_hosts
    if not zombies:
        return None
    return stack.hosts.filter(hostname__in=zombies)


def check_for_ssh(stack, hosts):
    """
    Attempts to SSH to the given hosts.

    @param (stacks.models.Stack) - the stack the hosts belong to
    @param (list[stacks.models.Host]) - hosts to check for SSH
    @returns (list) - list of tuples (bool, Host) where the bool value is
    True if we could connect to Host over SSH, False otherwise
    """
    opts = get_salt_cloud_opts()
    vms = get_stack_vm_map(stack)
    mapper = get_stack_mapper(stack)
    result = []

    # Iterate over the given hosts. If the host hasn't been assigned a
    # hostname or is not physically running, there's nothing we can do
    # so we skip them
    for host in hosts:
        if host.hostname not in vms:
            continue

        # Build the standard vm_ object and inject some additional stuff
        # we'll need
        vm_ = vms[host.hostname]
        vm_provider_metadata = mapper.get_running_by_names(host.hostname)
        if not vm_provider_metadata:
            # host is not actually running so skip it
            continue

        provider, provider_type = vm_['provider'].split(':')
        vm_.update(
            vm_provider_metadata[provider][provider_type][vm_['name']]
        )

        # Pull some values we need to test for SSH
        key_filename = config.get_cloud_config_value(
            'private_key', vm_, opts, search_global=False, default=None
        )
        username = config.get_cloud_config_value(
            'ssh_username', vm_, opts, search_global=False, default=None
        )
        hostname = config.get_cloud_config_value(
            'private_ips', vm_, opts, search_global=False, default=None
        )

        # Test SSH connection
        ok = salt.utils.cloud.wait_for_passwd(
            hostname,
            key_filename=key_filename,
            username=username,
            ssh_timeout=1,  # 1 second timeout
            maxtries=3,     # 3 max tries per host
            trysleep=0.5,   # half second between tries
            display_ssh_output=False)

        result.append((ok, host))
    return result


def terminate_hosts(stack, hosts):
    """
    Uses salt-cloud to terminate the given list of hosts.

    @param (list[stacks.models.Host]) - the hosts to terminate.
    @returns None
    """

    opts = get_salt_cloud_opts()
    opts.update({
        'parallel': True
    })
    mapper = salt.cloud.Map(opts)
    hostnames = [h.hostname for h in hosts]
    logger.debug('Terminating hosts: {0}'.format(hostnames))
    mapper.destroy(hostnames)


def bootstrap_hosts(stack, hosts, parallel=True):
    """
    Iterates over the given `hosts` and executes the bootstrapping process
    via salt cloud.

    @param stack (stacks.models.Stack) - Stack object (should be the stack that
        owns the given `hosts`.
    @param hosts (QuerySet) - QuerySet of stacks.models.Host objects
    @param parallel (bool) - if True, we'll bootstrap in parallel using a
        multiprocessing Pool with a size determined by salt-cloud's config
        Defaults to True

    WARNING: This is not parallelized. My only hope is that the list is
    relatively small (e.g, only bootstrap hosts that were unsuccessful...see
    the `find_zombie_hosts` method)
    """
    __opts__ = get_salt_cloud_opts()
    dmap = get_stack_map_data(stack)

    # Params list holds the dict objects that will be used during
    # the deploy process; this will be handed off to the multiprocessing
    # Pool as the "iterable" argument
    params = []
    for host in hosts:
        vm_ = dmap['existing'].get(host.hostname)
        if vm_ is None:
            continue

        # Regenerate minion keys which will kill the keys for this host
        # on the master as well as the pki directory on the minion to
        # ensure we have the same keys in use or else the automatic
        # key acceptance will fail and the minion will still be in limbo
        minion_pem, minion_pub = regenerate_minion_keys(host, vm_, __opts__)

        # Add the keys
        vm_['priv_key'] = minion_pem
        vm_['pub_key'] = minion_pub

        d = {
            'host_obj': host,
            'vm_': vm_,
            '__opts__': __opts__,
        }

        # if we're not deploying in parallel, simply pass the dict
        # in, else we'll shove the dict into the params list
        if not parallel:
            deploy_vm(d)
        else:
            params.append(d)

    # Parallel deployment using multiprocessing Pool. The size of the
    # Pool object is either pulled from salt-cloud's config file or
    # the length of `params` is used. Note, it's highly recommended to
    # set the `pool_size` parameter in the salt-cloud config file to
    # prevent issues with larger pool sizes
    if parallel and len(params) > 0:
        pool_size = __opts__.get('pool_size', len(params))
        multiprocessing.Pool(pool_size).map(
            func=deploy_vm,
            iterable=params
        )


def deploy_vm(params):
    """
    Basically duplicating the deploy logic from `salt.cloud.clouds.ec2::create`
    so we can bootstrap minions whenever needed. Ideally, this would be handled
    in salt-cloud directly, but for now it's easier to handle this on our end.

    @param params (dict) - a dictionary containing all the necessary
        params we need and are defined below:

    @params[host_obj] (stacks.models.Host) - a Django ORM Host object
    @params[vm_] (dict) - the vm data structure that salt likes to use
    @params[__opts__] (dict) - the big config object that salt passes
        around to all of its modules. See `get_salt_cloud_opts`
    """

    host_obj = params['host_obj']
    vm_ = params['vm_']
    __opts__ = params['__opts__']

    logger.info('Deploying minion on VM: {0}'.format(vm_['name']))

    # Start gathering the information we need to build up the deploy kwargs
    # object that will be handed to `salt.utils.cloud.deploy_script`

    # The SSH username we'll use for pushing files and remote execution. This
    # should already be defined in the cloud image this host is using.
    username = config.get_cloud_config_value(
        'ssh_username', vm_, __opts__, search_global=False, default=None
    )

    # The private key, along with ssh_username above, is necessary for SSH
    key_filename = config.get_cloud_config_value(
        'private_key', vm_, __opts__, search_global=False, default=None
    )

    # Which deploy script will be run to bootstrap the minions. This is pre-
    # defined in the cloud image/profile for the host.
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
        'host': host_obj.provider_private_dns,
        'hostname': host_obj.provider_private_dns,
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
        'minion_pem': vm_['priv_key'],
        'minion_pub': vm_['pub_key'],
    }

    # TODO(abemusic): log this to a file instead of dumping to celery
    logger.info('Executing deploy_script for {0}'.format(vm_['name']))
    try:
        deployed = salt.utils.cloud.deploy_script(**deploy_kwargs)
        if deployed:
            logger.info('Salt installed on {name}'.format(**vm_))
        else:
            logger.error('Failed to start Salt on Cloud VM '
                         '{name}'.format(**vm_))
    except Exception:
        logger.exception('Unhandled exception while deploying minion')
        deployed = False

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
    """
    Selects n random hosts for the given stack and modifies/adds
    the map entry for thoses hosts with the kwargs.
    """
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
    """
    For debug method purpose only
    """
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


def create_zombies(stack, n):
    """
    For the given stack, will randomly select `n` hosts and kill the
    salt-minion service that should already be running on the host.

    @param (stacks.models.Stack) stack - the stack we're targeting
    @param (int) n - the number of randomly selected hosts to zombify
    @returns (None)
    """

    # Random sampling of n hosts
    hosts = random.sample(stack.hosts.all(), n)
    if not hosts:
        return

    client = salt.client.LocalClient(
        settings.STACKDIO_CONFIG.salt_master_config
    )
    result = client.cmd(
        ' or '.join([h.hostname for h in hosts]),
        'service.stop',
        arg=('salt-minion',),
        expr_form='compound'
    )
    print(result)
