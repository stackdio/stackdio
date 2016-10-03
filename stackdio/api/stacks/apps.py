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

from django.apps import AppConfig


class StackdioStacksAppConfig(AppConfig):
    name = 'stackdio.api.stacks'
    label = 'stacks'

    def ready(self):
        # Do the actstram registration
        from actstream import registry
        registry.register(self.get_model('Stack'))
        registry.register(self.get_model('Host'))
        registry.register(self.get_model('StackCommand'))

        # Do the notifications registration
        from stackdio.core.notifications import registry as notifications_registry
        from .serializers import StackSerializer, StackCommandSerializer
        notifications_registry.register(self.get_model('Stack'),
                                        StackSerializer,
                                        'ui:stack-detail')
        notifications_registry.register(self.get_model('StackCommand'),
                                        StackCommandSerializer,
                                        'ui:stack-command-detail')
