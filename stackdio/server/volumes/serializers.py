import logging

from rest_framework import serializers

from .models import (
    Volume, 
)

logger = logging.getLogger(__name__)


class VolumeSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.Field()
    snapshot_name = serializers.Field(source='snapshot.snapshot_id')
    size_in_gb = serializers.Field(source='snapshot.size_in_gb')

    class Meta:
        model = Volume
        fields = (
            'id',
            'url',
            'owner',
            'volume_id',
            'attach_time',
            'stack',
            'hostname',
            'host',
            'snapshot',
            'snapshot_name',
            'size_in_gb',
            'device',
            'mount_point',
        )
