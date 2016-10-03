#!/usr/bin/env python
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


# WARN: This is used as a console_scripts entrypoint set via setuptools during
# a stackdio install. There are things these various commands do that require
# stackdio, salt, and other packages to be installed into site-packages. Using
# this without an install will not work as expected. After an install, the
# command `stackdio` will be available.

import argparse
import sys

from stackdio.server.management import commands
from stackdio.server.version import __version__


if sys.stdout.isatty():
    import readline  # pylint: disable=wrong-import-order


def main():
    parser = argparse.ArgumentParser(prog='stackdio')

    parser.add_argument('-v', '--version',
                        action='version',
                        version=__version__)

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
                                     'supervisord. Default is stackdio.'))
    config_parser.add_argument('--with-ssl',
                               default=False,
                               action='store_true',
                               help='Toggles SSL for nginx configuration.')
    config_parser.add_argument('--exclude-gunicorn',
                               dest='with_gunicorn',
                               default=True,
                               action='store_false',
                               help='Excludes gunicorn from supervisord.')
    config_parser.add_argument('--exclude-celery',
                               dest='with_celery',
                               default=True,
                               action='store_false',
                               help='Excludes celery from supervisord.')
    config_parser.add_argument('--exclude-salt-master',
                               dest='with_salt_master',
                               default=True,
                               action='store_false',
                               help='Excludes salt-master from supervisord.')
    config_parser.set_defaults(command=commands.ConfigCommand)
    config_parser.set_defaults(raw_args=False)

    upgrade_salt_parser = subparsers.add_parser(
        'upgrade-salt',
        help='upgrade your salt version in config files')
    upgrade_salt_parser.set_defaults(command=commands.UpgradeSaltCommand)
    upgrade_salt_parser.set_defaults(raw_args=False)

    celery_parser = subparsers.add_parser(
        'celery',
        help='convenience wrapper for the celery command',
        add_help=False
    )
    celery_parser.set_defaults(command=commands.CeleryWrapperCommand)
    celery_parser.set_defaults(raw_args=True)

    # Runs the development Django server for stackdio API/UI
    managepy_parser = subparsers.add_parser(
        'manage.py',
        help='convenience wrapper for Django\'s manage.py command',
        add_help=False)
    managepy_parser.set_defaults(command=commands.DjangoManageWrapperCommand)
    managepy_parser.set_defaults(raw_args=True)

    # Expose salt-specific commands that we'll wrap and execute with
    # the appropriate arguments
    for wrapper in commands.SaltWrapperCommand.COMMANDS:
        wrapper_parser = subparsers.add_parser(
            wrapper,
            add_help=False,
            help='convenience wrapper for `{0}` command'.format(wrapper))
        wrapper_parser.set_defaults(command=commands.SaltWrapperCommand)
        wrapper_parser.set_defaults(raw_args=True)

    # parse args
    args, unknown_args = parser.parse_known_args()  # pylint: disable=unused-variable
    if args.raw_args:
        args.command(sys.argv[1:])()
    else:
        args.command(args, parser=parser)()

if __name__ == '__main__':
    main()
