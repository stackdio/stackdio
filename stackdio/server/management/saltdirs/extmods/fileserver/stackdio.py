# -*- coding: utf-8 -*-
"""
The default file server backend

This fileserver backend serves files from the Master's local filesystem. If
:conf_master:`fileserver_backend` is not defined in the Master config file,
then this backend is enabled by default. If it *is* defined then ``roots`` must
be in the :conf_master:`fileserver_backend` list to enable this backend.

.. code-block:: yaml

    fileserver_backend:
      - roots

Fileserver environments are defined using the :conf_master:`file_roots`
configuration option.
"""
from __future__ import absolute_import

# Import python libs
import os
import errno
import logging

# Import salt libs
import salt.fileserver
import salt.utils
from salt.utils.event import tagify
import salt.ext.six as six

# import the functions that don't change from the default roots fileserver
from salt.fileserver.roots import (
    serve_file,
    file_list,
    file_list_emptydirs,
    dir_list,
)

log = logging.getLogger(__name__)


__virtualname__ = 'stackdio'


def __virtual__():
    if __virtualname__ not in __opts__['fileserver_backend']:
        return False

    storage_dir = _get_storage_dir()

    if storage_dir is None:
        log.error('stackdio fileserver is enabled in fileserver_backend '
                  'configuration, but root_dir location is missing in the '
                  'stackdio configuration.')
        return False

    if not os.path.isdir(storage_dir):
        log.error('stackdio::root_dir location is not a directory: {0}'.format(storage_dir))
        return False

    return __virtualname__


def _get_storage_dir():
    salt_root_dir = __opts__.get('root_dir')

    if salt_root_dir is None:
        log.warn('salt root_dir configuration does not exist.')
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
        os.mkdir(formula_dir, 0o755)

    return formula_dir


def _get_dir_list(saltenv):
    """
    Get a list of all search directories for the given saltenv
    :param saltenv: the salt env
    :return: A list of filesystem paths to search for files
    """
    env_dir = _get_env_dir(saltenv)

    formula_dirs = []
    for formula_root in os.listdir(env_dir):
        formula_env_dir = os.path.join(env_dir, formula_root)
        if os.path.isdir(formula_env_dir):
            formula_dirs.append(formula_env_dir)

    return formula_dirs


def find_file(path, saltenv='base', env=None, **kwargs):
    """
    Search the environment for the relative path
    """
    if env is not None:
        salt.utils.warn_until(
            'Carbon',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Carbon.'
        )
        # Backwards compatibility
        saltenv = env

    path = os.path.normpath(path)
    fnd = {'path': '',
           'rel': ''}
    if os.path.isabs(path):
        return fnd
    if saltenv not in envs():
        return fnd

    for root in _get_dir_list(saltenv):
        full = os.path.join(root, path)
        if os.path.isfile(full) and not salt.fileserver.is_file_ignored(__opts__, full):
            fnd['path'] = full
            fnd['rel'] = path
            fnd['stat'] = list(os.stat(full))
            return fnd
    return fnd


def envs():
    """
    Return the file server environments
    """
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
        with salt.utils.fopen(mtime_map_path, 'r') as fp_:
            for line in fp_:
                try:
                    file_path, mtime = line.split(':', 1)
                    old_mtime_map[file_path] = mtime
                except ValueError:
                    # Document the invalid entry in the log
                    log.warning('Skipped invalid cache mtime entry in {0}: {1}'
                                .format(mtime_map_path, line))

    # generate the new map
    path_map = dict((saltenv, _get_dir_list(saltenv)) for saltenv in envs())
    new_mtime_map = salt.fileserver.generate_mtime_map(path_map)

    # compare the maps, set changed to the return value
    data['changed'] = salt.fileserver.diff_mtime_map(old_mtime_map, new_mtime_map)

    # write out the new map
    mtime_map_path_dir = os.path.dirname(mtime_map_path)
    if not os.path.exists(mtime_map_path_dir):
        os.makedirs(mtime_map_path_dir)
    with salt.utils.fopen(mtime_map_path, 'w') as fp_:
        for file_path, mtime in six.iteritems(new_mtime_map):
            fp_.write('{file_path}:{mtime}\n'.format(file_path=file_path,
                                                     mtime=mtime))

    if __opts__.get('fileserver_events', False):
        # if there is a change, fire an event
        event = salt.utils.event.get_event(
                'master',
                __opts__['sock_dir'],
                __opts__['transport'],
                opts=__opts__,
                listen=False)
        event.fire_event(data, tagify(['stackdio', 'update'], prefix='fileserver'))


def file_hash(load, fnd):
    """
    Return a file hash, the hash type is set in the master config file
    """
    if 'env' in load:
        salt.utils.warn_until(
            'Carbon',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Carbon.'
        )
        load['saltenv'] = load.pop('env')

    if 'path' not in load or 'saltenv' not in load:
        return ''
    path = fnd['path']
    ret = {}

    # if the file doesn't exist, we can't get a hash
    if not path or not os.path.isfile(path):
        return ret

    # set the hash_type as it is determined by config-- so mechanism won't change that
    ret['hash_type'] = __opts__['hash_type']

    # check if the hash is cached
    # cache file's contents should be "hash:mtime"
    cache_path = os.path.join(__opts__['cachedir'],
                              'stackdio/hash',
                              load['saltenv'],
                              u'{0}.hash.{1}'.format(fnd['rel'],
                              __opts__['hash_type']))
    # if we have a cache, serve that if the mtime hasn't changed
    if os.path.exists(cache_path):
        try:
            with salt.utils.fopen(cache_path, 'r') as fp_:
                try:
                    hsum, mtime = fp_.read().split(':')
                except ValueError:
                    log.debug('Fileserver attempted to read incomplete cache file. Retrying.')
                    # Delete the file since its incomplete (either corrupted or incomplete)
                    try:
                        os.unlink(cache_path)
                    except OSError:
                        pass
                    return file_hash(load, fnd)
                if os.path.getmtime(path) == mtime:
                    # check if mtime changed
                    ret['hsum'] = hsum
                    return ret
        except (os.error, IOError):  # Can't use Python select() because we need Windows support
            log.debug("Fileserver encountered lock when reading cache file. Retrying.")
            # Delete the file since its incomplete (either corrupted or incomplete)
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
        try:
            os.makedirs(cache_dir)
        except OSError as err:
            if err.errno == errno.EEXIST:
                # rarely, the directory can be already concurrently created between
                # the os.path.exists and the os.makedirs lines above
                pass
            else:
                raise
    # save the cache object "hash:mtime"
    cache_object = '{0}:{1}'.format(ret['hsum'], os.path.getmtime(path))
    with salt.utils.flopen(cache_path, 'w') as fp_:
        fp_.write(cache_object)
    return ret


def _file_lists(load, form):
    """
    Return a dict containing the file lists for files, dirs, emtydirs and symlinks
    """
    if 'env' in load:
        salt.utils.warn_until(
            'Carbon',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Carbon.'
        )
        load['saltenv'] = load.pop('env')
    if load['saltenv'] not in envs():
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
        for path in _get_dir_list(load['saltenv']):
            for root, dirs, files in os.walk(
                    path,
                    followlinks=__opts__['fileserver_followsymlinks']):
                dir_rel_fn = os.path.relpath(root, path)
                if __opts__.get('file_client', 'remote') == 'local' and os.path.sep == "\\":
                    dir_rel_fn = dir_rel_fn.replace('\\', '/')
                ret['dirs'].append(dir_rel_fn)
                if len(dirs) == 0 and len(files) == 0:
                    if not salt.fileserver.is_file_ignored(__opts__, dir_rel_fn):
                        ret['empty_dirs'].append(dir_rel_fn)
                for fname in files:
                    is_link = os.path.islink(os.path.join(root, fname))
                    if is_link:
                        ret['links'].append(fname)
                    if __opts__['fileserver_ignoresymlinks'] and is_link:
                        continue
                    rel_fn = os.path.relpath(
                                os.path.join(root, fname),
                                path
                            )
                    if not salt.fileserver.is_file_ignored(__opts__, rel_fn):
                        if __opts__.get('file_client', 'remote') == 'local' and os.path.sep == "\\":
                            rel_fn = rel_fn.replace('\\', '/')
                        ret['files'].append(rel_fn)
        if save_cache:
            try:
                salt.fileserver.write_file_list_cache(
                    __opts__, ret, list_cache, w_lock
                )
            except NameError:
                # Catch msgpack error in salt-ssh
                pass
        return ret.get(form, [])
    # Shouldn't get here, but if we do, this prevents a TypeError
    return []


def symlink_list(load):
    """
    Return a dict of all symlinks based on a given path on the Master
    """
    if 'env' in load:
        salt.utils.warn_until(
            'Carbon',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Carbon.'
        )
        load['saltenv'] = load.pop('env')

    ret = {}
    if load['saltenv'] not in envs():
        return ret
    for path in _get_dir_list(load['saltenv']):
        try:
            prefix = load['prefix'].strip('/')
        except KeyError:
            prefix = ''
        # Adopting rsync functionality here and stopping at any encounter of a symlink
        for root, dirs, files in os.walk(os.path.join(path, prefix), followlinks=False):
            for fname in files:
                if not os.path.islink(os.path.join(root, fname)):
                    continue
                rel_fn = os.path.relpath(
                            os.path.join(root, fname),
                            path
                        )
                if not salt.fileserver.is_file_ignored(__opts__, rel_fn):
                    ret[rel_fn] = os.readlink(os.path.join(root, fname))
            for dname in dirs:
                if os.path.islink(os.path.join(root, dname)):
                    ret[os.path.relpath(os.path.join(root,
                                                     dname),
                                        path)] = os.readlink(os.path.join(root,
                                                                          dname))
    return ret
