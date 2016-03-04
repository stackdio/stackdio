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


"""
Rackspace provider for stackd.io
"""

import logging

from stackdio.api.cloud.providers.base import BaseCloudProvider

logger = logging.getLogger(__name__)


##
# Required parameters that must be defined
##

class RackspaceCloudProvider(BaseCloudProvider):
    # Notice we're using openstack as the shortname here, as this is
    # the appropriate provider type for dealing with Rackspace
    SHORT_NAME = 'openstack'
    LONG_NAME = 'Rackspace'

    # Identity URL
    IDENTITY_URL = 'identity_url'

    # Compute name
    COMPUTE_NAME = 'compute_name'

    # Compute region
    COMPUTE_REGION = 'compute_region'

    # Protocol
    PROTOCOL = 'protocol'

    # Authentication
    USERNAME = 'username'
    TENANT_ID = 'tenant_id'
    API_KEY = 'api_key'

    @classmethod
    def get_provider_data(cls, validated_data, all_data):
        yaml_data = {
            'provider': cls.SHORT_NAME,
            'identity_url': validated_data[cls.IDENTITY_URL],
            'compute_name': validated_data[cls.COMPUTE_NAME],
            'compute_region': validated_data[cls.COMPUTE_REGION],
            'protocol': validated_data[cls.PROTOCOL],
            'user': validated_data[cls.USERNAME],
            'tenant': validated_data[cls.TENANT_ID],
            'apikey': validated_data[cls.API_KEY],
        }

        return yaml_data

    @classmethod
    def get_required_fields(cls):
        return [
            cls.IDENTITY_URL,
            cls.COMPUTE_NAME,
            cls.COMPUTE_REGION,
            cls.PROTOCOL,
            cls.USERNAME,
            cls.TENANT_ID,
            cls.API_KEY,
        ]

    @classmethod
    def register_dns(cls, hosts):
        pass

    @classmethod
    def unregister_dns(cls, hosts):
        pass

    @classmethod
    def validate_image_id(cls, image_id):
        pass
