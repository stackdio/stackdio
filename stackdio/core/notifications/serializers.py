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

from django.db import transaction
from rest_framework import serializers

from stackdio.core.serializers import EventField, StackdioHyperlinkedModelSerializer
from stackdio.core.utils import recursive_update
from . import models, utils, validators

logger = logging.getLogger(__name__)


def validate_notifier(value):
    if value not in utils.get_notifier_list():
        raise serializers.ValidationError('No notifier named {}'.format(value))


class NotifierSerializer(serializers.Serializer):

    name = serializers.CharField()
    backend = serializers.CharField(source='class_path')


class NotificationHandlerSerializer(serializers.HyperlinkedModelSerializer):

    options = serializers.JSONField()

    class Meta:
        model = models.NotificationHandler

        fields = (
            'notifier',
            'options',
        )

        extra_kwargs = {
            'notifier': {'validators': [validate_notifier]}
        }

    def validate(self, attrs):
        notifier_cls = utils.get_notifier_class(attrs['notifier'])
        required_options = notifier_cls.get_required_options()

        received_options = attrs.get('options', {})

        missing_options = []
        for option in required_options:
            if option not in received_options:
                missing_options.append(option)

        if missing_options:
            raise serializers.ValidationError({
                'options': ['Missing the following options: {}'.format(', '.join(missing_options))]
            })

        return attrs

    def update(self, instance, validated_data):
        """
        Need to override this so we can add custom logic for PUT vs PATCH
        """
        if self.partial:
            # This is a PATCH request - so merge the new options into the old ones
            new_options = validated_data.get('options', {})

            validated_data['options'] = recursive_update(instance.options, new_options)

        return super(NotificationHandlerSerializer, self).update(instance, validated_data)


class SubscriberNotificationChannelSerializer(StackdioHyperlinkedModelSerializer):

    events = EventField(many=True, read_only=True)

    handlers = NotificationHandlerSerializer(many=True, read_only=True)

    action = serializers.ChoiceField(('add', 'remove'), write_only=True)

    class Meta:
        model = models.NotificationChannel
        lookup_field = 'name'

        app_label = 'users'
        model_name = 'currentuser-channel'

        fields = (
            'action',
            'url',
            'name',
            'events',
            'handlers',
        )

        extra_kwargs = {
            'name': {'validators': [validators.ChannelExistsValidator()]},
        }

    def save(self, **kwargs):
        queryset = self.Meta.model.objects.filter(auth_object=kwargs['auth_object'])

        # Just get the channel
        channel = queryset.get(name=self.validated_data['name'])

        action = self.validated_data['action']

        # Either add or remove the subscribed object depending on the action
        if action == 'add':
            channel.add_subscriber(kwargs['subscribed_object'])
        elif action == 'remove':
            channel.remove_subscriber(kwargs['subscribed_object'])

        # DRF gets angry if this is missing
        self.instance = channel

        return channel


class NotificationChannelSerializer(StackdioHyperlinkedModelSerializer):

    events = EventField(many=True, required=True)

    handlers = NotificationHandlerSerializer(many=True, required=True)

    class Meta:
        model = models.NotificationChannel
        lookup_field = 'name'

        fields = (
            'url',
            'name',
            'events',
            'handlers',
        )

        extra_kwargs = {
            'name': {'validators': [validators.UniqueChannelValidator()]},
        }

    def create(self, validated_data):
        # Grab the handlers
        handlers = validated_data.pop('handlers')

        with transaction.atomic(using=models.NotificationChannel.objects.db):
            # Create the channel
            channel = super(NotificationChannelSerializer, self).create(validated_data)

            # Create the handlers
            for handler in handlers:
                handler['channel'] = channel
            self.fields['handlers'].create(handlers)

        return channel

    def update(self, instance, validated_data):
        # Grab the handlers
        handlers = validated_data.pop('handlers', [])

        with transaction.atomic(using=models.NotificationChannel.objects.db):
            # Update the channel
            channel = super(NotificationChannelSerializer, self).update(instance, validated_data)

            # Update the handlers
            if self.partial:
                # This is a PATCH request
                pass
            else:
                # This is a PUT request

                # delete all the handlers first
                for handler in channel.handlers.all():
                    handler.delete()

                # Then recreate them
                for handler in handlers:
                    handler['channel'] = channel
                self.fields['handlers'].create(handlers)

        return channel


class AbstractNotificationSerializer(serializers.ModelSerializer):
    """
    This is abstract, it won't work on purpose.
    """

    event = EventField()

    object_type = serializers.CharField(source='content_type.name')

    class Meta:
        model = models.Notification

        fields = (
            'event',
            # 'timestamp',
            'object_type',
            'object',
        )
