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
