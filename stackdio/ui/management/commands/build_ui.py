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

import os
import shutil
import subprocess
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import get_template

STATIC_DIR = os.path.join(
    settings.BASE_DIR,
    'stackdio',
    'ui',
    'static',
    'stackdio',
)

APP_DIR = os.path.join(STATIC_DIR, 'app')
BUILD_DIR = os.path.join(STATIC_DIR, 'build')

BOWER_PATH = os.path.join(
    STATIC_DIR,
    'lib',
    'bower_components',
)

NODE_PATH = os.path.join(
    settings.BASE_DIR,
    'node_modules',
)

R_JS = os.path.join(
    NODE_PATH,
    '.bin',
    'r.js',
)

BUILD_FILE = os.path.join(
    settings.BASE_DIR,
    'stackdio',
    'ui',
    'management',
    'files',
    'app.build.js',
)


class Command(BaseCommand):
    help = 'Optimizes all the javascript files'

    def handle(self, *args, **options):
        try:
            self._handle(*args, **options)
        except (KeyboardInterrupt, EOFError):
            # Clean up after ourselves if somebody quits
            try:
                shutil.rmtree(NODE_PATH)
            except Exception:
                pass

    def _handle(self, *args, **options):
        # Force the user to install bower components first
        if not os.path.exists(BOWER_PATH):
            err_msg = ('It looks like you haven\'t installed the bower dependencies yet.  '
                       'Please run `bower install` before using this command.\n')
            self.stderr.write(err_msg)
            sys.exit(1)

        # Install r.js
        args = ['npm', 'install', 'requirejs']
        ret = subprocess.call(args, cwd=settings.BASE_DIR)

        if ret:
            self.stderr.write('Failed to install requirejs with npm.\n')
            sys.exit(1)

        # Get rid of our build dir if it's already there
        if os.path.exists(BUILD_DIR):
            shutil.rmtree(BUILD_DIR)

        main_template = get_template('stackdio/js/main.js')

        js = main_template.render({})

        # Replace our appDir
        js = js.replace('{0}stackdio/app'.format(settings.STATIC_URL), '.')

        full_path = os.path.join(APP_DIR, 'main.js')

        # Write it to disk
        with open(full_path, 'w') as f:
            f.write(js)

        # Optimize the project using r.js
        args = ['node', R_JS, '-o', BUILD_FILE]

        # Build the optimized file
        ret = subprocess.call(args)
        if ret:
            self.stderr.write('Failed to optimize project\n')
            sys.exit(1)

        built_main_file = os.path.join(BUILD_DIR, 'main.js')

        # Grab the contents of the build main file
        with open(built_main_file, 'r') as f:
            built_main_js = f.read()

        # Fix the built main file
        built_main_js = built_main_js.replace(
            'baseUrl:"."',
            'baseUrl:"{0}stackdio/build"'.format(settings.STATIC_URL)
        )

        # Write it back out to disk
        with open(built_main_file, 'w') as f:
            f.write(built_main_js)

        # Get rid of temporary main.js
        os.remove(full_path)

        # Remove the extra build.txt file r.js throws in
        os.remove(os.path.join(BUILD_DIR, 'build.txt'))

        # Get rid of our node_modules
        shutil.rmtree(NODE_PATH)
