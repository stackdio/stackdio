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


import os
import sys

from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession


if float('{0}.{1}'.format(*sys.version_info[:2])) < 2.7:
    print('Your Python version {0}.{1}.{2} is not supported.'.format(*sys.version_info[:3]))
    print('stackdio requires Python 2.7 or newer.')
    sys.exit(1)

# Grab the current version from our stackdio package
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'stackdio'))
VERSION = __import__('stackdio').__version__
sys.path.pop(0)

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


def load_pip_links(fp):
    deps = []
    for d in parse_requirements(fp, session=PipSession()):
        # Support for all pip versions
        if hasattr(d, 'link'):
            # pip >= 6.0
            deps.append(str(d.link.url))
        else:
            # pip < 6.0
            deps.append(str(d.url))
    return deps

if __name__ == "__main__":
    # build our list of requirements and dependency links based on our
    # requirements.txt file
    reqs = load_pip_requirements('requirements.txt')
    deps = load_pip_links('links.txt')

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
        packages=find_packages('stackdio'),
        package_dir={'': 'stackdio'},
        py_modules=['manage'],
        zip_safe=False,
        install_requires=reqs,
        dependency_links=deps,
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Web Environment',
            'Framework :: Django',
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
            'stackdio = stackdio.management:main'
        ]}
    )
