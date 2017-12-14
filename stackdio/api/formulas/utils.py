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

# Disable these pylint things since we just copied a bunch of code from salt
# pylint: disable=super-init-not-called,redefined-outer-name

from __future__ import unicode_literals

import io
import os
import uuid

import salt.config
import salt.fileserver
import salt.payload
import salt.utils
import salt.utils.event
import six
from django.conf import settings

from stackdio.salt.utils.gitfs import StackdioGitFS, PER_REMOTE_OVERRIDES


def get_gitfs(uri, ssh_private_key, formula=None):
    """
    Given a uri and optionally a private key, return a GitFS object that can be used to
    inspect formulas
    :return: GitFS
    """
    opts = salt.config.client_config(settings.STACKDIO_CONFIG.salt_master_config)

    base_cachedir = os.path.join(opts['cachedir'], 'stackdio', 'formulas')

    if formula is None:
        root_dir = os.path.join(base_cachedir, six.text_type(uuid.uuid4()))
        new_cachedir = root_dir
        opts['cleanup_cachedir'] = True
    else:
        root_dir = formula.get_root_dir()
        new_cachedir = os.path.join(base_cachedir, six.text_type(formula.id))

    # Always write out the private / public keys
    if ssh_private_key:
        # Write out the key file
        ssh_private_key_file = os.path.join(root_dir, 'id_rsa')
        with io.open(ssh_private_key_file, 'wt') as f:
            f.write(ssh_private_key)

        os.chmod(ssh_private_key_file, 0o600)

        # The config now looks different
        gitfs_remotes = [{
            uri: [
                {'privkey': ssh_private_key_file},
            ]
        }]
    else:
        gitfs_remotes = [uri]

    opts['gitfs_remotes'] = gitfs_remotes
    if not os.path.isdir(new_cachedir):
        os.makedirs(new_cachedir)
    opts['cachedir'] = new_cachedir
    gitfs = StackdioGitFS(opts)
    gitfs.init_remotes(gitfs_remotes, PER_REMOTE_OVERRIDES)

    return gitfs
