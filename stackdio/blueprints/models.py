import json
import logging

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
)
from formulas.models import FormulaComponent

PROTOCOL_CHOICES = [
    ('tcp', 'TCP'),
    ('udp', 'UDP'),
    ('icmp', 'ICMP'),
]

logger = logging.getLogger(__name__)


class BlueprintManager(models.Manager):
    @transaction.commit_on_success
    def create(self, owner, data):
        '''
        data is a JSON object that looks something like:

        {
            "title": "Test Blueprint",
            "description": "Testing and stuff...",
            "properties": [
                {
                    "name": "property1",
                    "value": "value1"
                },
                {
                    "name": "property2",
                    "value": "value2"
                }
            ],
            "hosts": [
                {
                    "count": 1,
                    "size": 1,         # what instance_size object to use
                    "pattern": "foo",  # the naming pattern for the host's
                                            # hostname, in this case the hostname
                                            # would become 'foo-1'
                    "cloud_profile": 1,     # what cloud_profile object to use
                    "access_rules": [
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
                        }
                    ],
                    "formula_components": [1,2,3...]  # formula components to attach to this host
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
                               owner=owner)
        blueprint.save()

        # create properties
        for prop in data.get('properties', []):
            blueprint.properties.create(name=prop['name'], value=prop['value'])

        # create corresonding hosts and related models
        for host in data['hosts']:
            profile_obj = CloudProfile.objects.get(pk=host['cloud_profile'])
            size_obj = CloudInstanceSize.objects.get(pk=host['size'])
            zone_obj = CloudZone.objects.get(pk=host['zone'])
            host_obj = blueprint.host_definitions.create(
                count=host['count'],
                prefix=host['prefix'],
                cloud_profile=profile_obj,
                size=size_obj,
                zone=zone_obj,
            )

            # formula components
            for component_id in host['formula_components']:
                component_obj = FormulaComponent.objects.get(
                    pk=component_id,
                    formula__owner=owner)
                host_obj.formula_components.add(component_obj)

            for access_rule in host.get('access_rules', []):
                host_obj.access_rules.create(
                    protocol=access_rule['protocol'],
                    from_port=access_rule['from_port'],
                    to_port=access_rule['to_port'],
                    rule=access_rule['rule']
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

    # owner of the blueprint
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blueprints')

    # Use our custom manager object
    objects = BlueprintManager()

    def __unicode__(self):
   		return u'{0} (id={1})'.format(self.title, self.id)

    @property
    def property_count(self):
        return self.properties.count()

    @property
    def host_definition_count(self):
        return self.host_definitions.count()


class BlueprintHostDefinition(TimeStampedModel):

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

    # The default prefix this host definition should use. These will
    # be used when registering with DNS when a Stack is launched
    prefix = models.CharField(max_length=64)

    # The default instance size for the host
    size = models.ForeignKey('cloud.CloudInstanceSize')

    # The default availability zone for the host
    zone = models.ForeignKey('cloud.CloudZone')

    # What Salt formula components need to be installed by default 
    formula_components = models.ManyToManyField('formulas.FormulaComponent')

    @property
    def formula_components_count(self):
        return self.formula_components.count()

    def __unicode__(self):
        return u'{0} ({1})'.format(
            self.prefix,
            self.blueprint
        )


class BlueprintProperty(TimeStampedModel):
    '''
    Properties are a way for users to override pillar variables
    without modifying the pillar files directly or updating
    the SLS to hardcode parameters.
    '''

    class Meta:
        unique_together = ('blueprint', 'name')
        verbose_name_plural = 'properties'

    # The blueprint object this property applies to
    blueprint = models.ForeignKey('blueprints.Blueprint',
                                  related_name='properties')

    # The name of the property
    name = models.CharField(max_length=255)

    # The value of the property
    value = models.CharField(max_length=255)

    def __unicode__(self):
        return u'{0}:{1}'.format(
            self.name,
            self.value
        )


class BlueprintAccessRule(TimeStampedModel):
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
