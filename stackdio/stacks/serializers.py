import logging

from rest_framework import serializers

from . import models
from blueprints.serializers import BlueprintHostFormulaComponentSerializer
from cloud.serializers import SecurityGroupSerializer

logger = logging.getLogger(__name__)


class StackPropertiesSerializer(serializers.Serializer):
    def to_native(self, obj):
        if obj is not None:
            return obj.properties
        return {}


class HostSerializer(serializers.HyperlinkedModelSerializer):
    availability_zone = serializers.PrimaryKeyRelatedField()
    subnet_id = serializers.Field()
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
            'subnet_id',
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
    action = serializers.HyperlinkedIdentityField(view_name='stack-action')
    logs = serializers.HyperlinkedIdentityField(view_name='stack-logs')
    orchestration_errors = serializers.HyperlinkedIdentityField(
        view_name='stack-orchestration-errors')
    provisioning_errors = serializers.HyperlinkedIdentityField(
        view_name='stack-provisioning-errors')
    host_count = serializers.Field(source='hosts.count')
    volumes = serializers.HyperlinkedIdentityField(view_name='stack-volumes')
    volume_count = serializers.Field(source='volumes.count')
    properties = serializers.HyperlinkedIdentityField(
        view_name='stack-properties')
    history = serializers.HyperlinkedIdentityField(
        view_name='stack-history')
    access_rules = serializers.HyperlinkedIdentityField(
        view_name='stack-access-rules')
    security_groups = serializers.HyperlinkedIdentityField(
        view_name='stack-security-groups')

    class Meta:
        model = models.Stack
        fields = (
            'id',
            'title',
            'description',
            'public',
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
            'action',
            'access_rules',
            'security_groups',
            'logs',
            'orchestration_errors',
            'provisioning_errors',
        )

class StackSecurityGroupSerializer(SecurityGroupSerializer):
    pass

#class AccessRuleSerializer(serializers.HyperlinkedModelSerializer):
#
#    stack = serializers.HyperlinkedRelatedField(read_only=True, 
#                                            view_name='stack-detail')
#
#    class Meta:
#        model = models.StackAccessRule
#        view_name = 'access-rule-detail'
#        fields = (
#            'id',
#            'url',
#            'stack',
#            'protocol',
#            'from_port',
#            'to_port',
#            'rule',
#        )
