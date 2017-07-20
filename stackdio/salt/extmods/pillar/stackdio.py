# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
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


"""
Loads a stack-specific pillar file. stack_pillar_file must be set in the grains
or this module will not be available to pillar.
"""

from __future__ import absolute_import

import logging
import os
import subprocess

import yaml
from stackdio.core.utils import recursive_update

# Set up logging
logger = logging.getLogger(__name__)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stackdio.server.settings.production')


def django_setup():
    """
    Our version of django.setup() that doesn't configure logging
    """
    from django.apps import apps
    from django.conf import settings

    apps.populate(settings.INSTALLED_APPS)

# setup django (without logging)
django_setup()

# These must be imported AFTER django is set up
from stackdio.api.cloud.models import CloudAccount  # NOQA
from stackdio.api.stacks.models import Stack  # NOQA
from stackdio.api.environments.models import Environment  # NOQA


def __virtual__():
    return True


def ext_pillar(minion_id, pillar, *args, **kwargs):
    """
    Basically, we need to provide additional pillar data to our states
    but only the pillar data defined for a stack. The user should have
    the ability to do this from the UI and the pillar file used will
    be located in the grains.
    """

    new_pillar = {}

    # First try the environment
    # (always do this regardless of whether there's we're in global orchestration or not)
    if 'env' in __grains__:
        _, _, env_name = __grains__['env'].partition('.')
        try:
            environment = Environment.objects.get(name=env_name)
            recursive_update(new_pillar, environment.get_full_pillar())
        except Environment.DoesNotExist:
            logger.info('Environment {} was specified in the grains '
                        'but was not found.'.format(env_name))

    global_orch = __grains__.get('global_orchestration', False)

    # Then the cloud account (but only if we ARE in global orchestration)
    if global_orch and 'cloud_account' in __grains__:
        try:
            account = CloudAccount.objects.get(slug=__grains__['cloud_account'])
            recursive_update(new_pillar, account.get_full_pillar())
        except CloudAccount.DoesNotExist:
            logger.info('Cloud account {} not found'.format(__grains__['cloud_account']))

    # Then the stack (but only if we ARE NOT in global orchestration)
    if not global_orch and 'stack_id' in __grains__ and isinstance(__grains__['stack_id'], int):
        try:
            stack = Stack.objects.get(id=__grains__['stack_id'])
            recursive_update(new_pillar, stack.get_full_pillar())
        except Stack.DoesNotExist:
            logger.info('Stack {} not found'.format(__grains__['stack_id']))

    # This is the old way, try it too for compatibility purposes.
    # Make it last so it has the highest precedence.
    if 'stack_pillar_file' in __grains__:
        # load the stack_pillar_file, rendered as yaml, and add it into the return dict
        try:
            with open(__grains__['stack_pillar_file'], 'r') as f:
                loaded_pillar = yaml.safe_load(f)
                recursive_update(new_pillar, loaded_pillar)
        except Exception as e:
            logger.exception(e)
            logger.critical('Unable to load/render stack_pillar_file. Is the YAML '
                            'properly formatted?')

    # Generate an SSL cert for the host
    ca_dir = __opts__.get('ssl_ca_dir')
    ca_subject = __opts__.get('ssl_ca_subject', '')
    ca_key_password = __opts__.get('ssl_ca_key_password')

    if not ca_dir:
        raise ValueError('Missing the ssl_ca_dir config option')

    if not ca_key_password:
        raise ValueError('Missing the ssl_ca_key_password config option')

    key_file = os.path.join(ca_dir, 'private', __grains__['fqdn'] + '.key')
    csr_file = os.path.join(ca_dir, 'csr', __grains__['fqdn'] + '.csr')
    cert_file = os.path.join(ca_dir, 'certs', __grains__['fqdn'] + '.crt')
    ca_cert_chain_file = os.path.join(ca_dir, 'certs', 'chain.crt')
    root_ca_cert_file = os.path.join(ca_dir, 'certs', 'root.crt')

    # Give everything a default
    ssl_opts = {
        'private_key': None,
        'certificate': None,
        'chained_certificate': None,
        'ca_certificate': None,
    }

    # Grab the private key
    if not os.path.exists(key_file):
        # Generate a key
        subprocess.call(['openssl', 'genrsa', '-out', key_file, '2048'])

        # Check again just in case it didn't work for some reason
        if os.path.exists(key_file):
            os.chmod(key_file, 0o400)

    if not os.path.exists(cert_file):
        # Generate a cert signing request
        subprocess.call([
            'openssl', 'req',
            '-config', os.path.join(ca_dir, 'openssl.cnf'),
            '-key', key_file,
            '-new', '-sha256',
            '-out', csr_file,
            '-subj', '{}/CN={}'.format(ca_subject, __grains__['fqdn'])
        ], env={'DNS_NAME': __grains__['fqdn']})

        # Sign the certificate
        subprocess.call([
            'openssl', 'ca',
            '-config', os.path.join(ca_dir, 'openssl.cnf'),
            '-extensions', 'stackdio',
            '-days', '1825',
            '-notext', '-batch',
            '-md', 'sha256',
            '-key', ca_key_password,
            '-in', csr_file,
            '-out', cert_file
        ], env={'DNS_NAME': __grains__['fqdn']})

        if os.path.exists(cert_file):
            os.chmod(cert_file, 0o444)

    try:
        # Add the priv key to the pillar
        with open(key_file, 'r') as f:
            ssl_opts['private_key'] = f.read()

        # Add all the certs to the pillar
        with open(cert_file, 'r') as f:
            ssl_opts['certificate'] = f.read()

        with open(ca_cert_chain_file, 'r') as f:
            # We need to put the newly generated cert on the front
            ssl_opts['chained_certificate'] = ssl_opts['certificate'] + f.read()

        with open(root_ca_cert_file, 'r') as f:
            ssl_opts['ca_certificate'] = f.read()

    except IOError:
        logger.warning('Certificate generation didn\'t work for some reason.  '
                       'Look at the logs above.')

    new_pillar['ssl'] = ssl_opts

    return new_pillar
