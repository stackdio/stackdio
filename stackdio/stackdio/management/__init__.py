#!/usr/bin/env python

# WARN: This is used as a console_scripts entrypoint set via setuptools during
# a stackdio install. There are things these various commands do that require
# stackdio, salt, and other packages to be installed into site-packages. Using
# this without an install will not work as expected. After an install, the
# command `stackdio` will be available.

import argparse
import sys

if sys.stdout.isatty():
    import readline  # NOQA

from . import commands

SALT_COMMANDS = (
    'salt',
    'salt-master',
    'salt-run',
    'salt-cloud',
    'salt-key',
)


def main():
    parser = argparse.ArgumentParser(prog='stackdio')
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='available subcommands')

    # Runs the user through a set of questions, builds the ~/.stackdio/config
    # file, renders the salt master and cloud templates, and copies over
    # the base set of states, pillar, user_states, and salt extensions
    init_parser = subparsers.add_parser(
        'init',
        help='initialize stackdio configuration',
        description='Initializes the required stackdio configuration file.')
    init_parser.set_defaults(command=commands.InitCommand)
    init_parser.set_defaults(raw_args=False)

    # Dumps the configuration of various things
    config_parser = subparsers.add_parser(
        'config',
        help='dumps configuration for stackdio and 3rd-party services')
    config_parser.add_argument('type',
                               nargs='?',
                               default='stackdio',
                               help=('The type of configuration to dump. '
                                     'Valid choices: stackdio, nginx, '
                                     'apache, supervisord. Default is '
                                     'stackdio.'))
    config_parser.add_argument('--with-ssl',
                               default=False,
                               action='store_true',
                               help=('Toggles SSL for apache and nginx '
                                     'configuration.'))
    config_parser.add_argument('--exclude-gunicorn',
                               dest='with_gunicorn',
                               default=True,
                               action='store_false',
                               help=('Excludes gunicorn from supervisord.'))
    config_parser.add_argument('--exclude-celery',
                               dest='with_celery',
                               default=True,
                               action='store_false',
                               help=('Excludes celery from supervisord.'))
    config_parser.add_argument('--exclude-salt-master',
                               dest='with_salt_master',
                               default=True,
                               action='store_false',
                               help=('Excludes salt-master from supervisord.'))
    config_parser.set_defaults(command=commands.ConfigCommand)
    config_parser.set_defaults(raw_args=False)

    upgrade_salt_parser = subparsers.add_parser(
        'upgrade-salt',
        help='upgrade your salt version')
    upgrade_salt_parser.add_argument('version',
                                     help=('The version of salt you would like '
                                           'to upgrade to'))
    upgrade_salt_parser.set_defaults(command=commands.UpgradeSaltCommand)
    upgrade_salt_parser.set_defaults(raw_args=False)

    # Runs the development Django server for stackdio API/UI
    managepy_parser = subparsers.add_parser(
        'manage.py',
        help='convenience wrapper for Django\' manage.py command',
        add_help=False)
    managepy_parser.set_defaults(command=commands.DjangoManageWrapperCommand)
    managepy_parser.set_defaults(raw_args=True)

    # Expose salt-specific commands that we'll wrap and execute with
    # the appropriate arguments
    for wrapper in SALT_COMMANDS:
        wrapper_parser = subparsers.add_parser(
            wrapper,
            add_help=False,
            help='convenience wrapper for `{0}` command'.format(wrapper))
        wrapper_parser.set_defaults(command=commands.SaltWrapperCommand)
        wrapper_parser.set_defaults(raw_args=True)

    # parse args
    args, unknown_args = parser.parse_known_args()
    if args.raw_args:
        args.command(sys.argv[1:])()
    else:
        args.command(args, parser=parser)()

if __name__ == '__main__':
    main()
