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
    def get_provider_data(cls, data, files=None):
        yaml_data = {
            'provider': cls.SHORT_NAME,
            'identity_url': data[cls.IDENTITY_URL],
            'compute_name': data[cls.COMPUTE_NAME],
            'compute_region': data[cls.COMPUTE_REGION],
            'protocol': data[cls.PROTOCOL],
            'user': data[cls.USERNAME],
            'tenant': data[cls.TENANT_ID],
            'apikey': data[cls.API_KEY],
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
