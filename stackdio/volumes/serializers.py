import logging

from rest_framework import serializers

from .models import (
    Volume, 
)

logger = logging.getLogger(__name__)

class VolumeSerializer(serializers.HyperlinkedModelSerializer):

    snapshot_id = serializers.Field(source='snapshot.id')
    snapshot_name = serializers.Field(source='snapshot.snapshot_id')

    class Meta:
        model = Volume
        fields = (
            'id',
            'url',
            'volume_id',
            'attach_time',
            'user',
            'host',
            'snapshot',
            'snapshot_id',
            'snapshot_name',
            'device',
            'mount_point',
        )
