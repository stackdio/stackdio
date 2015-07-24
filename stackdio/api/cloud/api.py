# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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

from rest_framework import generics
from rest_framework.compat import OrderedDict
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from stackdio.api.blueprints.models import Blueprint
from stackdio.api.cloud.providers.base import DeleteGroupException
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.core.permissions import StackdioModelPermissions, StackdioObjectPermissions
from stackdio.core.utils import FakeQuerySet
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)
from . import filters, mixins, models, serializers, permissions

logger = logging.getLogger(__name__)


class CloudRootView(APIView):
    """
    Root of the cloud API. Below are all of the cloud API endpoints that
    are currently accessible. Each API will have its own documentation
    and particular parameters that may discoverable by browsing directly
    to them.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        api = OrderedDict((
            ('providers', reverse('cloudprovider-list',
                                  request=request,
                                  format=format)),
            ('accounts', reverse('cloudaccount-list',
                                 request=request,
                                 format=format)),
            ('profiles', reverse('cloudprofile-list',
                                 request=request,
                                 format=format)),
            ('snapshots', reverse('snapshot-list',
                                  request=request,
                                  format=format)),
            ('security_groups', reverse('securitygroup-list',
                                        request=request,
                                        format=format)),
        ))

        return Response(api)


class CloudProviderListAPIView(generics.ListAPIView):
    queryset = models.CloudProvider.objects.all()
    serializer_class = serializers.CloudProviderSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    lookup_field = 'name'


class CloudProviderDetailAPIView(generics.RetrieveAPIView):
    queryset = models.CloudProvider.objects.all()
    serializer_class = serializers.CloudProviderSerializer
    permission_classes = (StackdioObjectPermissions,)
    lookup_field = 'name'


class CloudProviderObjectUserPermissionsViewSet(mixins.CloudProviderRelatedMixin,
                                                StackdioObjectUserPermissionsViewSet):
    permission_classes = (permissions.CloudProviderPermissionsObjectPermissions,)
    parent_lookup_field = 'name'


class CloudProviderObjectGroupPermissionsViewSet(mixins.CloudProviderRelatedMixin,
                                                 StackdioObjectGroupPermissionsViewSet):
    permission_classes = (permissions.CloudProviderPermissionsObjectPermissions,)
    parent_lookup_field = 'name'


class CloudAccountListAPIView(generics.ListCreateAPIView):
    queryset = models.CloudAccount.objects.all()
    serializer_class = serializers.CloudAccountSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.CloudAccountFilter


class CloudAccountDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.CloudAccount.objects.all()
    serializer_class = serializers.CloudAccountSerializer
    permission_classes = (StackdioObjectPermissions,)

    def perform_destroy(self, instance):
        # check for profiles using this account before deleting
        profiles = [p.slug for p in instance.profiles.all()]
        if profiles:
            raise ValidationError({
                'detail': 'One or more profiles are making use of this account.',
                'profiles': profiles,
            })

        # ask the driver to clean up after itself since it's no longer needed
        driver = instance.get_driver()
        driver.destroy()

        instance.delete()


class CloudAccountModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    permission_classes = (permissions.CloudAccountPermissionsModelPermissions,)
    model_cls = models.CloudAccount


class CloudAccountModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    permission_classes = (permissions.CloudAccountPermissionsModelPermissions,)
    model_cls = models.CloudAccount


class CloudAccountObjectUserPermissionsViewSet(mixins.CloudAccountRelatedMixin,
                                               StackdioObjectUserPermissionsViewSet):
    permission_classes = (permissions.CloudAccountPermissionsObjectPermissions,)


class CloudAccountObjectGroupPermissionsViewSet(mixins.CloudAccountRelatedMixin,
                                                StackdioObjectGroupPermissionsViewSet):
    permission_classes = (permissions.CloudAccountPermissionsObjectPermissions,)


class GlobalOrchestrationComponentListAPIView(mixins.CloudAccountRelatedMixin,
                                              generics.ListCreateAPIView):
    serializer_class = serializers.GlobalOrchestrationFormulaComponentSerializer

    def get_queryset(self):
        return self.get_cloudaccount().global_formula_components.all()

    def perform_create(self, serializer):
        serializer.save(account=self.get_cloudaccount())

    def create(self, request, *args, **kwargs):
        component_id = request.DATA.get('component')
        try:
            # Delete an existing component if there is one
            component = self.get_queryset().get(component__id=component_id)
            component.delete()
        except models.GlobalOrchestrationFormulaComponent.DoesNotExist:
            pass

        return super(GlobalOrchestrationComponentListAPIView, self).create(request, *args, **kwargs)


class GlobalOrchestrationComponentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.GlobalOrchestrationFormulaComponent.objects.all()
    serializer_class = serializers.GlobalOrchestrationFormulaComponentSerializer
    permission_classes = (StackdioObjectPermissions,)


class GlobalOrchestrationPropertiesAPIView(mixins.CloudAccountRelatedMixin,
                                           generics.RetrieveUpdateAPIView):
    queryset = models.CloudAccount.objects.all()
    serializer_class = serializers.GlobalOrchestrationPropertiesSerializer


class CloudAccountVPCSubnetListAPIView(mixins.CloudAccountRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.VPCSubnetSerializer

    def get_queryset(self):
        account = self.get_cloudaccount()
        driver = account.get_driver()
        # Grab the subnets from the driver
        subnets = driver.get_vpc_subnets()
        # Sort them by name
        return sorted(subnets, key=lambda s: s.tags.get('Name'))


class CloudAccountFormulaVersionsAPIView(mixins.CloudAccountRelatedMixin,
                                         generics.ListCreateAPIView):
    serializer_class = FormulaVersionSerializer

    def get_queryset(self):
        account = self.get_cloudaccount()
        return account.formula_versions.all()

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_cloudaccount())


class CloudProfileListAPIView(generics.ListCreateAPIView):
    queryset = models.CloudProfile.objects.all()
    serializer_class = serializers.CloudProfileSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.CloudProfileFilter

    def perform_create(self, serializer):
        obj = serializer.save()
        obj.update_config()


class CloudProfileDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.CloudProfile.objects.all()
    serializer_class = serializers.CloudProfileSerializer
    permission_classes = (StackdioObjectPermissions,)

    def perform_destroy(self, instance):
        # check for blueprint usage before deleting
        blueprints = Blueprint.objects.filter(host_definition__cloud_profile=instance).distinct()

        if blueprints:
            raise ValidationError({
                'detail': 'One or more blueprints are making use of this '
                          'profile.',
                'blueprints': [b.title for b in blueprints],
            })

        instance.delete()


class CloudProfileModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    permission_classes = (permissions.CloudProfilePermissionsModelPermissions,)
    model_cls = models.CloudProfile


class CloudProfileModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    permission_classes = (permissions.CloudProfilePermissionsModelPermissions,)
    model_cls = models.CloudProfile


class CloudProfileObjectUserPermissionsViewSet(mixins.CloudProfileRelatedMixin,
                                               StackdioObjectUserPermissionsViewSet):
    permission_classes = (permissions.CloudProfilePermissionsObjectPermissions,)


class CloudProfileObjectGroupPermissionsViewSet(mixins.CloudProfileRelatedMixin,
                                                StackdioObjectGroupPermissionsViewSet):
    permission_classes = (permissions.CloudProfilePermissionsObjectPermissions,)


class SnapshotListAPIView(generics.ListCreateAPIView):
    queryset = models.Snapshot.objects.all()
    serializer_class = serializers.SnapshotSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)


class SnapshotDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Snapshot.objects.all()
    serializer_class = serializers.SnapshotSerializer
    permission_classes = (StackdioObjectPermissions,)


class SnapshotModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    permission_classes = (permissions.SnapshotPermissionsModelPermissions,)
    model_cls = models.Snapshot


class SnapshotModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    permission_classes = (permissions.SnapshotPermissionsModelPermissions,)
    model_cls = models.Snapshot


class SnapshotObjectUserPermissionsViewSet(mixins.SnapshotRelatedMixin,
                                           StackdioObjectUserPermissionsViewSet):
    permission_classes = (permissions.SnapshotPermissionsObjectPermissions,)


class SnapshotObjectGroupPermissionsViewSet(mixins.SnapshotRelatedMixin,
                                            StackdioObjectGroupPermissionsViewSet):
    permission_classes = (permissions.SnapshotPermissionsObjectPermissions,)


class CloudInstanceSizeListAPIView(mixins.CloudProviderRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.CloudInstanceSizeSerializer
    filter_class = filters.CloudInstanceSizeFilter
    lookup_field = 'instance_id'

    def get_queryset(self):
        return models.CloudInstanceSize.objects.filter(provider=self.get_cloudprovider())


class CloudInstanceSizeDetailAPIView(mixins.CloudProviderRelatedMixin,
                                     generics.RetrieveAPIView):
    serializer_class = serializers.CloudInstanceSizeSerializer
    lookup_field = 'instance_id'

    def get_queryset(self):
        return models.CloudInstanceSize.objects.filter(provider=self.get_cloudprovider())


class CloudRegionListAPIView(mixins.CloudProviderRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.CloudRegionSerializer
    filter_class = filters.CloudRegionFilter
    lookup_field = 'title'

    def get_queryset(self):
        return models.CloudRegion.objects.filter(provider=self.get_cloudprovider())


class CloudRegionDetailAPIView(mixins.CloudProviderRelatedMixin, generics.RetrieveAPIView):
    serializer_class = serializers.CloudRegionSerializer
    lookup_field = 'title'

    def get_queryset(self):
        return models.CloudRegion.objects.filter(provider=self.get_cloudprovider())


class CloudRegionZoneListAPIView(mixins.CloudProviderRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.CloudZoneSerializer
    filter_class = filters.CloudZoneFilter

    def get_queryset(self):
        region = models.CloudRegion.objects.get(provider=self.get_cloudprovider(),
                                                title=self.kwargs.get('title'))
        return region.zones.all()


class CloudZoneListAPIView(mixins.CloudProviderRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.CloudZoneSerializer
    filter_class = filters.CloudZoneFilter
    lookup_field = 'title'

    def get_queryset(self):
        return models.CloudZone.objects.filter(region__provider=self.get_cloudprovider())


class CloudZoneDetailAPIView(mixins.CloudProviderRelatedMixin, generics.RetrieveAPIView):
    serializer_class = serializers.CloudZoneSerializer
    lookup_field = 'title'

    def get_queryset(self):
        return models.CloudZone.objects.filter(region__provider=self.get_cloudprovider())


class SecurityGroupListAPIView(generics.ListCreateAPIView):
    """
    Lists and creates new security groups.

    ### GET

    Retrieves all security groups owned by the authenticated user.
    The associated rules for each group will also be given in the
    `rules` attribute. The `active_hosts` field will also be
    updated to show the number of hosts known by stackd.io to be
    using the security group at this time, but please **note**
    that other machines in the cloud account could be using
    the same security group and stackd.io may not be aware.

    ### POST

    Creates a new security group given the following properties
    in the JSON request:

    `name` -- The name of the security group. This will also be
              used to create the security group on the account.

    `description` -- The description or purpose of the group.

    `account` -- The id of the cloud account to associate
                        this group with.

    `default` -- Boolean representing if this group, for this
                    account, is set to automatically be added
                    to all hosts launched on the account. **NOTE**
                    this property may only be set by an admin.
    """
    queryset = models.SecurityGroup.objects.all()
    serializer_class = serializers.SecurityGroupSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.SecurityGroupFilter


class SecurityGroupDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Shows the detail for a security group and allows for the default
    flag to be modified (for admins only.)

    ### GET

    Retrieves the detail for the security group as defined by its
    `pk` identifier in the URL. The associated `rules` and
    `active_hosts` fields will be populated like with the full
    list.

    ### PUT / PATCH

    Updates an existing security group's details. Currently, only
    the `default` field may be modified.

    ### DELETE

    Removes the corresponding security group from stackd.io, as well as
    from the underlying cloud account if `managed` is true.
    **NOTE** that if the security group is currently being used, then
    it can not be removed. You must first terminate all machines depending
    on the security group and then delete it.
    """

    queryset = models.SecurityGroup.objects.all()
    serializer_class = serializers.SecurityGroupSerializer
    permission_classes = (StackdioObjectPermissions,)

    def perform_destroy(self, instance):
        account = instance.account

        if instance.is_managed:
            # Delete from AWS. This will throw the appropriate error
            # if the group is being used.
            driver = account.get_driver()
            try:
                driver.delete_security_group(instance.name)
            except DeleteGroupException as e:
                raise ValidationError({
                    'detail': ['Could not delete this security group.',
                               e.message]
                })

        # Save this before we delete
        is_default = instance.is_default

        # Delete the instance
        instance.delete()

        # update accounts configuration file if the security
        # group's is_default was True
        if is_default:
            logger.debug('Security group deleted and is_default set to True; '
                         'updating cloud account configuration.')
            account.update_config()


class SecurityGroupRulesAPIView(mixins.SecurityGroupRelatedMixin, generics.ListAPIView):
    """
    ### PUT

    Authorizes or revokes a rule for the security group. The rule
    must be valid JSON with the following fields:

    `action` -- the action to take for the rule [authorize, revoke]

    `protocol` -- the protocol of the rule [tcp, udp, icmp]

    `from_port` -- the starting port for the rule's port range [0-65535]

    `to_port` -- the ending port for the rule's port range [0-65535]

    `rule` -- the actual rule, this should be either a CIDR (IP address
    with associated routing prefix) **or** an existing account ID and
    group name combination to authorize or revoke for the rule. See
    examples below.

    ##### To authorize SSH to a single IP address
        {
            "action": "authorize",
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "rule": "192.168.1.108/32"
        }

    ##### To authorize a range of UDP ports to another account's group
        {
            "action": "authorize",
            "protocol": "udp",
            "from_port": 3000,
            "to_port": 3030,
            "rule": "<account_number>:<group_name>"
        }

        Where account_number is the account ID of the account and
        group_name is an existing group name on that account.

    To revoke either of the rules above, you would just change the `action`
    field's value to be "revoke"
    """
    serializer_class = serializers.SecurityGroupRuleSerializer

    def get_queryset(self):
        return self.get_securitygroup().rules()

    def put(self, request, *args, **kwargs):
        security_group = self.get_securitygroup()

        serializer = self.get_serializer(security_group=security_group, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CloudAccountSecurityGroupListAPIView(mixins.CloudAccountRelatedMixin,
                                           generics.ListCreateAPIView):
    """
    Like the standard, top-level Security Group List API, this API will allow
    you to create and pull security groups. The only significant difference is
    that GET requests will only return security groups associated with the
    account, and you may only create security groups on the associated account.

    ### GET

    Retrieves the detail for the security group as defined by its
    `pk` identifier in the URL. The associated `rules` and
    `active_hosts` fields will be populated like with the full
    list.

    ### PUT / PATCH

    Updates an existing security group's details. Currently, only
    the `default` field may be modified.

    ### DELETE

    Removes the corresponding security group from stackd.io, as well as
    from the underlying cloud account if `managed` is true.
    **NOTE** that if the security group is currently being used, then
    it can not be removed. You must first terminate all machines depending
    on the security group and then delete it.
    """
    serializer_class = serializers.CloudAccountSecurityGroupSerializer
    filter_class = filters.SecurityGroupFilter

    def get_queryset(self):
        account = self.get_cloudaccount()
        return account.security_groups.all()

    def perform_create(self, serializer):
        serializer.save(account=self.get_cloudaccount())


class FullCloudAccountSecurityGroupListAPIView(mixins.CloudAccountRelatedMixin,
                                               generics.ListAPIView):
    """
    The standard security_group endpoint will only show you security groups that are
    stored in our local database.  This endpoint will reach out to the associated
    CloudAccount and pull a list of all applicable security groups, along with their
    associated rules.
    """
    serializer_class = serializers.DirectCloudAccountSecurityGroupSerializer
    filter_class = filters.SecurityGroupFilter

    def get_queryset(self):
        account = self.get_cloudaccount()
        driver = account.get_driver()
        account_groups = driver.get_security_groups()

        return FakeQuerySet(models.SecurityGroup, sorted(account_groups, key=lambda x: x.name))
