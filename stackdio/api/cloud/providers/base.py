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


import logging
import os
import shutil

from django.conf import settings
from rest_framework.serializers import ValidationError

from stackdio.core.constants import Health

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    pass


class MaxFailuresException(Exception):
    pass


class GroupNotFoundException(Exception):
    pass


class GroupExistsException(Exception):
    pass


class DeleteGroupException(Exception):
    pass


class RuleNotFoundException(Exception):
    pass


class RuleExistsException(Exception):
    pass


class SecurityGroupRule(object):
    def __init__(self, protocol, from_port, to_port, rule):
        self.protocol = protocol
        self.from_port = from_port
        self.to_port = to_port
        self.rule = rule


class SecurityGroup(object):
    def __init__(self, name, description, group_id, vpc_id, rules, rules_egress):
        self.name = name
        self.description = description
        self.group_id = group_id
        self.vpc_id = vpc_id
        self.rules = rules
        self.rules_egress = rules_egress


class BaseCloudProvider(object):

    REQUIRED_MESSAGE = 'This field is required.'

    # SHORT_NAME - required
    # Must correspond to a salt-cloud provider type (e.g, 'aws' or
    # 'rackspace')
    SHORT_NAME = None

    # LONG_NAME - required
    # The human readable version of the SHORT_NAME (e.g, 'Amazon
    # Web Services' or 'Rackspace')
    LONG_NAME = None

    def __init__(self, account=None, *args, **kwargs):
        if account:
            from stackdio.api.cloud.models import CloudAccount

            assert isinstance(account, CloudAccount)

        # The `account` attribute is the Django ORM object for this cloud
        # account instance. See models.py for more information.
        self.account = account

        # `provider_storage` is the location where provider implementations
        # should be writing their files to. If implementations are written
        # elsewhere, there's no guarantee that it will work later, be backed
        # up, etc.
        self.provider_storage = os.path.join(settings.FILE_STORAGE_DIRECTORY,
                                             'cloud',
                                             account.slug) if self.account else None

        # make sure the storage directory is available
        if self.provider_storage and not os.path.isdir(self.provider_storage):
            os.makedirs(self.provider_storage)

    def destroy(self):
        """
        Cleans up the provider storage. Overrides should call
        this method to make sure files and directories are
        properly removed.
        """
        if not self.provider_storage:
            return

        if os.path.isdir(self.provider_storage):
            logger.info('Deleting provider storage: {0}'.format(
                self.provider_storage
            ))
            shutil.rmtree(self.provider_storage)
            self.provider_storage = None

    @classmethod
    def get_provider_choice(cls):
        """
        Should return a two-element tuple of the short and long name of the
        provider type. This should be what the choices attribute on a
        model field is expected (e.g., ('db_value', 'Label') )
        """

        if not hasattr(cls, 'SHORT_NAME') or not cls.SHORT_NAME:
            raise AttributeError('SHORT_NAME must exist and be a string.')

        if not hasattr(cls, 'LONG_NAME') or not cls.LONG_NAME:
            raise AttributeError('LONG_NAME must exist and be a string.')

        return cls.SHORT_NAME, cls.LONG_NAME

    def get_health_from_state(self, state):
        return Health.UNKNOWN

    def get_required_fields(self):
        """
        Return the fields required in the data dictionary for
        `get_provider_data` and `validate_provider_data`
        """
        raise NotImplementedError()

    @classmethod
    def get_provider_data(cls, validated_data, all_data):
        """
        Takes a dict of values provided by the user (most likely from the
        request data) and returns a new dict of info that's specific to
        the provider type you're implementing. The returned dict will be
        used in the yaml config written for salt cloud.

        `files` is a list of files that might have been uploaded to the
        API that is available at this time. Each provider implementation
        must make sure that any files are written to disk and referenced
        properly in the result dict for salt cloud.

        See Salt Cloud documentation for more info on what needs to be in
        this return dict for each provider.
        """
        raise NotImplementedError()

    def validate_provider_data(self, serializer_attrs, all_data):
        """
        Checks that the keys defined in `get_required_fields` are in the
        given `data` dict. This merely checks that they are there and the
        values aren't empty. Override for any additional validation
        required.
        """
        errors = {}
        for key in self.get_required_fields():
            value = all_data.get(key)
            if not value:
                errors.setdefault(key, []).append(
                    '{0} is a required field.'.format(key)
                )

        if errors:
            raise ValidationError(errors)

        return serializer_attrs

    @classmethod
    def validate_image_id(cls, image_id):
        """
        Given an image_id, check that it exists and you have
        permissions to use it. It should a tuple:
            (boolean, string)
        where True means the image_id is available, and False
        means it does not. The string is the underlying error
        string if provided.
        """
        raise NotImplementedError()

    @classmethod
    def register_dns(cls, hosts):
        """
        Given a list of 'stacks.Host' objects, this method's
        implementation should handle the registration of DNS
        for the given cloud provider (e.g., Route53 on AWS)
        """
        raise NotImplementedError()

    @classmethod
    def unregister_dns(cls, hosts):
        """
        Given a list of 'stacks.Host' objects, this method's
        implementation should handle the de-registration of DNS
        for the given cloud provider (e.g., Route53 on AWS)
        """
        raise NotImplementedError()
