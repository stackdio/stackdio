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

import logging
import os

import git
import salt.utils
from salt.utils.gitfs import GitFS, GitPython


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
                f.write('#!/bin/bash\n')
                f.write('SSH=$(which ssh)\n')
                f.write('exec $SSH -o StrictHostKeyChecking=no -i {} "$@"\n'.format(
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
