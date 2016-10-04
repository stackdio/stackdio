# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import unicode_literals

import logging

import six
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def get_user_queryset():
    return get_user_model().objects.all()


@six.python_2_unicode_compatible
class UserSettings(models.Model):

    class Meta:
        verbose_name_plural = 'User settings'
        default_permissions = ()

    # which user the settings below
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='settings')

    # public RSA key for the user
    public_key = models.TextField(blank=True)

    # Is the advanced view on?
    advanced_view = models.BooleanField('Advanced View', default=False)

    def __str__(self):
        return six.text_type('Settings for {}'.format(self.user.username))


@receiver(models.signals.post_save, sender=settings.AUTH_USER_MODEL)
def user_post_save(sender, **kwargs):
    """
    Catch the post_save signal for all User objects and create a
    UserSettings objects if needed
    """
    if kwargs.get('raw'):
        # Don't do this on loaddata
        return

    user = kwargs.pop('instance')
    created = kwargs.pop('created', False)

    if created:
        UserSettings.objects.create(user=user)
