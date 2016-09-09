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


"""
Custom fileserver backend for stackd.io that allows looks for states
from cloned formulas using the user directory as an environment. This
allows individual users to clone the same formulas or formulas with
common paths (eg., cdh4.hadoop.namenode) without stepping on other
users.

NOTE: Most of this was taken from salt's fileserver.roots module and
adapted to work in the manner described above.
"""

# Import python libs
import logging
import os

if '__opts__' not in globals():
    __opts__ = {}

try:
    import fcntl
    HAS_FCNTL = os.uname()[0] != "SunOS"
except ImportError:
    # fcntl is not available on windows
    HAS_FCNTL = False

# Import salt libs
from salt.utils.event import tagify  # NOQA
import salt.fileserver  # NOQA
import salt.utils  # NOQA

log = logging.getLogger(__name__)


def __virtual__():
    storage_dir = _get_storage_dir()

    if storage_dir is None:
        log.error('stackdio fileserver is enabled in fileserver_backend '
                  'configuration, but root_dir location is missing in the '
                  'stackdio configuration.')
        return False

    if not os.path.isdir(storage_dir):
        log.error('stackdio::root_dir location is not a directory: {0}'.format(storage_dir))
        return False

    return 'stackdio'


def _get_storage_dir():
    salt_root_dir = __opts__.get('root_dir')

    if salt_root_dir is None:
        log.warn('stackdio fileserver root_dir configuration does not exist.')
        return salt_root_dir

    # The storage dir is the parent of the salt root dir.
    return os.path.dirname(os.path.abspath(salt_root_dir))


def _get_env_dir(saltenv):
    """
    Grab the actual path where formulas live for a salt env
    :param saltenv: the salt env
    :return: the filesystem path corresponding to the salt env
    """
    env_type, dot, name = saltenv.partition('.')
    root_dir = os.path.join(_get_storage_dir(), env_type, name)

    if not os.path.isdir(root_dir):
        log.warn('The env dir doesn\'t exist... Something has gone horribly wrong.')

    formula_dir = os.path.join(root_dir, 'formulas')

    if not os.path.exists(formula_dir):
        os.mkdir(formula_dir, 0755)

    return formula_dir


def envs():
    storage_dir = _get_storage_dir()

    ret = []

    cloud_dir = os.path.join(storage_dir, 'cloud')
    stacks_dir = os.path.join(storage_dir, 'stacks')

    for account in os.listdir(cloud_dir):
        account_dir = os.path.join(cloud_dir, account)
        if not os.path.isdir(account_dir):
            continue
        ret.append('cloud.{0}'.format(account))

    for stack in os.listdir(stacks_dir):
        stack_dir = os.path.join(stacks_dir, stack)
        if not os.path.isdir(stack_dir):
            continue
        ret.append('stacks.{0}'.format(stack))

    return ret


def find_file(path, saltenv='base', env=None, **kwargs):
    """
    Search the environment for the relative path
    """
    if env is not None:
        salt.utils.warn_until(
            'Boron',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Boron.'
        )
        # Backwards compatibility
        saltenv = env

    fnd = {'path': '',
           'rel': ''}
    if os.path.isabs(path):
        return fnd
    if saltenv not in envs():
        return fnd

    root = _get_env_dir(saltenv)
    for formula_root in os.listdir(root):
        formula_dir = os.path.join(root, formula_root)
        if not os.path.isdir(formula_dir):
            continue
        full = os.path.join(formula_dir, path)
        if os.path.isfile(full) and not salt.fileserver.is_file_ignored(__opts__, full):
            fnd['path'] = full
            fnd['rel'] = path
            return fnd
    return fnd


def serve_file(load, fnd):
    """
    Return a chunk from a file based on the data received
    """
    if 'env' in load:
        salt.utils.warn_until(
            'Boron',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Boron.'
        )
        load['saltenv'] = load.pop('env')

    ret = {'data': '',
           'dest': ''}
    if 'path' not in load or 'loc' not in load or 'saltenv' not in load:
        return ret
    if not fnd['path']:
        return ret
    ret['dest'] = fnd['rel']
    gzip = load.get('gzip', None)

    with salt.utils.fopen(fnd['path'], 'rb') as fp_:
        fp_.seek(load['loc'])
        data = fp_.read(__opts__['file_buffer_size'])
        if gzip and data:
            data = salt.utils.gzip_util.compress(data, gzip)
            ret['gzip'] = gzip
        ret['data'] = data
    return ret


def update():
    """
    When we are asked to update (regular interval) lets reap the cache
    """
    try:
        salt.fileserver.reap_fileserver_cache_dir(
            os.path.join(__opts__['cachedir'], 'stackdio/hash'),
            find_file
        )
    except (IOError, OSError):
        # Hash file won't exist if no files have yet been served up
        pass

    mtime_map_path = os.path.join(__opts__['cachedir'], 'stackdio/mtime_map')
    # data to send on event
    data = {'changed': False,
            'backend': 'stackdio'}

    old_mtime_map = {}
    # if you have an old map, load that
    if os.path.exists(mtime_map_path):
        with salt.utils.fopen(mtime_map_path, 'rb') as fp_:
            for line in fp_:
                file_path, mtime = line.split(':', 1)
                old_mtime_map[file_path] = mtime

    # generate the new map
    saltenvs = envs()
    path_map = {}
    for saltenv in saltenvs:
        path_map[saltenv] = [_get_env_dir(saltenv)]
    new_mtime_map = salt.fileserver.generate_mtime_map(path_map)

    # compare the maps, set changed to the return value
    data['changed'] = salt.fileserver.diff_mtime_map(old_mtime_map, new_mtime_map)

    # write out the new map
    mtime_map_path_dir = os.path.dirname(mtime_map_path)
    if not os.path.exists(mtime_map_path_dir):
        os.makedirs(mtime_map_path_dir)
    with salt.utils.fopen(mtime_map_path, 'w') as fp_:
        for file_path, mtime in new_mtime_map.items():
            fp_.write('{file_path}:{mtime}\n'.format(file_path=file_path, mtime=mtime))

    if __opts__.get('fileserver_events', False):
        # if there is a change, fire an event
        event = salt.utils.event.MasterEvent(__opts__['sock_dir'])
        event.fire_event(
            data,
            tagify(['stackdio', 'update'], prefix='fileserver')
        )


# Ignoring code complexity issues
def file_hash(load, fnd):  # NOQA
    """
    Return a file hash, the hash type is set in the master config file
    """
    if 'env' in load:
        salt.utils.warn_until(
            'Boron',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Boron.'
        )
        load['saltenv'] = load.pop('env')

    if 'path' not in load or 'saltenv' not in load:
        return ''
    path = fnd['path']
    ret = {}

    # if the file doesn't exist, we can't get a hash
    if not path or not os.path.isfile(path):
        log.warn('Path does not exist or is not a file: {0}'.format(path))
        return ret

    # set the hash_type as it is determined by config-- so mechanism won't
    # change that
    ret['hash_type'] = __opts__['hash_type']

    # check if the hash is cached
    # cache file's contents should be "hash:mtime"
    cache_path = os.path.join(
        __opts__['cachedir'],
        'stackdio/hash',
        load['saltenv'],
        '{0}.hash.{1}'.format(
            fnd['rel'],
            __opts__['hash_type']
        )
    )

    # if we have a cache, serve that if the mtime hasn't changed
    if os.path.exists(cache_path):
        try:
            with salt.utils.fopen(cache_path, 'rb') as fp_:
                try:
                    hsum, mtime = fp_.read().split(':')
                except ValueError:
                    log.debug('Fileserver attempted to read incomplete cache '
                              'file. Retrying.')
                    # Delete the file since its incomplete (either corrupted
                    # or incomplete)
                    try:
                        os.unlink(cache_path)
                    except OSError:
                        pass
                    return file_hash(load, fnd)
                if os.path.getmtime(path) == mtime:
                    # check if mtime changed
                    ret['hsum'] = hsum
                    return ret
        # Can't use Python select() because we need Windows support
        except (os.error, IOError):
            log.debug('Fileserver encountered lock when reading cache file. '
                      'Retrying.')

            # Delete the file since its incomplete (either corrupted or
            # incomplete)
            try:
                os.unlink(cache_path)
            except OSError:
                pass
            return file_hash(load, fnd)

    # if we don't have a cache entry-- lets make one
    ret['hsum'] = salt.utils.get_hash(path, __opts__['hash_type'])
    cache_dir = os.path.dirname(cache_path)
    # make cache directory if it doesn't exist
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    # save the cache object "hash:mtime"
    if HAS_FCNTL:
        with salt.utils.flopen(cache_path, 'w') as fp_:
            fp_.write('{0}:{1}'.format(ret['hsum'], os.path.getmtime(path)))
            fcntl.flock(fp_.fileno(), fcntl.LOCK_UN)
        return ret
    else:
        with salt.utils.fopen(cache_path, 'w') as fp_:
            fp_.write('{0}:{1}'.format(ret['hsum'], os.path.getmtime(path)))
        return ret


# Ignoring code complexity issues
def _file_lists(load, form):  # NOQA
    """
    Return a dict containing the file lists for files, dirs, emtydirs and
    symlinks
    """
    if 'env' in load:
        salt.utils.warn_until(
            'Boron',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Boron.'
        )
        load['saltenv'] = load.pop('env')
    if load['saltenv'] not in envs():
        return []

    env_dir = _get_env_dir(load['saltenv'])

    if not os.path.isdir(env_dir):
        log.error('Environment directory does not exist: {0}'.format(env_dir))
        return []

    list_cachedir = os.path.join(__opts__['cachedir'], 'file_lists/stackdio')
    if not os.path.isdir(list_cachedir):
        try:
            os.makedirs(list_cachedir)
        except os.error:
            log.critical('Unable to make cachedir {0}'.format(list_cachedir))
            return []
    list_cache = os.path.join(list_cachedir, '{0}.p'.format(load['saltenv']))
    w_lock = os.path.join(list_cachedir, '.{0}.w'.format(load['saltenv']))
    cache_match, refresh_cache, save_cache = \
        salt.fileserver.check_file_list_cache(
            __opts__, form, list_cache, w_lock
        )
    if cache_match is not None:
        return cache_match
    if refresh_cache:
        ret = {
            'files': [],
            'dirs': [],
            'empty_dirs': [],
            'links': []
        }

        for formula_root in os.listdir(env_dir):
            formula_dir = os.path.join(env_dir, formula_root)
            if not os.path.isdir(formula_dir):
                continue

            # walk each formula and pull the relative file paths
            for root, dirs, files in os.walk(
                    formula_dir,
                    followlinks=__opts__['fileserver_followsymlinks']):

                dir_rel_fn = os.path.relpath(root, formula_dir)
                ret['dirs'].append(dir_rel_fn)
                if len(dirs) == 0 and len(files) == 0:
                    if not salt.fileserver.is_file_ignored(__opts__,
                                                           dir_rel_fn):
                        ret['empty_dirs'].append(dir_rel_fn)
                for fname in files:
                    is_link = os.path.islink(os.path.join(root, fname))
                    if is_link:
                        ret['links'].append(fname)
                    if __opts__['fileserver_ignoresymlinks'] and is_link:
                        continue
                    rel_fn = os.path.relpath(
                        os.path.join(root, fname),
                        formula_dir
                    )
                    if not salt.fileserver.is_file_ignored(__opts__, rel_fn):
                        ret['files'].append(rel_fn)
        if save_cache:
            salt.fileserver.write_file_list_cache(
                __opts__, ret, list_cache, w_lock
            )
        return ret.get(form, [])
    # Shouldn't get here, but if we do, this prevents a TypeError
    return []


def file_list(load):  # NOQA
    """
    Return a list of all files on the file server in a specified
    environment
    """
    return _file_lists(load, 'files')


def file_list_emptydirs(load):
    """
    Return a list of all empty directories on the master
    """
    return _file_lists(load, 'empty_dirs')


def dir_list(load):
    """
    Return a list of all directories on the master
    """
    return _file_lists(load, 'dirs')


# Ignoring code complexity issues
def symlink_list(load):  # NOQA
    """
    Return a dict of all symlinks based on a given path on the Master
    """
    if 'env' in load:
        salt.utils.warn_until(
            'Boron',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Boron.'
        )
        load['saltenv'] = load.pop('env')

    ret = {}
    if load['saltenv'] not in envs():
        return ret

    env_root = _get_env_dir(load['saltenv'])
    for formula_root in os.listdir(env_root):
        formula_dir = os.path.join(env_root, formula_root)
        if not os.path.isdir(formula_dir):
            continue

        # Adopting rsync functionality here and stopping at any encounter of
        # a symlink
        for root, dirs, files in os.walk(formula_dir, followlinks=False):
            for fname in files:
                if not os.path.islink(os.path.join(root, fname)):
                    continue
                rel_fn = os.path.relpath(os.path.join(root, fname),
                                         formula_dir)
                if not salt.fileserver.is_file_ignored(__opts__, rel_fn):
                    ret[rel_fn] = os.readlink(os.path.join(root, fname))
            for dname in dirs:
                if os.path.islink(os.path.join(root, dname)):
                    relpath = os.path.relpath(os.path.join(root, dname),
                                              formula_root)
                    ret[relpath] = os.readlink(os.path.join(root, dname))
    return ret
