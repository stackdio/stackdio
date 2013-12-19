import json
import logging
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from core.fields import DeletingFileField
from cloud.models import (
    CloudProfile,
    CloudInstanceSize,
    CloudZone,
    Snapshot
)
from formulas.models import FormulaComponent

PROTOCOL_CHOICES = [
    ('tcp', 'TCP'),
    ('udp', 'UDP'),
    ('icmp', 'ICMP'),
]

DEVICE_ID_CHOICES = [
    ('/dev/xvdj', '/dev/xvdj'),
    ('/dev/xvdk', '/dev/xvdk'),
    ('/dev/xvdl', '/dev/xvdl'),
    ('/dev/xvdm', '/dev/xvdm'),
    ('/dev/xvdn', '/dev/xvdn'),
]

logger = logging.getLogger(__name__)

def get_props_file_path(obj, filename):
    return "blueprints/{0}/{1}.props".format(obj.owner.username, obj.slug)


class BlueprintManager(models.Manager):
    @transaction.commit_on_success
    def create(self, owner, data):
        '''
        data is a JSON object that looks something like:

        {
            "title": "Test Blueprint",
            "description": "Testing and stuff...",
            "public": true | false,
            "properties": {
                "prop1": "value1",
                "foo": {
                    "bar": {
                        "prop2": "value2"
                    }
                }
            },
            "hosts": [
                {
                    "count": 1,
                    "size": 1,          # what instance_size id to use
                    "hostname_template": "foo-{user}-{index}",    # the naming pattern for the host's
                                        # hostname, template variables are
                                        # supported
                    "zone": 1,          # availability zone id
                    "cloud_profile": 1, # what cloud_profile id to use
                    "access_rules": [                                   # access rule configuration (optional)
                        {
                            "protocol": "tcp | udp | icmp",
                            "from_port": "1-65535 | -1 for icmp",
                            "to_port": "1-65535 | -1 for icmp",
                            "rule": "CIDR | owner_id:group (AWS only)"
                        },
                        {
                            "protocol": "tcp",
                            "from_port": "22",
                            "to_port": "22",
                            "rule": "0.0.0.0/0"
                        },
                        {
                        ...
                        more rules
                        ...
                        },
                    ],
                    "volumes": [                        # volume configuration (optional)
                        {
                            "device": "/dev/xvdj",
                            "mount_point": "/mnt/ebs1",
                            "snapshot": 1
                        },
                        {
                            "device": "/dev/xvdk",
                            "mount_point": "/mnt/ebs2",
                            "snapshot": 1
                        }
                    ],
                    "formula_components": [             # formula components to attach to this host
                        {"id": 1},                      # based on component id
                        {"title": "foo"},               # based on component title__icontains
                        {"id": 1, "order": 0}           # specific ordering of component provisioning
                    ],
                    "spot_config": {                    # spot instance configuration (optional)
                        "spot_price": 0.20
                    }
                },
                {
                    ...
                    more hosts
                    ...
                }
            ]
        }
        '''

        ##
        # validate incoming data
        ##
        blueprint = self.model(title=data['title'],
                               description=data['description'],
                               public=data.get('public', False),
                               owner=owner)
        blueprint.save()

        props_json = json.dumps(data.get('properties', {}), indent=4)
        if not blueprint.props_file:
            blueprint.props_file.save(blueprint.slug+'.props', ContentFile(props_json))
        else:
            with open(blueprint.props_file.path, 'w') as f:
                f.write(props_json)

        # create corresonding hosts and related models
        for host in data['hosts']:
            profile_obj = CloudProfile.objects.get(pk=host['cloud_profile'])
            size_obj = CloudInstanceSize.objects.get(pk=host['size'])
            zone_obj = CloudZone.objects.get(pk=host['zone'])
            spot_price = host.get('spot_config', {}).get('spot_price', None)
            formula_components = host.get('formula_components', [])
            if spot_price is not None:
                spot_price = Decimal(str(spot_price))
            host_obj = blueprint.host_definitions.create(
                title=host['title'],
                description=host.get('description', ''),
                count=host['count'],
                hostname_template=host['hostname_template'],
                cloud_profile=profile_obj,
                size=size_obj,
                zone=zone_obj,
                spot_price=spot_price,
            )

            # create extended formula components for the blueprint
            for component in formula_components:
                component_id = component.get('id')
                component_title = component.get('title')
                component_sls_path = component.get('sls_path')
                component_order = int(component.get('order', 0))

                d = {'formula__owner': owner}
                if component_id:
                    d['pk'] = component_id
                elif component_sls_path:
                    d['sls_path__iexact'] = component_sls_path
                elif component_title:
                    d['title__icontains'] = component_title
                component_obj = FormulaComponent.objects.get(**d)
                host_obj.formula_components.create(
                    component=component_obj,
                    order=component_order
                )

            # build out the access rules
            for access_rule in host.get('access_rules', []):
                host_obj.access_rules.create(
                    protocol=access_rule['protocol'],
                    from_port=access_rule['from_port'],
                    to_port=access_rule['to_port'],
                    rule=access_rule['rule']
                )

            # build out the volumes
            for volume in host.get('volumes', []):
                logger.debug(volume)
                host_obj.volumes.create(
                    device=volume['device'],
                    mount_point=volume['mount_point'],
                    snapshot=volume['snapshot']
                )

        return blueprint


class Blueprint(TimeStampedModel, TitleSlugDescriptionModel):
    '''
    Blueprints are a template of reusable configuration used to launch
    Stacks. The purpose to create a blueprint that encapsulates the
    functionality, software, etc you want in your infrastructure once
    and use it to repeatably create your infrastructure when needed.

    TODO: @params
    '''

    class Meta:
        unique_together = ('owner', 'title')

    # owner of the blueprint
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blueprints')

    # publicly available to other users?
    public = models.BooleanField(default=False)

    # storage for properties file
    props_file = DeletingFileField(
        max_length=255,
        upload_to=get_props_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    # Use our custom manager object
    objects = BlueprintManager()

    def __unicode__(self):
   		return u'{0} (id={1})'.format(self.title, self.id)

    @property
    def host_definition_count(self):
        return self.host_definitions.count()

    @property
    def properties(self):
        if not self.props_file:
            return {}
        with open(self.props_file.path) as f:
            return json.loads(f.read())


class BlueprintHostDefinition(TitleSlugDescriptionModel, TimeStampedModel):

    class Meta:
        verbose_name_plural = 'host definitions'

    # The blueprint object this host is owned by
    blueprint = models.ForeignKey('blueprints.Blueprint',
                                  related_name='host_definitions')

    # The cloud profile object this host should use when being
    # launched
    cloud_profile = models.ForeignKey('cloud.CloudProfile')

    # The default number of instances to launch for this host definition
    count = models.IntegerField()

    # The hostname template that will be used to generate the actual
    # hostname at launch time. Several template variables will be provided
    # when the template is rendered down to its final form
    hostname_template = models.CharField(max_length=64)

    # The default instance size for the host
    size = models.ForeignKey('cloud.CloudInstanceSize')

    # The default availability zone for the host
    zone = models.ForeignKey('cloud.CloudZone')

    # The spot instance price for this host. If null, spot
    # instances will not be used for this host.
    spot_price = models.DecimalField(max_digits=5,
                                     decimal_places=2,
                                     blank=True,
                                     null=True)

    @property
    def formula_components_count(self):
        return self.formula_components.count()

    def __unicode__(self):
        return self.title


class BlueprintHostFormulaComponent(TimeStampedModel):
    '''
    An extension of an existing FormulaComponent to add additional metadata
    for those components based on this blueprint. In particular, this is how
    we track the order in which the formula should be provisioned in a
    blueprint.
    '''

    class Meta:
        verbose_name_plural = 'formula components'
        ordering = ['order']

    # The formula component we're extending
    component = models.ForeignKey('formulas.FormulaComponent')

    # The host definition this extended formula component applies to
    host = models.ForeignKey('blueprints.BlueprintHostDefinition',
                             related_name='formula_components')

    # The order in which the component should be provisioned
    order = models.IntegerField(default=0)

    def __unicode__(self):
        return u'{0}:{1}'.format(
            self.component,
            self.host
        )


class BlueprintAccessRule(TitleSlugDescriptionModel, TimeStampedModel):
    '''
    Access rules are a white list of rules for a host that defines
    what protocols and ports are available for the corresponding
    machines at launch time. In other words, they define the
    firefall rules for the machine.
    '''

    class Meta:
        verbose_name_plural = 'access rules'

    # The host definition this access rule applies to
    host = models.ForeignKey('blueprints.BlueprintHostDefinition',
                             related_name='access_rules')

    # The protocol for the access rule. One of tcp, udp, or icmp
    protocol = models.CharField(max_length=4, choices=PROTOCOL_CHOICES)

    # The from and to ports define the range of ports to open for the
    # given protocol and rule string. To open a single port, the
    # from and to ports should be the same integer.
    from_port = models.IntegerField()
    to_port = models.IntegerField()

    # Rule is a string specifying the CIDR for what network has access
    # to the given protocl and ports. For AWS, you may also specify
    # a rule of the form "owner_id:security_group", that will authorize
    # access to the given security group owned by the owner_id's account
    rule = models.CharField(max_length=255)

    def __unicode__(self):
        return u'{0} {1}-{2} {3}'.format(
            self.protocol,
            self.from_port,
            self.to_port,
            self.rule
        )


class BlueprintVolume(TitleSlugDescriptionModel, TimeStampedModel):
    '''
    '''

    class Meta:
        verbose_name_plural = 'volumes'

    # The host definition this access rule applies to
    host = models.ForeignKey('blueprints.BlueprintHostDefinition',
                             related_name='volumes')

    # The device that the volume should be attached to when a stack is created
    device = models.CharField(max_length=32, choices=DEVICE_ID_CHOICES)

    # Where the volume will be mounted after created and attached
    mount_point = models.CharField(max_length=64)

    # The snapshot ID to create the volume from
    snapshot = models.ForeignKey('cloud.Snapshot',
                                 related_name='host_definitions')

    def __unicode__(self):
        return u'BlueprintVolume: {0}'.format(self.pk)

