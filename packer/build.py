#!/usr/bin/env python

import os
import subprocess
import sys
import urllib2


def main():
    if len(sys.argv) < 2:
        sys.stderr.write('usage: build.py <version>\n')
        return 1

    version = sys.argv[1]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    dist_dir = os.path.join(base_dir, 'dist')

    wheel_file = os.path.join(dist_dir, 'stackdio_server-{0}-py2-none-any.whl'.format(version))

    if not os.path.isdir(dist_dir):
        os.mkdir(dist_dir)
    elif os.path.exists(wheel_file):
        os.remove(wheel_file)

    try:
        response = urllib2.urlopen('https://github.com/stackdio/stackdio/releases/download/{0}/'
                                   'stackdio_server-{0}-py2-none-any.whl'.format(version))

        f = open(wheel_file, 'w')
        f.write(response.read())
        f.close()

    except urllib2.URLError:
        sys.stderr.write('Invalid version supplied.  Please try one listed here:  '
                         'https://github.com/stackdio/stackdio/releases\n')
        return 1

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
