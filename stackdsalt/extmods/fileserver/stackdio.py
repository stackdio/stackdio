'''
TODO:
'''

#Import python libs
import logging
import os

# Import salt libs
import salt.fileserver
import salt.utils
from salt.utils.event import tagify

log = logging.getLogger(__name__)

def __virtual__():
    '''
    '''
    envs_dir = get_envs_dir()

    if envs_dir is None:
        log.error('stackdio fileserver is enabled in fileserver_backend '
                  'configuration, but envs location is missing in the '
                  'stackdio configuration')
        return False

    if not os.path.isdir(envs_dir):
        log.error('stackdio::user_envs location is not a directory.')
        return False

    return 'stackdio'

def get_envs_dir():
    return __opts__.get('stackdio', {}).get('user_envs', None)

def envs():
    ret = []
    envs_dir = get_envs_dir()
    if envs_dir is None:
        log.warn('stackdio fileserver user_envs configuration does not exist.')
        return ret  

    if not os.path.isdir(envs_dir):
        log.warn('stackdio fileserver user_envs configuration is not a directory.')
        return ret

    # Stackdio expects the directory specified in the master configuration 
    # under stackdio::envs to contain a number of other directories 
    # corresponding to the user who "owns" it. Each user will be considered
    # an environment to "sandbox" the formulas owned by them.
    for user in os.listdir(envs_dir):
        user_dir = os.path.join(envs_dir, user)
        if not os.path.isdir(user_dir):
            continue
        ret.append(user)
    log.warn('Environments = {0}'.format(ret))
    return ret

def find_file(path, env='base', **kwargs):
    '''
    Search the environment for the relative path
    '''
    log.warn('find_file {0}, {1}'.format(path, env))
    fnd = {'path': '',
           'rel': ''}
    if os.path.isabs(path):
        return fnd
    if env not in envs():
        return fnd

    root = os.path.join(get_envs_dir(), env)
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
    '''
    Return a chunk from a file based on the data received
    '''
    ret = {'data': '',
           'dest': ''}
    if 'path' not in load or 'loc' not in load or 'env' not in load:
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

def file_list(load):
    ret = []
    if load['env'] not in envs():
        return ret

    # each env is a specific directory tied to a stackdio user. Inside each
    # of those user directories are a number of imported/cloned formulas.
    # We need to build and return the file list for the given env/user
    env_dir = os.path.join(get_envs_dir(), load['env'])

    if not os.path.isdir(env_dir):
        log.error('Environment directory does not exist: {0}'.format(env_dir))
        return ret

    # each directory in the environment is a root of a formula
    ret = []
    for formula_root in os.listdir(env_dir):
        formula_dir = os.path.join(env_dir, formula_root)
        if not os.path.isdir(formula_dir):
            continue

        # walk each formula and pull the relative file paths
        for root, dirs, files in os.walk(formula_dir, followlinks=True):
            # The root of the formula contains README and other non-salt
            # related files
            if root == formula_dir:
                continue

            for fname in files:
                rel_fn = os.path.relpath(
                            os.path.join(root, fname),
                            formula_dir
                        )
                if not salt.fileserver.is_file_ignored(__opts__, rel_fn):
                    ret.append(rel_fn)
    log.warn('file_list: env={0}'.format(load['env']))
    log.warn(ret)
    return ret

def update():
    log.warn('stackdio fileserver - udpate called')

def file_hash(load, fnd):
    log.warn('stackdio fileserver - file_hash called')

def file_list_emptydirs(load):
    log.warn('stackdio fileserver - file_list_emptydirs called')

def dir_list(load):
    log.warn('stackdio fileserver - dir_list called')

