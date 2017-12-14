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
Generates an SSL certificate / private key pair for each minion
"""

from __future__ import absolute_import, unicode_literals

import io
import logging
import os
import subprocess

# Set up logging
logger = logging.getLogger(__name__)


def __virtual__():
    return True


def ext_pillar(minion_id, pillar, *args, **kwargs):
    # Generate an SSL cert for the host
    ca_dir = kwargs.get('ca_dir')
    ca_subject = kwargs.get('ca_subject')
    ca_key_password = kwargs.get('ca_key_password')

    if not ca_dir:
        logger.info('The ssl external pillar is loaded, but no ca_dir is defined.')
        return {}

    key_file = os.path.join(ca_dir, 'private', __grains__['fqdn'] + '.key')
    csr_file = os.path.join(ca_dir, 'csr', __grains__['fqdn'] + '.csr')
    cert_file = os.path.join(ca_dir, 'certs', __grains__['fqdn'] + '.crt')
    ca_cert_chain_file = os.path.join(ca_dir, 'certs', 'chain.crt')
    intermediate_ca_cert_file = os.path.join(ca_dir, 'certs', 'intermediate.crt')
    root_ca_cert_file = os.path.join(ca_dir, 'certs', 'root.crt')

    # Generate the private key
    if not os.path.exists(key_file):
        subprocess.call(['openssl', 'genrsa', '-out', key_file, '2048'])

        # Check again just in case it didn't work for some reason
        if os.path.exists(key_file):
            os.chmod(key_file, 0o400)

    # Generate the certificate
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
        command = [
            'openssl', 'ca',
            '-config', os.path.join(ca_dir, 'openssl.cnf'),
            '-extensions', 'stackdio',
            '-days', '1825',
            '-notext', '-batch',
            '-md', 'sha256',
            '-in', csr_file,
            '-out', cert_file
        ]

        # Add the key password if there is one
        if ca_key_password:
            command += ['-key', ca_key_password]

        subprocess.call(command, env={'DNS_NAME': __grains__['fqdn']})

        if os.path.exists(cert_file):
            os.chmod(cert_file, 0o444)

    # Give everything a default
    ssl_opts = {
        'private_key': None,
        'certificate': None,
        'chained_certificate': None,
        'intermediate_ca_certificate': None,
        'ca_certificate': None,
    }

    try:
        # Add the priv key to the pillar
        with io.open(key_file, 'r') as f:
            ssl_opts['private_key'] = f.read()

        # Add all the certs to the pillar
        with io.open(cert_file, 'r') as f:
            ssl_opts['certificate'] = f.read()

        with io.open(ca_cert_chain_file, 'r') as f:
            # We need to put the newly generated cert on the front
            ssl_opts['chained_certificate'] = ssl_opts['certificate'] + f.read()

        with io.open(intermediate_ca_cert_file, 'r') as f:
            ssl_opts['intermediate_ca_certificate'] = f.read()

        with io.open(root_ca_cert_file, 'r') as f:
            ssl_opts['ca_certificate'] = f.read()

    except IOError:
        logger.warning('Certificate generation didn\'t work for some reason.  '
                       'Look at the logs above.')
        return {}

    return {'ssl': ssl_opts}
