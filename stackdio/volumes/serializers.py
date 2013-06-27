import logging

from rest_framework import serializers

from .models import (
    Volume, 
)

logger = logging.getLogger(__name__)

class VolumeSerializer(serializers.HyperlinkedModelSerializer):
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
            'device',
            'mount_point',
        )
