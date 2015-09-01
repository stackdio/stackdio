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

import errno
import os
import shutil
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import Context
from django.template.loader import get_template

from stackdio.ui import views as ui_views

STATIC_DIR = os.path.join(
    settings.BASE_DIR,
    'stackdio',
    'ui',
    'static',
    'stackdio',
)

INPUT_DIR = os.path.join(STATIC_DIR, 'app', 'build-input')
OUTPUT_DIR = os.path.join(STATIC_DIR, 'build')

BOWER_PATH = os.path.join(
    STATIC_DIR,
    'lib',
    'bower_components',
)

R_JS = os.path.join(
    settings.BASE_DIR,
    'node_modules',
    '.bin',
    'r.js',
)


class Command(BaseCommand):
    help = 'Optimizes all the javascript files'

    def handle(self, *args, **options):
        base_cls = ui_views.PageView

        viewmodels = set()

        for view in ui_views.__dict__.values():
            try:
                if issubclass(view, base_cls):
                    if view.viewmodel is not None:
                        viewmodels.add(view.viewmodel)
            except TypeError:
                # We don't care if it wasn't a class
                pass

        # Install bower dependencies
        args = ['bower', 'install']
        subprocess.call(args, cwd=settings.BASE_DIR)

        # Install r.js
        args = ['npm', 'install', 'requirejs']
        subprocess.call(args, cwd=settings.BASE_DIR)

        main_template = get_template('stackdio/js/main.js')

        # Go over each of the viewmodels
        for vm in viewmodels:
            # Render the main js file
            context = Context({'viewmodel': vm})
            js = main_template.render(context)
            full_path = os.path.join(INPUT_DIR, vm) + '.js'

            try:
                os.makedirs(os.path.dirname(full_path))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

            # Write it to disk
            with open(full_path, 'w') as f:
                f.write(js)

            output = os.path.join(OUTPUT_DIR, vm) + '.js'

            try:
                os.makedirs(os.path.dirname(output))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

            # Optimize the file using r.js
            args = [
                'node', R_JS, '-o',
                'baseUrl={0}/app'.format(STATIC_DIR),
                'name=build-input/{0}'.format(vm),
                'mainConfigFile={0}'.format(full_path),
                'out={0}'.format(output),
            ]

            # Build the optimized file
            subprocess.call(args)

        # Get rid of our input directory
        shutil.rmtree(INPUT_DIR)
