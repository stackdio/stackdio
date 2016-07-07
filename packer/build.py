#!/usr/bin/env python

import os
import subprocess
import sys


def main():
    if len(sys.argv) < 2:
        sys.stderr.write('usage: build.py <version>\n')
        return 1

    version = sys.argv[1]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    os.environ['STACKDIO_VERSION'] = version

    p = subprocess.Popen(['packer', 'build', 'packer/build.json'], cwd=base_dir)

    should_exit = False

    # Make sure our script doesn't exit until packer does
    while not should_exit:
        try:
            p.wait()
            should_exit = True
        except (KeyboardInterrupt, EOFError):
            pass

    return 0

if __name__ == '__main__':
    sys.exit(main())
