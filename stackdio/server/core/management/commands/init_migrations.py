import os
import sys
import glob

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import logging
logger = logging.getLogger('core')

class Command(BaseCommand):
    args = 'app-name, app-name, ...'
    help = 'Deletes all migrations for the given app and re-initializes them.'

    def handle(self, *args, **kwargs):
        if len(args) == 0:
            self.error('At least one app-name must be provided.')

        for app_name in args:
            migration_dir = os.path.join(
                settings.SITE_ROOT,
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
            logger.info('Executing manage.py schemamigration {0} ' \
                        '--initial'.format(app_name))
            call_command('schemamigration', app_name, initial=True)
            

    def error(self, msg=''):
        logger.error(msg)
        sys.exit(1)
