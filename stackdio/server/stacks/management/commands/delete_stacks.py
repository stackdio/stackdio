from django.core.management.base import BaseCommand, CommandError
from stacks.models import Stack

import logging
logger = logging.getLogger('stacks')

class Command(BaseCommand):
    args = ''
    help = 'Removes all Stack objects from the database.'

    def handle(self, *args, **kwargs):
        logger.info('Deleting all Stack objects from the database...')
        Stack.objects.all().delete()
