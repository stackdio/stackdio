#!/usr/bin/env python

import argparse
import jinja2
import os
import shutil
import sys
import yaml
from django.utils.crypto import get_random_string

from salt.utils import get_colors
COLORS = get_colors()

# color shortcuts
C_BLACK = COLORS['DEFAULT_COLOR']
C_ERROR = COLORS['RED_BOLD']
C_WARN = COLORS['BROWN']
C_INFO = COLORS['CYAN']
C_PROMPT = COLORS['GREEN']
C_VALUE = COLORS['BLUE']

CONFIG_DIR = os.path.expanduser('~/.stackdio')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config')


def _write(msg, color=C_BLACK, fp=sys.stdout):
    fp.write(color + msg + COLORS['ENDC'])


def _prompt(message='', default_value=None, choices=None, validator=None, config=None):  # NOQA
    try:
        while True:
            s = ''
            if message:
                s = C_PROMPT + '{0} '.format(message.strip())
            if choices:
                s += '{0} '.format(tuple(choices))
            if default_value:
                s += '{0}[{1}{2}{0}] '.format(C_BLACK,
                                              C_VALUE,
                                              default_value)
            s += COLORS['ENDC']
            value = raw_input(s)

            if choices and value not in choices:
                _write('Invalid response. Must be one of {0}\n\n'
                       .format(choices), C_ERROR)
                continue
            if not value and default_value is None:
                _write('Invalid response. Please provide a value.\n\n',
                       C_ERROR)
                continue

            if not value:
                value = default_value

            if validator is None:
                return value

            ok, msg = validator(value, config=config)
            if ok:
                return value

            _write('{0}\n\n'.format(msg), C_ERROR)

    except (KeyboardInterrupt, EOFError):
        _write('\nAborting.\n', C_ERROR)
        sys.exit(1)


def _load_resource(rp):
    '''
    Takes a relative path `rp`, and attempts to pull the full resource
    path using pkg_resources.
    '''
    from pkg_resources import ResourceManager, get_provider
    provider = get_provider('stackdio')
    return provider.get_resource_filename(ResourceManager(),
                                          os.path.join('stackdio', rp))


def _render_template(tmpl, outfile, context={}):
    tmpl = _load_resource(tmpl)
    with open(tmpl) as f:
        t = jinja2.Template(f.read())

    with open(outfile, 'w') as f:
        f.write(t.render(context))


def _init_stackdio(config):
    # create config dir if it doesn't already exist
    if not os.path.isdir(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, mode=0755)

    _render_template('management/templates/config.jinja2',
                     CONFIG_FILE,
                     context=config)
    _write('stackdio configuration written to {0}\n'.format(CONFIG_FILE),
           C_INFO)


def _init_salt(config):
    salt_dir = os.path.join(config['storage_root'], 'salt', 'config')
    master_path = os.path.join(salt_dir, 'master')
    cloud_path = os.path.join(salt_dir, 'cloud')

    if not os.path.isdir(salt_dir):
        os.makedirs(salt_dir)
        _write('Created salt configuration directory at '
               '{0}\n'.format(salt_dir), C_INFO)

    context = config.copy()
    context.update({
        'root_dir': salt_dir,
    })

    # Render salt-master and salt-cloud configuration files
    _render_template('management/templates/master.jinja2',
                     master_path,
                     context=context)
    _write('Salt master configuration written to {0}\n'.format(master_path),
           C_INFO)

    _render_template('management/templates/cloud.jinja2',
                     cloud_path,
                     context=context)
    _write('Salt cloud configuration written to {0}\n'.format(cloud_path),
           C_INFO)

    # Copy the salt directories needed
    saltdirs = _load_resource('management/saltdirs')
    for rp in os.listdir(saltdirs):
        path = os.path.join(saltdirs, rp)
        dst = os.path.join(salt_dir, rp)

        # check for existing dst and skip it
        if os.path.isdir(dst):
            _write('Salt configuration directory {0} already exists...'
                   'skipping.\n'.format(rp), C_WARN)
            continue

        shutil.copytree(path, dst)
        _write('Copied salt configuration directory {0}.\n'.format(rp),
               C_INFO)


def _is_valid_user(user, config=None):
    from pwd import getpwnam
    try:
        getpwnam(user)
    except KeyError:
        return False, 'User does not exist. Please try another user.'
    return True, ''


def _check_config_dir(path, config=None):
    from pwd import getpwnam

    if not os.path.exists(path):
        return False, 'Directory does not exist.'
    if not os.path.isdir(path):
        return False, 'Path is not a directory.'

    user = config['user']
    uid = getpwnam(user).pw_uid
    stat = os.stat(path)
    if stat.st_uid != uid:
        return False, 'Directory is not owned by {0} user.'.format(user)
    if not os.access(path, os.W_OK):
        return False, 'Directory is not writable.'
    return True, ''


def init(args):  # NOQA
    options = [
        ('user',
         'Which user will stackdio and salt run as?',
         'This user will own services, files, etc related to stackdio.',
         'stackdio',
         _is_valid_user),
        ('storage_root',
         'Where should stackdio and salt store their data?',
         'Root directory for stackdio to store its files, logs, salt\n'
         'configuration, etc. It must exist and be owned by the user\n'
         'provided above.',
         '/var/lib/stackdio',
         _check_config_dir),
        ('salt_bootstrap_script',
         'Which bootstrap script should salt-cloud use when launching VMs?',
         'When launching and bootstrapping machines using salt-cloud,\n'
         'what bootstrap script should be used? Typically, this should\n'
         'be left alone.',
         'bootstrap-salt'),
        ('salt_bootstrap_args',
         'Any special arguments for the bootstrap script?',
         'What arguments to pass to the bootstrap script above? For our\n'
         'purposes, we are enabling debug output for tracking down issues\n'
         'that may crop up during the bootstrap process. Override the\n'
         'defaults here. See http://bootstrap.saltstack.org for more info',
         '-D'),
        ('db_dsn',
         'What database DSN should stackdio use to connect to the DB?',
         'The database DSN the stackdio Django application will use to\n'
         'acccess the database server. The server must be running, the\n'
         'database must already exist, and the user must have access to it.',
         'mysql://user:pass@localhost:3306/stackdio'),
    ]

    config = {}
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
            if config is None:
                config = {}
            else:
                _write('## WARNING: Existing configuration file found. Using '
                       'values as defaults.\n\n', C_WARN)

    # The template expects a django_secret_key, and if we don't have one
    # we'll generate one for the user automatically (using the logic
    # provided by Django)
    if not config.get('django_secret_key'):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        config['django_secret_key'] = get_random_string(50, chars)

    for option in options:
        attr, title, desc, default = option[:4]
        if len(option) > 4:
            validator = option[4]
        else:
            validator = None
        if attr in config:
            default = config[attr]
        _write('## {0}\n'.format(title), C_PROMPT)
        _write('{0}\n'.format(desc), C_PROMPT)
        value = _prompt('', default, validator=validator, config=config)
        _write('\n')
        config[attr] = value

    _write('Are the following values correct?\n', C_PROMPT)
    for option in options:
        _write('    {0}\n'.format(config[option[0]]), C_VALUE)
    _write('\nWARNING: If you say no, we will abort without changing '
           'anything!\n\n', C_ERROR)

    ok = _prompt('Correct? ', choices=('yes', 'no'))
    _write('\n')

    if ok == 'no':
        _write('Aborting.\n', C_ERROR)
        sys.exit(1)

    _init_stackdio(config)
    _init_salt(config)
    _write('Finished\n', C_INFO)


def main():
    parser = argparse.ArgumentParser(prog='stackdio')
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='available subcommands')

    init_parser = subparsers.add_parser(
        'init',
        help='initialize stackdio configuration',
        description='Initializes the required stackdio configuration file.')
    init_parser.set_defaults(func=init)

    # parse args
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
