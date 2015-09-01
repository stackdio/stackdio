# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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

from __future__ import print_function

import os
import sys

from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession


if float('{0}.{1}'.format(*sys.version_info[:2])) < 2.7:
    err_msg = ('Your Python version {0}.{1}.{2} is not supported.\n'
               'stackdio-server requires Python 2.7 or newer.\n'.format(*sys.version_info[:3]))
    sys.stderr.write(err_msg)
    sys.exit(1)


root_dir = os.path.dirname(os.path.abspath(__file__))

components_dir = os.path.join(
    root_dir,
    'stackdio',
    'ui',
    'static',
    'stackdio',
    'lib',
    'bower_components',
)

build_dir = os.path.join(
    root_dir,
    'stackdio',
    'ui',
    'static',
    'stackdio',
    'build',
)

# Force the user to build the ui first
if not os.path.exists(build_dir):
    err_msg = ('It looks like you haven\'t built the ui yet.  Please run '
               '`python manage.py build_ui` before using setup.py.\n')
    sys.stderr.write(err_msg)
    sys.exit(1)

# Force the user to install bower components first
if not os.path.exists(components_dir):
    err_msg = ('It looks like you haven\'t installed the bower dependencies yet.  Please run '
               '`bower install` before using setup.py.\n')
    sys.stderr.write(err_msg)
    sys.exit(1)

# Grab the current version from our stackdio package
from stackdio.server import __version__
VERSION = __version__

# Short and long descriptions for our package
SHORT_DESCRIPTION = ('A cloud deployment, automation, and orchestration '
                     'platform for everyone.')
LONG_DESCRIPTION = SHORT_DESCRIPTION

# If we have a README.md file, use its contents as the long description
if os.path.isfile('README.md'):
    with open('README.md') as f:
        LONG_DESCRIPTION = f.read()


def load_pip_requirements(fp):
    return [str(r.req) for r in parse_requirements(fp, session=PipSession())]

if __name__ == "__main__":
    # build our list of requirements and dependency links based on our
    # requirements.txt file
    reqs = load_pip_requirements('requirements.txt')

    # Call the setup method from setuptools that does all the heavy lifting
    # of packaging stackdio
    setup(
        name='stackdio-server',
        version=VERSION,
        url='http://stackd.io',
        author='Digital Reasoning Systems, Inc.',
        author_email='info@stackd.io',
        description=SHORT_DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license='Apache 2.0',
        include_package_data=True,
        packages=find_packages(exclude=('tests', 'dist', 'build')),
        zip_safe=False,
        install_requires=reqs,
        dependency_links=[],
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Web Environment',
            'Framework :: Django',
            'Framework :: Django :: 1.8',
            'Intended Audience :: Developers',
            'Intended Audience :: Information Technology',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Topic :: System :: Clustering',
            'Topic :: System :: Distributed Computing',
        ],
        entry_points={'console_scripts': [
            'stackdio = stackdio.server.management:main'
        ]}
    )
