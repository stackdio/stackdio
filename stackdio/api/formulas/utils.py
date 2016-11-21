# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

from __future__ import unicode_literals

import logging
import os
import uuid
from shutil import rmtree

import git
import salt.config
import salt.utils
import six
from django.conf import settings
from salt.utils.gitfs import GitFS, GitPython

PER_REMOTE_OVERRIDES = ('base', 'mountpoint', 'root', 'ssl_verify', 'privkey')

_INVALID_REPO = (
    'Cache path {0} (corresponding remote: {1}) exists but is not a valid '
    'git repository. You will need to manually delete this directory on the '
    'master to continue to use this {2} remote.'
)


logger = logging.getLogger(__name__)


class StackdioGitPython(GitPython):

    def __init__(self, opts, remote, per_remote_defaults,
                 override_params, cache_root, role='gitfs'):
        self.provider = 'stackdiogitpython'
        self.cache_root = cache_root
        GitPython.__init__(self, opts, remote, per_remote_defaults,
                           override_params, cache_root, role)

    def _get_remote_env(self):
        remote_env = {}

        private_key_file = getattr(self, 'privkey', None)

        if private_key_file:
            git_wrapper = salt.utils.path_join(self.cache_root, '{}.sh'.format(self.hash))
            with open(git_wrapper, 'w') as f:
                f.write(b'#!/bin/bash\n')
                f.write(b'SSH=$(which ssh)\n')
                f.write(b'exec $SSH -o StrictHostKeyChecking=no -i {} "$@"\n'.format(
                    private_key_file
                ))

            # Make the git wrapper executable
            os.chmod(git_wrapper, 0o755)

            remote_env['GIT_SSH'] = git_wrapper

        return remote_env

    def init_remote(self):
        """
        Same as GitPython:init_remote(), we just do the call to update_environment after
        creating the repo.
        """
        new = False
        if not os.listdir(self.cachedir):
            # Repo cachedir is empty, initialize a new repo there
            self.repo = git.Repo.init(self.cachedir)
            self.repo.git.update_environment(**self._get_remote_env())
            new = True
        else:
            # Repo cachedir exists, try to attach
            try:
                self.repo = git.Repo(self.cachedir)
                self.repo.git.update_environment(**self._get_remote_env())
            except git.exc.InvalidGitRepositoryError:
                logger.error(_INVALID_REPO.format(self.cachedir, self.url, self.role))
                return new

        self.gitdir = salt.utils.path_join(self.repo.working_dir, '.git')

        if not self.repo.remotes:
            try:
                self.repo.create_remote('origin', self.url)
                # Ensure tags are also fetched
                self.repo.git.config('--add',
                                     'remote.origin.fetch',
                                     '+refs/tags/*:refs/tags/*')
                self.repo.git.config('http.sslVerify', self.ssl_verify)
            except os.error:
                # This exception occurs when two processes are trying to write
                # to the git config at once, go ahead and pass over it since
                # this is the only write. This should place a lock down.
                pass
            else:
                new = True
        return new


class StackdioGitFS(GitFS):

    def get_provider(self):
        """
        Always use the StackdioGitPython provider
        """
        self.provider = 'stackdiogitpython'
        self.provider_class = StackdioGitPython

    # Make it work as a contextmanager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.opts.get('cleanup_cachedir', False):
            if os.path.isdir(self.opts['cachedir']):
                logger.debug('Cleaning up gitfs cachedir: {}'.format(self.opts['cachedir']))
                rmtree(self.opts['cachedir'])
        return False


def get_gitfs(uri, ssh_private_key, formula=None):
    """
    Given a uri and optionally a private key, return a GitFS object that can be used to
    inspect formulas
    :return: GitFS
    """
    opts = salt.config.client_config(settings.STACKDIO_CONFIG.salt_master_config)

    base_cachedir = os.path.join(opts['cachedir'], b'stackdio', b'formulas')

    if formula is None:
        root_dir = os.path.join(base_cachedir, six.binary_type(uuid.uuid4()))
        new_cachedir = root_dir
        opts['cleanup_cachedir'] = True
    else:
        root_dir = formula.get_root_dir()
        new_cachedir = os.path.join(base_cachedir, six.binary_type(formula.id))

    # Always write out the private / public keys
    if ssh_private_key:
        # Write out the key file
        ssh_private_key_file = os.path.join(root_dir, b'id_rsa')
        with open(ssh_private_key_file, 'w') as f:
            f.write(ssh_private_key)

        os.chmod(ssh_private_key_file, 0o600)

        # The config now looks different
        gitfs_remotes = [{
            six.binary_type(uri): [
                {'privkey': ssh_private_key_file},
            ]
        }]
    else:
        gitfs_remotes = [six.binary_type(uri)]

    opts['gitfs_remotes'] = gitfs_remotes
    if not os.path.isdir(new_cachedir):
        os.makedirs(new_cachedir)
    opts['cachedir'] = new_cachedir
    gitfs = StackdioGitFS(opts)
    gitfs.init_remotes(gitfs_remotes, PER_REMOTE_OVERRIDES)

    return gitfs
