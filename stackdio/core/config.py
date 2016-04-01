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
from __future__ import print_function

import os

import yaml
from django.core.exceptions import ImproperlyConfigured


class StackdioConfig(dict):
    CONFIG_FILE = os.path.expanduser('~/.stackdio/config')
    REQUIRED_FIELDS = (
        'user',
        'db_dsn',
        'storage_root',
        'django_secret_key',
        'create_ssh_users',
        'salt_bootstrap_args',
    )

    def __init__(self):
        super(StackdioConfig, self).__init__()
        self._load_stackdio_config()

    def _load_stackdio_config(self):
        if not os.path.isfile(self.CONFIG_FILE):
            raise ImproperlyConfigured(
                'Missing stackdio configuration file. To create the file, you '
                'may use `stackdio init`')
        with open(self.CONFIG_FILE) as f:
            config = yaml.safe_load(f)

        if not config:
            raise ImproperlyConfigured(
                'stackdio configuration file appears to be empty or not '
                'valid yaml.')

        errors = []
        for k in self.REQUIRED_FIELDS:
            if k not in config:
                errors.append('Missing parameter `{0}`'.format(k))

        if errors:
            msg = 'stackdio configuration errors:\n'
            for err in errors:
                msg += '  - {0}\n'.format(err)
            raise ImproperlyConfigured(msg)

        self.update(config)

        # additional helper attributes
        self.salt_root = os.path.join(self.storage_root)
        self.salt_config_root = os.path.join(self.salt_root, 'etc', 'salt')
        self.salt_master_config = os.path.join(self.salt_config_root, 'master')
        self.salt_cloud_config = os.path.join(self.salt_config_root, 'cloud')
        self.salt_core_states = os.path.join(self.storage_root, 'core_states')
        self.salt_providers_dir = os.path.join(self.salt_config_root,
                                               'cloud.providers.d')
        self.salt_profiles_dir = os.path.join(self.salt_config_root,
                                              'cloud.profiles.d')

        if '{salt_version}' not in self.salt_bootstrap_args:
            raise ImproperlyConfigured('salt_bootstrap_args must contain `{salt_version}`')

        # defaults
        if not self.salt_master_log_level:  # pylint: disable=access-member-before-definition
            self.salt_master_log_level = 'info'

    def __getattr__(self, k):
        return self.get(k)

    def __setattr__(self, k, v):
        self[k] = v

if __name__ == '__main__':
    config = StackdioConfig()
    print(config.user)
