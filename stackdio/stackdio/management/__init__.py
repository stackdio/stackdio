#!/usr/bin/env python

import readline  # NOQA
import argparse

from commands import InitCommand


def main():
    parser = argparse.ArgumentParser(prog='stackdio')
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='available subcommands')

    init_parser = subparsers.add_parser(
        'init',
        help='initialize stackdio configuration',
        description='Initializes the required stackdio configuration file.')
    init_parser.set_defaults(command_class=InitCommand)

    # parse args
    args = parser.parse_args()
    args.command_class(args)()

if __name__ == '__main__':
    main()
