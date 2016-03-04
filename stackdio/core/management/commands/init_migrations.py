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
import sys
import glob
import logging

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

logger = logging.getLogger('core')


class Command(BaseCommand):
    args = 'app-name, app-name, ...'
    help = 'Deletes all migrations for the given app and re-initializes them.'

    def handle(self, *args, **kwargs):
        if len(args) == 0:
            self.error('At least one app-name must be provided.')

        for app_name in args:
            migration_dir = os.path.join(
                settings.BASE_DIR,
                app_name,
                'migrations'
            )

            if not os.path.isdir(migration_dir):
                logger.warn('No migrations found for {0} in {1}'.format(
                    app_name,
                    migration_dir
                ))
                continue

            glob_str = os.path.join(migration_dir, '*.py')
            for fp in glob.glob(glob_str):
                if fp.endswith('__init__.py'):
                    # skip module file
                    continue
                logger.info('Removing {0}'.format(fp))
                os.remove(fp)

            # Initialize migrations
            logger.info('Executing manage.py makemigrations {0}'.format(app_name))
            call_command('makemigrations', app_name)

    def error(self, msg=''):
        logger.error(msg)
        sys.exit(1)
