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

from .models import NotificationChannel


def add_subscribed_channels(model_cls):

    def get_subscribed_channels(self):
        return NotificationChannel.objects.filter(subscribed_object=self)

    model_cls.subscribed_channels = property(get_subscribed_channels)

    return model_cls
