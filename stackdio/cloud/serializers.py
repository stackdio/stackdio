import logging

from rest_framework import serializers

from formulas.serializers import FormulaComponentSerializer
from core.mixins import SuperuserFieldsMixin
from . import models
from .utils import get_provider_type_and_class

from rest_framework import permissions

logger = logging.getLogger(__name__)


class SecurityGroupSerializer(SuperuserFieldsMixin,
                              serializers.HyperlinkedModelSerializer):
    ##
    # Read-only fields.
    ##
    group_id = serializers.Field()
    owner = serializers.Field()

    # Field for showing the number of active hosts using this security
    # group. It is pulled automatically from the model instance method.
    active_hosts = serializers.Field(source='get_active_hosts')

    # Rules are defined in two places depending on the object we're dealing
    # with. If it's a QuerySet the rules are pulled in one query to the
    # cloud provider using the SecurityGroupQuerySet::with_rules method.
    # For single, detail objects we use the rules instance method on the
    # SecurityGroup object
    rules = serializers.Field(source='rules')
    provider_id = serializers.Field(source='cloud_provider.id')

    rules_url = serializers.HyperlinkedIdentityField(
            view_name='securitygroup-rules')

    class Meta:
        model = models.SecurityGroup
        fields = (
            'id',
            'url',
            'name',
            'description',
            'rules_url',
            'group_id',
            'cloud_provider',
            'provider_id',
            'owner',
            'is_default',
            'is_managed',
            'active_hosts',
            'rules',
        )
        superuser_fields = ('owner', 'is_default', 'is_managed')


class SecurityGroupRuleSerializer(serializers.Serializer):
    action = serializers.CharField(max_length=15)
    protocol = serializers.CharField(max_length=4)
    from_port = serializers.IntegerField()
    to_port = serializers.IntegerField()
    rule = serializers.CharField(max_length=255)


class CloudProviderSerializer(SuperuserFieldsMixin,
                              serializers.HyperlinkedModelSerializer):
    yaml = serializers.Field()
    provider_type = serializers.PrimaryKeyRelatedField()
    default_availability_zone = serializers.PrimaryKeyRelatedField(
        required=False)
    provider_type_name = serializers.Field(source='provider_type.type_name')
    security_groups = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-securitygroup-list')
    vpc_subnets = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-vpcsubnet-list')
    global_orchestration_components = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-global-orchestration-list')
    global_orchestration_properties = serializers.HyperlinkedIdentityField(
        view_name='cloudprovider-global-orchestration-properties')

    class Meta:
        model = models.CloudProvider
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'provider_type',
            'provider_type_name',
            'account_id',
            'default_availability_zone',
            'yaml',
            'vpc_id',
            'security_groups',
            'vpc_subnets',
            'global_orchestration_components',
            'global_orchestration_properties',
        )

        superuser_fields = ('yaml',)

    def validate(self, attrs):
        # validate provider specific request data
        request = self.context['request']

        # patch requests only accept a few things for modification
        if request.method == 'PATCH':
            fields_available = ('title',
                                'description',
                                'default_availability_zone')

            errors = {}
            for k in request.DATA:
                if k not in fields_available:
                    errors.setdefault(k, []).append(
                        'Field may not be modified.')
            if errors:
                logger.debug(errors)
                raise serializers.ValidationError(errors)

        elif request.method == 'POST':

            provider_type, provider_class = get_provider_type_and_class(
                request.DATA.get('provider_type'))

            # pull the availability zone name
            zone = request.DATA.get('default_availability_zone')
            if zone:
                try:
                    zone = models.CloudZone.objects.get(pk=zone)
                    request.DATA['default_availability_zone_name'] = zone.slug
                except models.CloudZone.DoesNotExist:
                    errors = [
                        'Could not look up availability zone. Did you give '
                        'a valid id?'
                    ]
                    raise serializers.ValidationError({'errors': errors})

            provider = provider_class()
            errors = provider.validate_provider_data(request.DATA,
                                                     request.FILES)

            if errors:
                logger.error('Cloud provider validation errors: '
                             '{0}'.format(errors))
                raise serializers.ValidationError(errors)

        return attrs


class CloudProviderTypeSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.Field(source='get_type_name_display')

    class Meta:
        model = models.CloudProviderType
        fields = (
            'id',
            'url',
            'title',
            'type_name',
        )


class CloudInstanceSizeSerializer(serializers.HyperlinkedModelSerializer):
    provider_type = serializers.Field(source='provider_type')

    class Meta:
        model = models.CloudInstanceSize
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'provider_type',
            'instance_id',
        )


class GlobalOrchestrationFormulaComponentSerializer(
        serializers.HyperlinkedModelSerializer):

    def __init__(self, *args, **kwargs):
        super(GlobalOrchestrationFormulaComponentSerializer, self) \
            .__init__(*args, **kwargs)

        # If read request, put in the component object, otherwise just pk
        context = kwargs.get('context')
        if context:
            request = context.get('request')
            if request and request.method in permissions.SAFE_METHODS:
                self.fields['component'] = FormulaComponentSerializer()

    class Meta:
        model = models.GlobalOrchestrationFormulaComponent
        fields = (
            'id',
            'url',
            'order',
            'component',
        )


class CloudProfileSerializer(SuperuserFieldsMixin,
                             serializers.HyperlinkedModelSerializer):
    cloud_provider = serializers.PrimaryKeyRelatedField()
    default_instance_size = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = models.CloudProfile
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'cloud_provider',
            'image_id',
            'default_instance_size',
            'ssh_user',
        )

        superuser_fields = ('image_id',)

    # TODO: Ignoring code complexity issues
    def validate(self, attrs):  # NOQA
        # validate provider specific request data
        request = self.context['request']

        # patch requests only accept a few things for modification
        if request.method in ('PATCH', 'PUT'):
            fields_available = ('title',
                                'description',
                                'default_instance_size',
                                'ssh_user',)

            errors = {}
            for k in request.DATA:
                if k not in fields_available:
                    errors.setdefault(k, []).append(
                        'Field may not be modified.')
            if errors:
                logger.debug(errors)
                raise serializers.ValidationError(errors)

        elif request.method == 'POST':
            image_id = request.DATA.get('image_id')
            provider_id = request.DATA.get('cloud_provider')
            if not provider_id:
                raise serializers.ValidationError({
                    'cloud_provider': 'Required field.'
                })

            provider = models.CloudProvider.objects.get(pk=provider_id)
            driver = provider.get_driver()

            valid, exc_msg = driver.validate_image_id(image_id)
            if not valid:
                raise serializers.ValidationError({
                    'image_id': ['Image ID does not exist on the given cloud '
                                 'provider. Check that it exists and you have '
                                 'access to it.'],
                    'image_id_exception': [exc_msg]
                })

        return attrs


class SnapshotSerializer(serializers.HyperlinkedModelSerializer):
    cloud_provider = serializers.PrimaryKeyRelatedField()
    default_instance_size = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = models.Snapshot
        fields = (
            'id',
            'url',
            'title',
            'slug',
            'description',
            'cloud_provider',
            'snapshot_id',
            'size_in_gb',
            'filesystem_type',
        )

    def validate(self, attrs):
        request = self.context['request']

        # validate that the snapshot exists by looking it up in the cloud
        # provider
        provider_id = request.DATA.get('cloud_provider')
        driver = models.CloudProvider.objects.get(pk=provider_id).get_driver()

        result, error = driver.has_snapshot(request.DATA['snapshot_id'])
        if not result:
            raise serializers.ValidationError({'errors': [error]})
        return attrs


class CloudZoneSerializer(serializers.HyperlinkedModelSerializer):
    provider_type = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = models.CloudZone
        fields = (
            'id',
            'title',
            'provider_type',
        )


class VPCSubnetSerializer(serializers.Serializer):
    vpc_id = serializers.Field()
    id = serializers.Field()
    availability_zone = serializers.Field()
    cidr_block = serializers.Field()
    tags = serializers.Field()
