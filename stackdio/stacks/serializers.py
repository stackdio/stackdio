import logging

from rest_framework import serializers

from . import models
from blueprints.serializers import BlueprintHostFormulaComponentSerializer

logger = logging.getLogger(__name__)


class StackPropertiesSerializer(serializers.Serializer):
    def to_native(self, obj):
        if obj is not None:
            return obj.properties
        return {}


class HostSerializer(serializers.HyperlinkedModelSerializer):
    availability_zone = serializers.PrimaryKeyRelatedField()
    formula_components = BlueprintHostFormulaComponentSerializer(many=True)

    class Meta:
        model = models.Host
        fields = (
            'id',
            'url',
            'hostname',
            'provider_dns',
            'fqdn',
            'state',
            'status',
            'status_detail',
            'availability_zone',
            'created',
            'sir_id',
            'sir_price',
            'formula_components',
        )


class StackHistorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = models.StackHistory
        fields = (
            'event',
            'status',
            'level',
            'created'
        )


class StackSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.Field()
    hosts = serializers.HyperlinkedIdentityField(view_name='stack-hosts')
    fqdns = serializers.HyperlinkedIdentityField(view_name='stack-fqdns')
    host_count = serializers.Field(source='hosts.count')
    volumes = serializers.HyperlinkedIdentityField(view_name='stack-volumes')
    volume_count = serializers.Field(source='volumes.count')
    properties = serializers.HyperlinkedIdentityField(
        view_name='stack-properties')
    #history = StackHistorySerializer(many=True)
    history = serializers.HyperlinkedIdentityField(
        view_name='stack-history')

    class Meta:
        model = models.Stack
        fields = (
            'id',
            'title',
            'description',
            'url',
            'owner',
            'namespace',
            'host_count',
            'volume_count',
            'created',
            'blueprint',
            'fqdns',
            'hosts',
            'volumes',
            'properties',
            'history',
        )
