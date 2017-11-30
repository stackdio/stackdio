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

from __future__ import absolute_import, print_function

import copy
import errno
import hashlib
import logging
import os
import time
from shutil import rmtree

import git
import salt.config
import salt.fileserver
import salt.payload
import salt.utils
import salt.utils.event
import six
from salt.fileserver import wait_lock, _lock_cache
from salt.exceptions import GitLockError
from salt.utils.event import tagify
from salt.utils.gitfs import (
    GitFS,
    GitPython,
    PER_REMOTE_ONLY,
    AUTH_PARAMS,
    AUTH_PROVIDERS,
    failhard as gitfs_failhard,
)
from salt.utils.process import os_is_running as pid_exists


PER_REMOTE_OVERRIDES = ('base', 'mountpoint', 'root', 'ssl_verify', 'privkey')

_INVALID_REPO = (
    'Cache path {0} (corresponding remote: {1}) exists but is not a valid '
    'git repository. You will need to manually delete this directory on the '
    'master to continue to use this {2} remote.'
)

logger = logging.getLogger(__name__)


def recursive_encode(d):
    if isinstance(d, dict):
        retu = {}
        for k, v in d.items():
            retu[recursive_encode(k)] = recursive_encode(v)
        return retu
    elif isinstance(d, (list, set)):
        retu = []
        for i in d:
            retu.append(recursive_encode(i))
        return retu
    elif isinstance(d, bytes):
        return six.text_type(d, 'utf-8')
    else:
        return d


def check_file_list_cache(opts, form, list_cache, w_lock):
    """
    COPIED FROM SALT
    changed: Read unicode strings from the file instead of binary strings
    """
    refresh_cache = False
    save_cache = True
    serial = salt.payload.Serial(opts)
    wait_lock(w_lock, list_cache, 5 * 60)
    if not os.path.isfile(list_cache) and _lock_cache(w_lock):
        refresh_cache = True
    else:
        attempt = 0
        while attempt < 11:
            try:
                if os.path.exists(w_lock):
                    # wait for a filelist lock for max 15min
                    wait_lock(w_lock, list_cache, 15 * 60)
                if os.path.exists(list_cache):
                    # calculate filelist age is possible
                    cache_stat = os.stat(list_cache)
                    age = time.time() - cache_stat.st_mtime
                else:
                    # if filelist does not exists yet, mark it as expired
                    age = opts.get('fileserver_list_cache_time', 30) + 1
                if age < opts.get('fileserver_list_cache_time', 30):
                    # Young enough! Load this sucker up!
                    with salt.utils.fopen(list_cache, 'rb') as fp_:
                        logger.trace('Returning file_lists cache data from '
                                     '{0}'.format(list_cache))

                        return recursive_encode(serial.load(fp_)).get(form, []), False, False
                elif _lock_cache(w_lock):
                    # Set the w_lock and go
                    refresh_cache = True
                    break
            except Exception:
                time.sleep(0.2)
                attempt += 1
                continue
        if attempt > 10:
            save_cache = False
            refresh_cache = True
    return None, refresh_cache, save_cache


class StackdioGitPython(GitPython):

    # pylint: disable=super-init-not-called
    def __init__(self, opts, remote, per_remote_defaults,
                 override_params, cache_root, role='gitfs'):
        """
        COPIED FROM SALT
        changed: self.id needs to be a unicode string - but a hash is created from it,
        and the hash needs a bytes object
        """
        self.provider = 'stackdiogitpython'
        self.cache_root = cache_root
        self.opts = opts
        self.role = role
        self.env_blacklist = self.opts.get(
            '{0}_env_blacklist'.format(self.role), [])
        self.env_whitelist = self.opts.get(
            '{0}_env_whitelist'.format(self.role), [])
        repo_conf = copy.deepcopy(per_remote_defaults)

        per_remote_collisions = [x for x in override_params
                                 if x in PER_REMOTE_ONLY]
        if per_remote_collisions:
            logger.critical(
                'The following parameter names are restricted to per-remote '
                'use only: {0}. This is a bug, please report it.'.format(
                    ', '.join(per_remote_collisions)
                )
            )

        try:
            valid_per_remote_params = override_params + PER_REMOTE_ONLY
        except TypeError:
            valid_per_remote_params = \
                list(override_params) + list(PER_REMOTE_ONLY)

        if isinstance(remote, dict):
            self.id = next(iter(remote))
            self.get_url()
            per_remote_conf = dict(
                [(key, six.text_type(val)) for key, val in
                 six.iteritems(salt.utils.repack_dictlist(remote[self.id]))]
            )
            if not per_remote_conf:
                logger.critical(
                    'Invalid per-remote configuration for {0} remote \'{1}\'. '
                    'If no per-remote parameters are being specified, there '
                    'may be a trailing colon after the URL, which should be '
                    'removed. Check the master configuration file.'.format(self.role, self.id)
                )
                gitfs_failhard(self.role)

            # Separate the per-remote-only (non-global) parameters
            per_remote_only = {}
            for param in PER_REMOTE_ONLY:
                if param in per_remote_conf:
                    per_remote_only[param] = per_remote_conf.pop(param)

            per_remote_errors = False
            for param in (x for x in per_remote_conf
                          if x not in valid_per_remote_params):
                if param in AUTH_PARAMS \
                        and self.provider not in AUTH_PROVIDERS:
                    msg = (
                        '{0} authentication parameter \'{1}\' (from remote '
                        '\'{2}\') is only supported by the following '
                        'provider(s): {3}. Current {0}_provider is \'{4}\'.'.format(
                            self.role,
                            param,
                            self.id,
                            ', '.join(AUTH_PROVIDERS),
                            self.provider
                        )
                    )
                    if self.role == 'gitfs':
                        msg += (
                            'See the GitFS Walkthrough in the Salt '
                            'documentation for further information.'
                        )
                    logger.critical(msg)
                else:
                    msg = (
                        'Invalid {0} configuration parameter \'{1}\' in '
                        'remote {2}. Valid parameters are: {3}.'.format(
                            self.role,
                            param,
                            self.url,
                            ', '.join(valid_per_remote_params)
                        )
                    )
                    if self.role == 'gitfs':
                        msg += (
                            ' See the GitFS Walkthrough in the Salt '
                            'documentation for further information.'
                        )
                    logger.critical(msg)

                per_remote_errors = True
            if per_remote_errors:
                gitfs_failhard(self.role)

            repo_conf.update(per_remote_conf)
            repo_conf.update(per_remote_only)
        else:
            self.id = remote
            self.get_url()

        # Winrepo doesn't support the 'root' option, but it still must be part
        # of the GitProvider object because other code depends on it. Add it as
        # an empty string.
        if 'root' not in repo_conf:
            repo_conf['root'] = ''

        if self.role == 'winrepo' and 'name' not in repo_conf:
            # Ensure that winrepo has the 'name' parameter set if it wasn't
            # provided. Default to the last part of the URL, minus the .git if
            # it is present.
            repo_conf['name'] = self.url.rsplit('/', 1)[-1]
            # Remove trailing .git from name
            if repo_conf['name'].lower().endswith('.git'):
                repo_conf['name'] = repo_conf['name'][:-4]

        # Set all repo config params as attributes
        for key, val in six.iteritems(repo_conf):
            setattr(self, key, val)

        if hasattr(self, 'mountpoint'):
            self.mountpoint = salt.utils.url.strip_proto(self.mountpoint)
        else:
            # For providers which do not use a mountpoint, assume the
            # filesystem is mounted at the root of the fileserver.
            self.mountpoint = ''

        if not isinstance(self.url, six.string_types):
            logger.critical(
                'Invalid {0} remote \'{1}\'. Remotes must be strings, you '
                'may need to enclose the URL in quotes'.format(
                    self.role,
                    self.id
                )
            )
            gitfs_failhard(self.role)

        hash_type = getattr(hashlib, self.opts.get('hash_type', 'md5'))
        self.hash = hash_type(self.id.encode('utf-8')).hexdigest()
        self.cachedir_basename = getattr(self, 'name', self.hash)
        self.cachedir = salt.utils.path_join(cache_root, self.cachedir_basename)
        if not os.path.isdir(self.cachedir):
            os.makedirs(self.cachedir)

        try:
            self.new = self.init_remote()
        except Exception as exc:
            msg = ('Exception caught while initializing {0} remote \'{1}\': '
                   '{2}'.format(self.role, self.id, exc))
            if isinstance(self, GitPython):
                msg += ' Perhaps git is not available.'
            logger.critical(msg, exc_info_on_loglevel=logging.DEBUG)
            gitfs_failhard(self.role)

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

    def _lock(self, lock_type='update', failhard=False):
        """
        COPIED FROM SALT
        changed: Fixed unicode errors (convert pid to bytes)
        """
        try:
            fh_ = os.open(self._get_lock_file(lock_type),
                          os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fh_, 'w'):
                # Write the lock file and close the filehandle
                os.write(fh_, six.binary_type(os.getpid()))
        except (OSError, IOError) as exc:
            if exc.errno == errno.EEXIST:
                with salt.utils.fopen(self._get_lock_file(lock_type), 'r') as fd_:
                    try:
                        pid = int(fd_.readline().rstrip())
                    except ValueError:
                        # Lock file is empty, set pid to 0 so it evaluates as
                        # False.
                        pid = 0
                global_lock_key = self.role + '_global_lock'
                lock_file = self._get_lock_file(lock_type=lock_type)
                if self.opts[global_lock_key]:
                    msg = (
                        '{0} is enabled and {1} lockfile {2} is present for '
                        '{3} remote \'{4}\'.'.format(
                            global_lock_key,
                            lock_type,
                            lock_file,
                            self.role,
                            self.id,
                        )
                    )
                    if pid:
                        msg += ' Process {0} obtained the lock'.format(pid)
                        if not pid_exists(pid):
                            msg += (' but this process is not running. The '
                                    'update may have been interrupted. If '
                                    'using multi-master with shared gitfs '
                                    'cache, the lock may have been obtained '
                                    'by another master.')
                    logger.warning(msg)
                    if failhard:
                        raise exc
                    return
                elif pid and pid_exists(pid):
                    logger.warning('Process %d has a %s %s lock (%s)',
                                   pid, self.role, lock_type, lock_file)
                    if failhard:
                        raise
                    return
                else:
                    if pid:
                        logger.warning(
                            'Process %d has a %s %s lock (%s), but this '
                            'process is not running. Cleaning up lock file.',
                            pid, self.role, lock_type, lock_file
                        )
                    success, _ = self.clear_lock()
                    if success:
                        return self._lock(lock_type='update',
                                          failhard=failhard)
                    elif failhard:
                        raise
                    return
            else:
                msg = 'Unable to set {0} lock for {1} ({2}): {3} '.format(
                    lock_type,
                    self.id,
                    self._get_lock_file(lock_type),
                    exc
                )
                logger.error(msg, exc_info_on_loglevel=logging.DEBUG)
                raise GitLockError(exc.errno, msg)
        msg = 'Set {0} lock for {1} remote \'{2}\''.format(
            lock_type,
            self.role,
            self.id
        )
        logger.debug(msg)
        return msg

    def write_file(self, blob, dest):
        """
        COPIED FROM SALT
        changed: Open the file as binary
        """
        with salt.utils.fopen(dest, 'wb+') as fp_:
            blob.stream_data(fp_)


class StackdioGitFS(GitFS):

    def envs(self, ignore_cache=False):
        """
        COPIED FROM SALT
        changed: Make sure envs() returns unicode strings instead of bytes
        """
        envs = super(StackdioGitFS, self).envs(ignore_cache)
        ret = []
        for env in envs:
            if isinstance(env, bytes):
                ret.append(six.text_type(env, 'utf-8'))
            else:
                ret.append(env)
        return ret

    def get_provider(self):
        """
        Always use the StackdioGitPython provider
        """
        self.provider = 'stackdiogitpython'
        self.provider_class = StackdioGitPython

    def _file_lists(self, load, form):
        """
        COPIED FROM SALT
        changed: use our custom check_file_list_cache method that reads unicode strings
        """
        if 'env' in load:
            salt.utils.warn_until(
                'Carbon',
                'Passing a salt environment should be done using \'saltenv\' '
                'not \'env\'. This functionality will be removed in Salt Carbon.'
            )
            load['saltenv'] = load.pop('env')

        if not os.path.isdir(self.file_list_cachedir):
            try:
                os.makedirs(self.file_list_cachedir)
            except os.error:
                logger.error(
                    'Unable to make cachedir {0}'.format(
                        self.file_list_cachedir
                    )
                )
                return []
        list_cache = salt.utils.path_join(
            self.file_list_cachedir,
            '{0}.p'.format(load['saltenv'].replace(os.path.sep, '_|-'))
        )
        w_lock = salt.utils.path_join(
            self.file_list_cachedir,
            '.{0}.w'.format(load['saltenv'].replace(os.path.sep, '_|-'))
        )
        cache_match, refresh_cache, save_cache = \
            check_file_list_cache(
                self.opts, form, list_cache, w_lock
            )
        if cache_match is not None:
            return cache_match
        if refresh_cache:
            ret = {'files': set(), 'symlinks': {}, 'dirs': set()}
            if salt.utils.is_hex(load['saltenv']) \
                    or load['saltenv'] in self.envs():
                for repo in self.remotes:
                    repo_files, repo_symlinks = repo.file_list(load['saltenv'])
                    ret['files'].update(repo_files)
                    ret['symlinks'].update(repo_symlinks)
                    ret['dirs'].update(repo.dir_list(load['saltenv']))
            ret['files'] = sorted(ret['files'])
            ret['dirs'] = sorted(ret['dirs'])

            if save_cache:
                salt.fileserver.write_file_list_cache(
                    self.opts, ret, list_cache, w_lock
                )
            # NOTE: symlinks are organized in a dict instead of a list, however
            # the 'symlinks' key will be defined above so it will never get to
            # the default value in the call to ret.get() below.
            return ret.get(form, [])
        # Shouldn't get here, but if we do, this prevents a TypeError
        return {} if form == 'symlinks' else []

    def update(self):
        """
        COPIED FROM SALT
        changed: salt.utils.fopen() call opens the file in binary mode instead.
        """
        # data for the fileserver event
        data = {
            'changed': self.clear_old_remotes(),
            'backend': 'gitfs'
        }

        if self.fetch_remotes():
            data['changed'] = True

        if data['changed'] is True or not os.path.isfile(self.env_cache):
            env_cachedir = os.path.dirname(self.env_cache)
            if not os.path.exists(env_cachedir):
                os.makedirs(env_cachedir)
            new_envs = self.envs(ignore_cache=True)
            serial = salt.payload.Serial(self.opts)
            with salt.utils.fopen(self.env_cache, 'wb+') as fp_:
                fp_.write(serial.dumps(new_envs))
                logger.trace('Wrote env cache data to {0}'.format(self.env_cache))

        # if there is a change, fire an event
        if self.opts.get('fileserver_events', False):
            event = salt.utils.event.get_event(
                'master',
                self.opts['sock_dir'],
                self.opts['transport'],
                opts=self.opts,
                listen=False,
            )
            event.fire_event(
                data,
                tagify(['gitfs', 'update'], prefix='fileserver')
            )

        try:
            salt.fileserver.reap_fileserver_cache_dir(
                self.hash_cachedir,
                self.find_file
            )
        except (OSError, IOError):
            # Hash file won't exist if no files have yet been served up
            pass

    # Make it work as a contextmanager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.opts.get('cleanup_cachedir', False):
            if os.path.isdir(self.opts['cachedir']):
                logger.debug('Cleaning up gitfs cachedir: {}'.format(self.opts['cachedir']))
                rmtree(self.opts['cachedir'])
        return False
