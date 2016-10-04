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

import boto3

from stackdio.core.notifiers.base import BaseNotifier, abstractmethod


class Boto3Notifier(BaseNotifier):

    needs_verification = False

    def __init__(self, aws_access_key, aws_secret_key, region, resource_name):
        super(Boto3Notifier, self).__init__()
        session = boto3.Session(aws_access_key_id=aws_access_key,
                                aws_secret_access_key=aws_secret_key,
                                region_name=region)
        self.resource = session.resource(resource_name)

    # Still mark this as abstract
    @abstractmethod
    def send_notification(self, notification):
        raise NotImplementedError()


class SNSNotifier(Boto3Notifier):

    def __init__(self, **kwargs):
        kwargs['resource_name'] = 'sns'
        super(SNSNotifier, self).__init__(**kwargs)

    def send_notification(self, notification):
        pass
