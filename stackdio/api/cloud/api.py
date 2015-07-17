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

import yaml
from rest_framework import generics, status
from rest_framework.compat import OrderedDict
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from stackdio.api.blueprints.serializers import BlueprintSerializer
from stackdio.api.formulas.models import FormulaVersion
from stackdio.api.formulas.serializers import FormulaVersionSerializer
from stackdio.core.exceptions import BadRequest, ResourceConflict
from stackdio.core.permissions import StackdioModelPermissions, StackdioObjectPermissions
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

    def perform_create(self, serializer):

        data = self.request.DATA
        files = self.request.FILES

        # Lookup provider type
        try:
            obj = serializer.save()

            driver = obj.get_driver()

            # Leverage the driver to generate its required data that
            # will be serialized down to yaml and stored in both the database
            # and the salt cloud providers file
            provider_data = driver.get_provider_data(data, files)

            # Generate the yaml and store in the database
            yaml_data = {
                obj.slug: provider_data
            }
            obj.yaml = yaml.safe_dump(yaml_data, default_flow_style=False)
            obj.save()

            # Update the salt cloud providers file
            obj.update_config()

        except models.CloudProvider.DoesNotExist:
            err_msg = 'Given provider type does not exist.'
            logger.exception(err_msg)
            raise BadRequest(err_msg)


class CloudAccountDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.CloudAccount.objects.all()
    serializer_class = serializers.CloudAccountSerializer
    permission_classes = (StackdioObjectPermissions,)

    def destroy(self, request, *args, **kwargs):
        # check for profiles using this account before deleting
        profiles = set(self.get_object().profiles.all())
        if profiles:
            profiles = serializers.CloudProfileSerializer(
                profiles,
                context={'request': request}).data
            return Response({
                'detail': 'One or more profiles are making use of this account.',
                'profiles': profiles,
            }, status=status.HTTP_400_BAD_REQUEST)

        # ask the driver to clean up after itsef since it's no longer needed
        driver = self.get_object().get_driver()
        driver.destroy()

        return super(CloudAccountDetailAPIView, self).destroy(request, *args, **kwargs)


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
    def list(self, request, *args, **kwargs):
        account = self.get_cloudaccount()
        driver = account.get_driver()

        subnets = driver.get_vpc_subnets()
        return Response({
            'results': serializers.VPCSubnetSerializer(subnets, many=True).data
        })


class CloudAccountFormulaVersionsAPIView(mixins.CloudAccountRelatedMixin,
                                         generics.ListCreateAPIView):
    serializer_class = FormulaVersionSerializer

    def get_queryset(self):
        account = self.get_cloudaccount()
        return account.formula_versions.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        formula = serializer.validated_data.get('formula')
        account = self.get_cloudaccount()

        try:
            # Setting self.instance will cause self.update() to be called instead of
            # self.create() during save()
            serializer.instance = account.formula_versions.get(formula=formula)
            response_code = status.HTTP_200_OK
        except FormulaVersion.DoesNotExist:
            # Return the proper response code
            response_code = status.HTTP_201_CREATED

        serializer.save(content_object=account)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=response_code, headers=headers)


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

    def update(self, request, *args, **kwargs):
        # validate that the AMI exists by looking it up in the cloud account
        if 'image_id' in request.DATA:
            driver = self.get_object().account.get_driver()
            result, error = driver.has_image(request.DATA['image_id'])
            if not result:
                raise BadRequest(error)

        # Perform the update
        ret = super(CloudProfileDetailAPIView, self).update(request,
                                                            *args,
                                                            **kwargs)

        # Regenerate the profile config file
        profile = self.get_object()
        profile.update_config()
        return ret

    def destroy(self, request, *args, **kwargs):
        # check for blueprint usage before deleting
        blueprints = set([hd.blueprint
                          for hd in self.get_object().host_definitions.all()])
        if blueprints:
            blueprints = BlueprintSerializer(blueprints,
                                             context={'request': request}).data
            return Response({
                'detail': 'One or more blueprints are making use of this '
                          'profile.',
                'blueprints': blueprints,
            }, status=status.HTTP_400_BAD_REQUEST)

        return super(CloudProfileDetailAPIView, self).destroy(request,
                                                              *args,
                                                              **kwargs)


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
        logger.debug(self.get_cloudprovider())

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

    `is_default` -- Boolean representing if this group, for this
                    account, is set to automatically be added
                    to all hosts launched on the account. **NOTE**
                    this property may only be set by an admin.
    """
    queryset = models.SecurityGroup.objects.all().with_rules()
    serializer_class = serializers.SecurityGroupSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.SecurityGroupFilter

    # TODO: Ignore code complexity issues
    def create(self, request, *args, **kwargs):  # NOQA
        name = request.DATA.get('name')
        group_id = request.DATA.get('group_id')
        description = request.DATA.get('description')
        account_id = request.DATA.get('account')
        is_default = request.DATA.get('is_default', False)

        if not request.user.is_superuser:
            is_default = False
        elif not isinstance(is_default, bool):
            is_default = False

        account = models.CloudAccount.objects.get(id=account_id)
        driver = account.get_driver()

        # check if the group already exists in our DB first
        try:
            models.SecurityGroup.objects.get(
                name=name,
                group_id=group_id,
                account=account
            )
            raise ResourceConflict('Security group already exists')
        except models.SecurityGroup.DoesNotExist:
            # doesn't exist in our database
            pass

        # check if the group exists on the account
        account = None
        if group_id:
            try:
                account_group = driver.get_security_groups([group_id])[name]
                logger.debug('Security group already exists on the '
                             'account: {0!r}'.format(account_group))

            except KeyError:
                raise
            except:
                # doesn't exist on the account either, we'll create it now
                account_group = None

        # admin is using an existing group, use the existing group id
        if account_group:
            group_id = account_group['group_id']
            description = account_group['description']
        else:
            # create a new group
            group_id = driver.create_security_group(name, description)

        # create a new group in the DB
        group_obj = models.SecurityGroup.objects.create(
            name=name,
            description=description,
            group_id=group_id,
            account=account,
            is_default=is_default
        )

        # if an admin and the security group is_default, we need to make sure
        # the cloud account configuration is properly maintained
        if request.user.is_superuser and is_default:
            logger.debug('Writing cloud accounts file because new security '
                         'group was added with is_default flag set to True')
            account.update_config()

        serializer = serializers.SecurityGroupSerializer(group_obj, context={
            'request': request
        })
        return Response(serializer.data)


class SecurityGroupDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Shows the detail for a security group and allows for the is_default
    flag to be modified (for admins only.)

    ### GET

    Retrieves the detail for the security group as defined by its
    `pk` identifier in the URL. The associated `rules` and
    `active_hosts` fields will be populated like with the full
    list.

    ### PUT

    Updates an existing security group's details. Currently, only
    the is_default field may be modified and only by admins.

    ### DELETE

    Removes the corresponding security group from stackd.io as well as
    from the underlying cloud account. **NOTE** that if the security
    group is currently being used, then it can not be removed. You
    must first terminate all machines depending on the security group
    and then delete it.
    """

    queryset = models.SecurityGroup.objects.all()
    serializer_class = serializers.SecurityGroupSerializer
    permission_classes = (StackdioObjectPermissions,)

    def update(self, request, *args, **kwargs):
        """
        Allow admins to update the is_default field on security groups.
        """

        if 'is_default' not in request.DATA:
            raise BadRequest('is_default is the only field allowed to be '
                             'updated.')

        is_default = request.DATA.get('is_default')
        if not isinstance(is_default, bool):
            raise BadRequest('is_default field must be a boolean.')

        # update the field value if needed
        obj = self.get_object()
        if obj.is_default != is_default:
            obj.is_default = is_default
            obj.save()

            # update accounts configuration file
            logger.debug('Security group is_default modified; updating cloud '
                         'account configuration.')
            obj.account.update_config()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):

        sg = self.get_object()

        # Delete from AWS. This will throw the appropriate error
        # if the group is being used.
        account = sg.account
        driver = account.get_driver()
        driver.delete_security_group(sg.name)

        # store the is_default and delete the security group
        is_default = sg.is_default
        result = super(SecurityGroupDetailAPIView, self).destroy(request,
                                                                 *args,
                                                                 **kwargs)

        # update accounts configuration file if the security
        # group's is_default was True
        if is_default:
            logger.debug('Security group deleted and is_default set to True; '
                         'updating cloud account configuration.')
            account.update_config()

        # return the original destroy response
        return result


class SecurityGroupRulesAPIView(generics.RetrieveUpdateAPIView):
    """
    ### PUT

    Authorizes or revokes a rule for the security group. The rule
    must be valid JSON with the following fields:

    `action` -- the action to take for the rule [authorize, revoke]

    `protocol` -- the protocol of the rule [tcp, udp, icmp]

    `from_port` -- the starting port for the rule's port range [1-65535]

    `to_port` -- the ending port for the rule's port range [1-65535]

    `rule` -- the actual rule, this should be either a CIDR (IP address
    with associated routing prefix) **or** an existing account ID and
    group name combination to authorize or revoke for the rule. See
    examples below.

    ##### To authorize SSH to a single IP address
        {
            'action': 'authorize',
            'protocol': 'tcp',
            'from_port': 22,
            'to_port': 22,
            'rule': '192.168.1.108/32'
        }

    ##### To authorize a range of UDP ports to another account's group
        {
            'action': 'authorize',
            'protocol': 'udp',
            'from_port': 3000,
            'to_port': 3030,
            'rule': '<account_number>:<group_name>'
        }

        Where account_number is the account ID of the account and
        group_name is an existing group name on that account.

    To revoke either of the rules above, you would just change the `action`
    field's value to be "revoke"
    """

    queryset = models.SecurityGroup.objects.all()
    serializer_class = serializers.SecurityGroupRuleSerializer
    permission_classes = (StackdioObjectPermissions,)

    def retrieve(self, request, *args, **kwargs):
        sg = self.get_object()
        driver = sg.account.get_driver()
        result = driver.get_security_groups(sg.group_id)
        return Response(result[sg.name]['rules'])

    def update(self, request, *args, **kwargs):
        sg = self.get_object()
        account = sg.account
        driver = account.get_driver()

        # validate input
        errors = []
        required_fields = [
            'action',
            'protocol',
            'from_port',
            'to_port',
            'rule']
        for field in required_fields:
            v = request.DATA.get(field)
            if not v:
                errors.append('{0} is a required field.'.format(field))

        if errors:
            raise BadRequest(errors)

        # Check the rule to determine the "type" of the rule. This
        # can be a CIDR or group rule. CIDR will look like an IP
        # address and anything else will be considered a group
        # rule, however, a group can contain the account id of
        # the group we're dealing with. If the group rule does
        # not contain a colon then we'll add the account's
        # account id
        rule = request.DATA.get('rule')
        if not driver.is_cidr_rule(rule) and ':' not in rule:
            rule = account.account_id + ':' + rule
            request.DATA['rule'] = rule
            logger.debug('Prefixing group rule with account id. '
                         'New rule: {0}'.format(rule))

        if request.DATA.get('action') == 'authorize':
            driver.authorize_security_group(sg.group_id, request.DATA)
        elif request.DATA.get('action') == 'revoke':
            driver.revoke_security_group(sg.group_id, request.DATA)
        elif request.DATA.get('action') == 'revoke_all':
            driver.revoke_all_security_groups(sg.group_id)
        else:
            raise BadRequest('Missing or invalid `action` parameter. Must be '
                             'one of \'authorize\' or \'revoke\'')

        result = driver.get_security_groups(sg.group_id)
        return Response(result[sg.name]['rules'])


class CloudAccountSecurityGroupListAPIView(mixins.CloudAccountRelatedMixin,
                                           SecurityGroupListAPIView):
    """
    Like the standard, top-level Security Group List API, this API will allow
    you to create and pull security groups. The only significant difference is
    that GET requests will only return security groups associated with the
    account.

    *For regular users*, this will only show security groups owned by you and
    associated with the account. *For admins*, this will pull all security
    groups on the account, regardless of ownership.

    Additionally, admins may provide a query parameter and value
    `filter=default` to only show the security groups that have been designated
    as "default" groups to be attached to all hosts started using this account

    See the standard, top-level Security Group API for further information.
    """
    filter_class = filters.SecurityGroupFilter

    def get_queryset(self):
        account = self.get_cloudaccount()

        # if admin, return all of the known default security groups on the
        # account
        if self.request.user.is_superuser:
            kwargs = {}
            if self.request.QUERY_PARAMS.get('filter', '') == 'default':
                kwargs['is_default'] = True
            return account.security_groups.filter(**kwargs).with_rules()

        # if user, only get what they own
        else:
            return self.request.user.security_groups.filter(
                account=account
            ).with_rules()

    # Override the generic list API to inject the security groups
    # known by the cloud account
    def list(self, request, *args, **kwargs):
        response = super(CloudAccountSecurityGroupListAPIView, self).list(
            request,
            *args,
            **kwargs)

        # only admins get to see all the groups on the account
        if not request.user.is_superuser:
            return response

        # Grab the groups from the account and inject them into the response,
        # removing the known managed security groups first
        account = self.get_cloudaccount()
        driver = account.get_driver()
        account_groups = driver.get_security_groups()
        for group in account.security_groups.all():
            if group.name in account_groups:
                del account_groups[group.name]

        # Filter these too
        query_name = request.QUERY_PARAMS.get('name', '')
        for name, data in account_groups.items():
            if query_name.lower() not in name.lower():
                del account_groups[name]

        response.data['account_groups'] = account_groups
        return response
