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
The stackdio file server backend

This fileserver backend serves files from the Master's local filesystem.
``stackdio`` must be in the :conf_master:`fileserver_backend` list to enable this backend.

.. code-block:: yaml

    fileserver_backend:
      - stackdio
      - roots

This backend allows us to have several environments that change dynamically rather
than static environments in the config file.
"""
from __future__ import absolute_import

import errno
import logging
import os

import salt.ext.six as six
import salt.fileserver
import salt.utils
from salt.utils.event import tagify


log = logging.getLogger(__name__)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stackdio.server.settings.production')


__virtualname__ = 'stackdio'


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
from stackdio.api.formulas.models import Formula  # NOQA
from stackdio.api.stacks.models import Stack  # NOQA
from stackdio.api.environments.models import Environment  # NOQA


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

    if not os.path.exists(root_dir):
        os.makedirs(root_dir)

    if not os.path.isdir(root_dir):
        log.warn('The env dir doesn\'t exist... Something has gone horribly wrong.')

    salt_files_dir = os.path.join(root_dir, 'salt_files')

    if not os.path.exists(salt_files_dir):
        os.mkdir(salt_files_dir, 0o755)

    return salt_files_dir


def _get_object(saltenv):
    env_type, dot, obj_id = saltenv.partition('.')

    if env_type == 'environments':
        return Environment.objects.get(name=obj_id)
    elif env_type == 'stacks':
        return Stack.objects.get(id=int(obj_id))
    elif env_type == 'cloud':
        return CloudAccount.objects.get(slug=obj_id)
    else:
        log.warning('Invalid saltenv: {}'.format(saltenv))
        return None


def _get_dir_list(saltenv):
    """
    Get a list of all search directories for the given saltenv
    :param saltenv: the salt env
    :return: A list of filesystem paths to search for files
    """
    return [_get_env_dir(saltenv)]


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

    # Just look in the one stack directory first
    for root in _get_dir_list(saltenv):
        full = os.path.join(root, path)
        if os.path.isfile(full) and not salt.fileserver.is_file_ignored(__opts__, full):
            fnd['path'] = full
            fnd['rel'] = path
            fnd['stat'] = list(os.stat(full))
            return fnd

    # Then check all of the formulas
    obj = _get_object(saltenv)

    for formula_version in obj.formula_versions.all():
        gitfs = formula_version.formula.get_gitfs()
        formula_fnd = gitfs.find_file(path, formula_version.version, **kwargs)

        # If we have a hit here, return it, otherwise go on to the next one
        if formula_fnd['path']:
            return formula_fnd

    return fnd


def envs():
    """
    Return the file server environments
    """
    ret = []

    for env in Environment.objects.all():
        ret.append('environments.{}'.format(env.name))

    for stack in Stack.objects.all():
        ret.append('stacks.{}'.format(stack.id))

    for account in CloudAccount.objects.all():
        ret.append('cloud.{}'.format(account.slug))

    return ret


def serve_file(load, fnd):
    """
    Return a chunk from a file based on the data received
    """
    if 'env' in load:
        salt.utils.warn_until(
            'Carbon',
            'Passing a salt environment should be done using \'saltenv\' '
            'not \'env\'. This functionality will be removed in Salt Carbon.'
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
    with salt.utils.fopen(os.path.normpath(fnd['path']), 'rb') as fp_:
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

    # Update all of the formulas too
    for formula in Formula.objects.all():
        gitfs = formula.get_gitfs()
        gitfs.update()


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
                              u'{0}.hash.{1}'.format(fnd['rel'], __opts__['hash_type']))

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


def file_list(load):
    """
    Return a list of all files on the file server in a specified
    environment
    """
    # Grab the local ones
    ret = _file_lists(load, 'files')

    saltenv = load['saltenv']

    if saltenv not in envs():
        return ret

    # Then check all of the formulas
    obj = _get_object(saltenv)

    for formula_version in obj.formula_versions.all():
        gitfs = formula_version.formula.get_gitfs()
        # temporarily inject our saltenv
        load['saltenv'] = formula_version.version
        ret.extend(gitfs.file_list(load))

    # put the saltenv back
    load['saltenv'] = saltenv

    return ret


def file_list_emptydirs(load):
    """
    Return a list of all empty directories on the master
    """
    return _file_lists(load, 'empty_dirs')


def dir_list(load):
    """
    Return a list of all directories on the master
    """
    ret = _file_lists(load, 'dirs')

    saltenv = load['saltenv']

    if saltenv not in envs():
        return ret

    # Then check all of the formulas
    obj = _get_object(saltenv)

    for formula_version in obj.formula_versions.all():
        gitfs = formula_version.formula.get_gitfs()
        # temporarily inject our saltenv
        load['saltenv'] = formula_version.version
        ret.extend(gitfs.dir_list(load))

    # put the saltenv back
    load['saltenv'] = saltenv

    return ret


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
    saltenv = load['saltenv']
    if saltenv not in envs():
        return ret
    for path in _get_dir_list(saltenv):
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

    # Then check all of the formulas
    obj = _get_object(saltenv)

    for formula_version in obj.formula_versions.all():
        gitfs = formula_version.formula.get_gitfs()
        # temporarily inject our saltenv
        load['saltenv'] = formula_version.version
        for k, v in gitfs.symlink_list(load).items():
            if k not in ret:
                ret[k] = v

    # put the saltenv back
    load['saltenv'] = saltenv

    return ret
