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
from collections import OrderedDict

from django.core.cache import cache
from guardian.shortcuts import assign_perm
from rest_framework import generics
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
from . import filters, mixins, models, serializers

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
            ('providers', reverse('api:cloud:cloudprovider-list',
                                  request=request,
                                  format=format)),
            ('accounts', reverse('api:cloud:cloudaccount-list',
                                 request=request,
                                 format=format)),
            ('images', reverse('api:cloud:cloudimage-list',
                               request=request,
                               format=format)),
            ('snapshots', reverse('api:cloud:snapshot-list',
                                  request=request,
                                  format=format)),
            ('security_groups', reverse('api:cloud:securitygroup-list',
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


class CloudProviderRequiredFieldsAPIView(generics.RetrieveAPIView):
    """
    This endpoint lists all the extra fields required when creating an account for this provider.
    """
    queryset = models.CloudProvider.objects.all()
    permission_classes = (StackdioObjectPermissions,)
    lookup_field = 'name'

    # Just list the required fields instead of using a serializer
    def retrieve(self, request, *args, **kwargs):
        provider = self.get_object()
        driver = provider.get_driver()
        return Response(driver.get_required_fields())


class CloudProviderObjectUserPermissionsViewSet(mixins.CloudProviderPermissionsMixin,
                                                StackdioObjectUserPermissionsViewSet):
    pass


class CloudProviderObjectGroupPermissionsViewSet(mixins.CloudProviderPermissionsMixin,
                                                 StackdioObjectGroupPermissionsViewSet):
    pass


class CloudAccountListAPIView(generics.ListCreateAPIView):
    queryset = models.CloudAccount.objects.all()
    serializer_class = serializers.CloudAccountSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.CloudAccountFilter

    def perform_create(self, serializer):
        account = serializer.save()

        for perm in models.CloudAccount.object_permissions:
            assign_perm('cloud.%s_cloudaccount' % perm, self.request.user, account)


class CloudAccountDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.CloudAccount.objects.all()
    serializer_class = serializers.CloudAccountSerializer
    permission_classes = (StackdioObjectPermissions,)

    def perform_update(self, serializer):
        account = serializer.save()
        account.update_config()

    def perform_destroy(self, instance):
        # check for images using this account before deleting
        images = [p.slug for p in instance.images.all()]
        if images:
            raise ValidationError({
                'detail': 'One or more images are making use of this account.',
                'images': images,
            })

        # ask the driver to clean up after itself since it's no longer needed
        driver = instance.get_driver()
        driver.destroy()

        instance.delete()


class CloudAccountModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    model_cls = models.CloudAccount


class CloudAccountModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    model_cls = models.CloudAccount


class CloudAccountObjectUserPermissionsViewSet(mixins.CloudAccountPermissionsMixin,
                                               StackdioObjectUserPermissionsViewSet):
    pass


class CloudAccountObjectGroupPermissionsViewSet(mixins.CloudAccountPermissionsMixin,
                                                StackdioObjectGroupPermissionsViewSet):
    pass


class GlobalOrchestrationComponentListAPIView(mixins.CloudAccountRelatedMixin,
                                              generics.ListCreateAPIView):
    serializer_class = serializers.GlobalOrchestrationComponentSerializer

    def get_queryset(self):
        cloud_account = self.get_cloudaccount()
        return cloud_account.formula_components.all()

    def get_serializer_context(self):
        context = super(GlobalOrchestrationComponentListAPIView, self).get_serializer_context()
        context['content_object'] = self.get_cloudaccount()
        return context

    def perform_create(self, serializer):
        serializer.save(content_object=self.get_cloudaccount())


class GlobalOrchestrationComponentDetailAPIView(mixins.CloudAccountRelatedMixin,
                                                generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.GlobalOrchestrationComponentSerializer

    def get_queryset(self):
        cloud_account = self.get_cloudaccount()
        return cloud_account.formula_components.all()

    def get_serializer_context(self):
        context = super(GlobalOrchestrationComponentDetailAPIView, self).get_serializer_context()
        context['content_object'] = self.get_cloudaccount()
        return context


class GlobalOrchestrationPropertiesAPIView(generics.RetrieveUpdateAPIView):
    queryset = models.CloudAccount.objects.all()
    serializer_class = serializers.GlobalOrchestrationPropertiesSerializer
    permission_classes = (StackdioObjectPermissions,)


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


class CloudAccountImageListAPIView(mixins.CloudAccountRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.CloudImageSerializer
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.CloudImageFilter

    def get_queryset(self):
        cloud_account = self.get_cloudaccount()
        return cloud_account.images.all()


class CloudImageListAPIView(generics.ListCreateAPIView):
    queryset = models.CloudImage.objects.all()
    serializer_class = serializers.CloudImageSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.CloudImageFilter

    def perform_create(self, serializer):
        image = serializer.save()
        image.update_config()

        for perm in models.CloudImage.object_permissions:
            assign_perm('cloud.%s_cloudimage' % perm, self.request.user, image)


class CloudImageDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.CloudImage.objects.all()
    serializer_class = serializers.CloudImageSerializer
    permission_classes = (StackdioObjectPermissions,)

    def perform_update(self, serializer):
        image = serializer.save()
        image.update_config()

    def perform_destroy(self, instance):
        # check for blueprint usage before deleting
        blueprints = Blueprint.objects.filter(host_definitions__cloud_image=instance).distinct()

        if blueprints:
            raise ValidationError({
                'detail': ['One or more blueprints are making use of this image.'],
                'blueprints': [b.title for b in blueprints],
            })

        instance.delete()


class CloudImageModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    model_cls = models.CloudImage


class CloudImageModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    model_cls = models.CloudImage


class CloudImageObjectUserPermissionsViewSet(mixins.CloudImagePermissionsMixin,
                                             StackdioObjectUserPermissionsViewSet):
    pass


class CloudImageObjectGroupPermissionsViewSet(mixins.CloudImagePermissionsMixin,
                                              StackdioObjectGroupPermissionsViewSet):
    pass


class SnapshotListAPIView(generics.ListCreateAPIView):
    queryset = models.Snapshot.objects.all()
    serializer_class = serializers.SnapshotSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.SnapshotFilter

    def perform_create(self, serializer):
        snapshot = serializer.save()

        for perm in models.Snapshot.object_permissions:
            assign_perm('cloud.%s_snapshot' % perm, self.request.user, snapshot)


class SnapshotDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Snapshot.objects.all()
    serializer_class = serializers.SnapshotSerializer
    permission_classes = (StackdioObjectPermissions,)


class SnapshotModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    model_cls = models.Snapshot


class SnapshotModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    model_cls = models.Snapshot


class SnapshotObjectUserPermissionsViewSet(mixins.SnapshotPermissionsMixin,
                                           StackdioObjectUserPermissionsViewSet):
    pass


class SnapshotObjectGroupPermissionsViewSet(mixins.SnapshotPermissionsMixin,
                                            StackdioObjectGroupPermissionsViewSet):
    pass


class CloudInstanceSizeListAPIView(mixins.CloudProviderRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.CloudInstanceSizeSerializer
    filter_class = filters.CloudInstanceSizeFilter
    lookup_field = 'instance_id'

    def get_queryset(self):
        cloud_provider = self.get_cloudprovider()
        return cloud_provider.instance_sizes.all()


class CloudInstanceSizeDetailAPIView(mixins.CloudProviderRelatedMixin, generics.RetrieveAPIView):
    serializer_class = serializers.CloudInstanceSizeSerializer
    lookup_field = 'instance_id'

    def get_queryset(self):
        cloud_provider = self.get_cloudprovider()
        return cloud_provider.instance_sizes.all()


class CloudRegionListAPIView(mixins.CloudProviderRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.CloudRegionSerializer
    filter_class = filters.CloudRegionFilter
    lookup_field = 'title'

    def get_queryset(self):
        cloud_provider = self.get_cloudprovider()
        return cloud_provider.regions.all()


class CloudRegionDetailAPIView(mixins.CloudProviderRelatedMixin, generics.RetrieveAPIView):
    serializer_class = serializers.CloudRegionSerializer
    lookup_field = 'title'

    def get_queryset(self):
        cloud_provider = self.get_cloudprovider()
        return cloud_provider.regions.all()


class CloudRegionZoneListAPIView(mixins.CloudProviderRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.CloudZoneSerializer
    filter_class = filters.CloudZoneFilter

    def get_queryset(self):
        cloud_provider = self.get_cloudprovider()
        region = cloud_provider.regions.get(title=self.kwargs.get('title'))
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
    in the JSON request.

    `group_id` -- the security group ID as defined py the cloud provider.
                  You may only provide either the group_id or the name, but
                  not both.  Using this property will **NOT** create a new group in the provider

    `name` -- The name of the security group. This will also be
              used to create the security group on the account.
              You may only provide either the group_id or the name, but
              not both.  Using this property **WILL** create a new group in the provider

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
                if 'does not exist' in e.message:
                    logger.info('Security group already deleted.')
                else:
                    raise ValidationError({
                        'detail': ['Could not delete this security group.', e.message]
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

    ### POST

    Creates a new security group given the following properties
    in the JSON request.

    `group_id` -- the security group ID as defined py the cloud provider.
                  You may only provide either the group_id or the name, but
                  not both.  Using this property will **NOT** create a new group in the provider

    `name` -- The name of the security group. This will also be
              used to create the security group on the account.
              You may only provide either the group_id or the name, but
              not both.  Using this property **WILL** create a new group in the provider

    `description` -- The description or purpose of the group.

    `default` -- Boolean representing if this group, for this
                    account, is set to automatically be added
                    to all hosts launched on the account. **NOTE**
                    this property may only be set by an admin.
    """
    serializer_class = serializers.CloudAccountSecurityGroupSerializer
    filter_class = filters.SecurityGroupFilter

    def get_queryset(self):
        account = self.get_cloudaccount()
        return account.security_groups.all()

    def get_serializer_context(self):
        context = super(CloudAccountSecurityGroupListAPIView, self).get_serializer_context()
        context['account'] = self.get_cloudaccount()
        return context


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

        cache_key = 'accounts:{0}:all_security_groups'.format(account.id)

        account_groups = cache.get(cache_key)

        if account_groups is None:
            driver = account.get_driver()
            account_groups = driver.get_security_groups()
            cache.set(cache_key, account_groups, 30)

        return FakeQuerySet(models.SecurityGroup, sorted(account_groups, key=lambda x: x.name))
