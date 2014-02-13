#!/usr/bin/env python

import argparse
import os
import sys
import yaml
import jinja2
from django.utils.crypto import get_random_string

from salt.utils import get_colors
COLORS = get_colors()

CONFIG_FILE = os.path.expanduser('~/.stackdio/config')

def _write(msg, color='DEFAULT_COLOR', fp=sys.stdout):
    fp.write(COLORS[color] + msg + COLORS['ENDC'])

def _prompt(message='', default_value=None, choices=None):
    try:
        while True:
            s = ''
            if message:
                s = COLORS['GREEN'] + '{0} '.format(message.strip() )
            if choices:
                s += '{0} '.format(tuple(choices))
            if default_value:
                s += '{0}[{1}{2}{0}] '.format(COLORS['BLACK'],
                                              COLORS['BLUE'],
                                              default_value)
            s += COLORS['ENDC']
            value = raw_input(s)

            if value and not choices:
                return value
            if not value and default_value:
                return default_value
            if choices and value in choices:
                return value
            if choices and value not in choices:
                _write('Invalid response. Must be one of {0}\n\n'
                       .format(choices), 'RED_BOLD')
            else:
                _write('Invalid response. Please provide a value.\n\n',
                       'RED_BOLD')

    except (KeyboardInterrupt, EOFError):
        _write('\nAborting.\n', 'RED_BOLD')
        sys.exit(1)

def init(args):
    options = [
        ('user',
         'Which user will stackdio and salt run as?',
         'This user will own services, files, etc related to stackdio.',
         'stackdio'),
        ('storage_root',
         'Where should stackdio and salt store their data?',
         'Root directory for stackdio to store its files, logs, salt\n'
         'configuration, etc. It must exist and be owned by the user\n'
         'provided above.',
         '/var/lib/stackdio'),
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
                _write('## INFO: Existing configuration file found. Using '
                      'values as defaults.\n\n', 'LIGHT_CYAN')

    # The template expects a django_secret_key, and if we don't have one
    # we'll generate one for the user automatically (using the logic
    # provided by Django)
    if not config.get('django_secret_key'):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        config['django_secret_key'] = get_random_string(50, chars)

    for option in options:
        attr, title, desc, default = option
        if attr in config:
            default = config[attr]
        _write('## {0}\n'.format(title), 'GREEN')
        _write('{0}\n'.format(desc), 'GREEN')
        value = _prompt('', default)
        _write('\n')
        config[attr] = value

    _write('Are the following values correct?\n', 'GREEN')
    for option in options:
        _write('    {0}\n'.format(config[option[0]]), 'BLUE')
    _write('\nWARNING: If you say no, we will abort without changing '
           'anything!\n\n', 'RED_BOLD')

    ok = _prompt('Correct? ', choices=('yes', 'no'))

    if ok == 'no':
        _write('\nAborting.\n', 'RED_BOLD')
        sys.exit(1)

    # render config template
    with open('templates/config') as f:
        t = jinja2.Template(f.read())

    with open(CONFIG_FILE, 'w') as f:
        f.write(t.render(config))

    _write('\nConfiguration written! Exiting.\n', 'CYAN')


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
