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

from __future__ import print_function

import os
import sys

from setuptools import setup, find_packages

major = sys.version_info[0]
minor = sys.version_info[1]
micro = sys.version_info[2]

supported_versions = [
    (2, 7),
    (3, 4),
    (3, 5),
]

if (major, minor) not in supported_versions:
    err_msg = ('Your Python version {0}.{1}.{2} is not supported.\n'
               'stackdio-server requires Python 2.7, 3.4, or 3.5.\n'.format(major, minor, micro))
    sys.stderr.write(err_msg)
    sys.exit(1)


root_dir = os.path.dirname(os.path.abspath(__file__))

bower_dir = 'stackdio/ui/static/stackdio/lib/bower_components'

components_dir = os.path.join(root_dir, bower_dir)

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
SHORT_DESCRIPTION = 'A cloud deployment, automation, and orchestration platform for everyone.'

# Grab README.md and use its contents as the long description
with open('README.rst') as f:
    LONG_DESCRIPTION = f.read()

requirements = [
    # Heavily used, hold to a specific minor version (let the patch version update)
    'celery[redis]~=3.1.0',
    'Django~=1.9.0',
    'djangorestframework~=3.4.0',
    'salt~=2016.3.0',

    # Used, but still hold an upper bound on the version
    'boto~=2.32',
    'boto3~=1.4.0',
    'django-activity-stream~=0.6.0',
    'django-extensions~=1.6.0',
    'django-filter~=0.9',
    'django-guardian~=1.4.2',
    'django-model-utils~=2.0',
    'django-redis-cache~=1.7.0',
    'Jinja2~=2.0',

    # Light usage, no need to have an upper bound on the version
    'dj-database-url>=0.3',
    'envoy',
    'GitPython>=2.0',
    'Markdown>=2.6',
    'pip>=6',
    'PyYAML>=3.10',
    'requests>=2.4',
    'six>=1.6',
]

testing_requirements = [
    'coveralls',
    'mock',
    'pep8',
    'pylint',
    'pytest',
    'pytest-cov',
    'pytest-django',
]

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
    packages=find_packages(exclude=('tests', 'dist', 'build', 'docs')),
    zip_safe=False,
    install_requires=requirements,
    extras_require={
        'production': [
            'gunicorn>=19.0',
            'supervisor>=3.0',
        ],
        'mysql': [
            'mysqlclient>=1.3.3',
        ],
        'postgresql': [
            'psycopg2>=2.5.0',
        ],
        'ldap': [
            'django-auth-ldap~=1.2.7',
        ],
        'slack': [
            'slackclient>=1.0.0',
        ],
        'development': testing_requirements + ['ipython>=2.0'],
        'testing': testing_requirements,
    },
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: System :: Clustering',
        'Topic :: System :: Distributed Computing',
    ],
    entry_points={
        'console_scripts': [
            'stackdio = stackdio.server.management:main',
        ],
    }
)
