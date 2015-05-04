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
from rest_framework import (
    generics,
    parsers,
    permissions,
    status
)
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from core.exceptions import BadRequest, ResourceConflict
from core.permissions import (
    AdminOrOwnerPermission,
    IsAdminOrReadOnly,
)
from blueprints.serializers import BlueprintSerializer
from . import models
from . import serializers
from . import filters
from core.utils import recursive_update


logger = logging.getLogger(__name__)


class CloudProviderTypeListAPIView(generics.ListAPIView):
    queryset = models.CloudProviderType.objects.all()
    serializer_class = serializers.CloudProviderTypeSerializer


class CloudProviderTypeDetailAPIView(generics.RetrieveAPIView):
    queryset = models.CloudProviderType.objects.all()
    serializer_class = serializers.CloudProviderTypeSerializer


class CloudProviderListAPIView(generics.ListCreateAPIView):
    queryset = models.CloudProvider.objects.all()
    serializer_class = serializers.CloudProviderSerializer
    permission_classes = (permissions.DjangoModelPermissions,)
    filter_class = filters.CloudProviderFilter

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

        except models.CloudProviderType.DoesNotExist:
            err_msg = 'Given provider type does not exist.'
            logger.exception(err_msg)
            raise BadRequest(err_msg)


class CloudProviderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.CloudProvider.objects.all()
    serializer_class = serializers.CloudProviderSerializer
    permission_classes = (permissions.DjangoModelPermissions,)

    def destroy(self, request, *args, **kwargs):
        # check for profiles using this provider before deleting
        profiles = set(self.get_object().profiles.all())
        if profiles:
            profiles = serializers.CloudProfileSerializer(
                profiles,
                context={'request': request}).data
            return Response({
                'detail': 'One or more profiles are making use of this '
                          'provider.',
                'profiles': profiles,
            }, status=status.HTTP_400_BAD_REQUEST)

        # ask the driver to clean up after itsef since it's no longer needed
        driver = self.get_object().get_driver()
        driver.destroy()

        return super(CloudProviderDetailAPIView, self).destroy(request,
                                                               *args,
                                                               **kwargs)


class CloudInstanceSizeListAPIView(generics.ListAPIView):
    queryset = models.CloudInstanceSize.objects.all()
    serializer_class = serializers.CloudInstanceSizeSerializer
    filter_class = filters.CloudInstanceSizeFilter


class CloudInstanceSizeDetailAPIView(generics.RetrieveAPIView):
    queryset = models.CloudInstanceSize.objects.all()
    serializer_class = serializers.CloudInstanceSizeSerializer


class GlobalOrchestrationComponentListAPIView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = serializers.GlobalOrchestrationFormulaComponentSerializer

    def get_provider(self):
        obj = get_object_or_404(models.CloudProvider, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        return self.get_provider().global_formula_components.all()

    def perform_create(self, serializer):
        serializer.save(provider=self.get_provider())

    def create(self, request, *args, **kwargs):
        component_id = request.DATA.get('component')
        try:
            # Delete an existing component if there is one
            component = self.get_queryset().get(component__id=component_id)
            component.delete()
        except models.GlobalOrchestrationFormulaComponent.DoesNotExist:
            pass

        return super(GlobalOrchestrationComponentListAPIView, self) \
            .create(request, *args, **kwargs)


class GlobalOrchestrationComponentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = serializers.GlobalOrchestrationFormulaComponentSerializer
    queryset = models.GlobalOrchestrationFormulaComponent.objects.all()


class GlobalOrchestrationPropertiesAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = serializers.serializers.Serializer

    def get_provider(self):
        obj = get_object_or_404(models.CloudProvider, id=self.kwargs.get('pk'))
        self.check_object_permissions(self.request, obj)
        return obj

    def retrieve(self, request, *args, **kwargs):
        return Response(self.get_provider().global_orchestration_properties)

    def update(self, request, *args, **kwargs):
        """
        PUT request - overwrite all the props
        """
        if not isinstance(request.DATA, dict):
            raise BadRequest('Request data but be a JSON object, not an array')
        provider = self.get_provider()
        provider.global_orchestration_properties = request.DATA
        provider.save()
        return Response(provider.global_orchestration_properties)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH request - merge the these new props in, overwrite old with new
        if there are conflicts
        """
        if not isinstance(request.DATA, dict):
            raise BadRequest('Request data but be a JSON object, not an array')
        provider = self.get_provider()
        provider.global_orchestration_properties = recursive_update(
            provider.global_orchestration_properties, request.DATA)
        provider.save()
        return Response(provider.global_orchestration_properties)


class CloudProfileListAPIView(generics.ListCreateAPIView):
    queryset = models.CloudProfile.objects.all()
    serializer_class = serializers.CloudProfileSerializer
    permission_classes = (permissions.DjangoModelPermissions,)
    filter_class = filters.CloudProfileFilter

    def perform_create(self, serializer):
        obj = serializer.save()
        obj.update_config()


class CloudProfileDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.CloudProfile.objects.all()
    serializer_class = serializers.CloudProfileSerializer
    permission_classes = (permissions.DjangoModelPermissions,)

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

    def update(self, request, *args, **kwargs):
        # validate that the AMI exists by looking it up in the cloud provider
        if 'image_id' in request.DATA:
            driver = self.get_object().cloud_provider.get_driver()
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


class SnapshotListAPIView(generics.ListCreateAPIView):
    queryset = models.Snapshot.objects.all()
    serializer_class = serializers.SnapshotSerializer
    permission_classes = (permissions.DjangoModelPermissions,)


class SnapshotAdminListAPIView(generics.ListAPIView):
    queryset = models.Snapshot.objects.all()
    serializer_class = serializers.SnapshotSerializer
    permission_classes = (permissions.IsAdminUser,)


class SnapshotDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Snapshot.objects.all()
    serializer_class = serializers.SnapshotSerializer
    permission_classes = (permissions.DjangoModelPermissions,)


class CloudRegionListAPIView(generics.ListAPIView):
    queryset = models.CloudRegion.objects.all()
    serializer_class = serializers.CloudRegionSerializer
    filter_class = filters.CloudRegionFilter


class CloudRegionDetailAPIView(generics.RetrieveAPIView):
    queryset = models.CloudRegion.objects.all()
    serializer_class = serializers.CloudRegionSerializer


class CloudRegionZoneListAPIView(generics.ListAPIView):
    serializer_class = serializers.CloudZoneSerializer
    filter_class = filters.CloudZoneFilter

    def get_queryset(self):
        return models.CloudZone.objects.filter(region__id=self.kwargs['pk'])


class CloudZoneListAPIView(generics.ListAPIView):
    queryset = models.CloudZone.objects.all()
    serializer_class = serializers.CloudZoneSerializer
    filter_class = filters.CloudZoneFilter


class CloudZoneDetailAPIView(generics.RetrieveAPIView):
    queryset = models.CloudZone.objects.all()
    serializer_class = serializers.CloudZoneSerializer


class SecurityGroupListAPIView(generics.ListCreateAPIView):
    """
    Lists and creates new security groups.

    ### GET

    Retrieves all security groups owned by the authenticated user.
    The associated rules for each group will also be given in the
    `rules` attribute. The `active_hosts` field will also be
    updated to show the number of hosts known by stackd.io to be
    using the security group at this time, but please **note**
    that other machines in the cloud provider could be using
    the same security group and stackd.io may not be aware.

    ### POST

    Creates a new security group given the following properties
    in the JSON request:

    `name` -- The name of the security group. This will also be
              used to create the security group on the provider.

    `description` -- The description or purpose of the group.

    `cloud_provider` -- The id of the cloud provider to associate
                        this group with.

    `is_default` -- Boolean representing if this group, for this
                    provider, is set to automatically be added
                    to all hosts launched on the provider. **NOTE**
                    this property may only be set by an admin.
    """

    serializer_class = serializers.SecurityGroupSerializer
    parser_classes = (parsers.JSONParser,)
    filter_class = filters.SecurityGroupFilter

    # Only admins may create security groups directly. Regular users
    # are restricted to using automatically managed security groups
    # on stacks
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        # if admin, get them all
        if self.request.user.is_superuser:
            return models.SecurityGroup.objects.all().with_rules()

        # if user, only get what they own
        else:
            return self.request.user.security_groups.all().with_rules()

    # TODO: Ignore code complexity issues
    def create(self, request, *args, **kwargs):  # NOQA
        name = request.DATA.get('name')
        group_id = request.DATA.get('group_id')
        description = request.DATA.get('description')
        provider_id = request.DATA.get('cloud_provider')
        is_default = request.DATA.get('is_default', False)
        owner = request.user

        if not owner.is_superuser:
            is_default = False
        elif not isinstance(is_default, bool):
            is_default = False

        provider = models.CloudProvider.objects.get(id=provider_id)
        driver = provider.get_driver()

        # check if the group already exists in our DB first
        try:
            models.SecurityGroup.objects.get(
                name=name,
                group_id=group_id,
                cloud_provider=provider
            )
            raise ResourceConflict('Security group already exists')
        except models.SecurityGroup.DoesNotExist:
            # doesn't exist in our database
            pass

        # check if the group exists on the provider
        provider_group = None
        if group_id:
            try:
                provider_group = driver.get_security_groups([group_id])[name]
                logger.debug('Security group already exists on the '
                             'provider: {0!r}'.format(provider_group))

            except KeyError:
                raise
            except:
                # doesn't exist on the provider either, we'll create it now
                provider_group = None

        # admin is using an existing group, use the existing group id
        if provider_group:
            group_id = provider_group['group_id']
            description = provider_group['description']
        else:
            # create a new group
            group_id = driver.create_security_group(name, description)

        # create a new group in the DB
        group_obj = models.SecurityGroup.objects.create(
            name=name,
            description=description,
            group_id=group_id,
            cloud_provider=provider,
            owner=owner,
            is_default=is_default
        )

        # if an admin and the security group is_default, we need to make sure
        # the cloud provider configuration is properly maintained
        if owner.is_superuser and is_default:
            logger.debug('Writing cloud providers file because new security '
                         'group was added with is_default flag set to True')
            provider.update_config()

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
    from the underlying cloud provider. **NOTE** that if the security
    group is currently being used, then it can not be removed. You
    must first terminate all machines depending on the security group
    and then delete it.
    """

    queryset = models.SecurityGroup.objects.all()
    serializer_class = serializers.SecurityGroupSerializer
    parser_classes = (parsers.JSONParser,)
    # Only admins are allowed write access
    permission_classes = (permissions.IsAuthenticated,
                          IsAdminOrReadOnly,
                          AdminOrOwnerPermission,)

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

            # update providers configuration file
            logger.debug('Security group is_default modified; updating cloud '
                         'provider configuration.')
            obj.cloud_provider.update_config()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):

        sg = self.get_object()

        # Delete from AWS. This will throw the appropriate error
        # if the group is being used.
        provider = sg.cloud_provider
        driver = provider.get_driver()
        driver.delete_security_group(sg.name)

        # store the is_default and delete the security group
        is_default = sg.is_default
        result = super(SecurityGroupDetailAPIView, self).destroy(request,
                                                                 *args,
                                                                 **kwargs)

        # update providers configuration file if the security
        # group's is_default was True
        if is_default:
            logger.debug('Security group deleted and is_default set to True; '
                         'updating cloud provider configuration.')
            provider.update_config()

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

    ##### To authorize a range of UDP ports to another provider's group
        {
            'action': 'authorize',
            'protocol': 'udp',
            'from_port': 3000,
            'to_port': 3030,
            'rule': '<account_number>:<group_name>'
        }

        Where account_number is the account ID of the provider and
        group_name is an existing group name on that provider.

    To revoke either of the rules above, you would just change the `action`
    field's value to be "revoke"
    """

    queryset = models.SecurityGroup.objects.all()
    serializer_class = serializers.SecurityGroupRuleSerializer
    parser_classes = (parsers.JSONParser,)
    permission_classes = (permissions.IsAuthenticated,
                          AdminOrOwnerPermission,)

    def retrieve(self, request, *args, **kwargs):
        sg = self.get_object()
        driver = sg.cloud_provider.get_driver()
        result = driver.get_security_groups(sg.group_id)
        return Response(result[sg.name]['rules'])

    def update(self, request, *args, **kwargs):
        sg = self.get_object()
        provider = sg.cloud_provider
        driver = provider.get_driver()

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
        # not contain a colon then we'll add the provider's
        # account id
        rule = request.DATA.get('rule')
        if not driver.is_cidr_rule(rule) and ':' not in rule:
            rule = provider.account_id + ':' + rule
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


class CloudProviderSecurityGroupListAPIView(SecurityGroupListAPIView):
    """
    Like the standard, top-level Security Group List API, this API will allow
    you to create and pull security groups. The only significant difference is
    that GET requests will only return security groups associated with the
    provider.

    *For regular users*, this will only show security groups owned by you and
    associated with the provider. *For admins*, this will pull all security
    groups on the provider, regardless of ownership.

    Additionally, admins may provide a query parameter and value
    `filter=default` to only show the security groups that have been designated
    as "default" groups to be attached to all hosts started using this provider

    See the standard, top-level Security Group API for further information.
    """
    filter_class = filters.SecurityGroupFilter

    def get_provider(self):
        pk = self.kwargs[self.lookup_field]
        return models.CloudProvider.objects.get(pk=pk)

    def get_queryset(self):
        provider = self.get_provider()

        # if admin, return all of the known default security groups on the
        # account
        if self.request.user.is_superuser:
            kwargs = {}
            if self.request.QUERY_PARAMS.get('filter', '') == 'default':
                kwargs['is_default'] = True
            return provider.security_groups.filter(**kwargs).with_rules()

        # if user, only get what they own
        else:
            return self.request.user.security_groups.filter(
                cloud_provider=provider
            ).with_rules()

    # Override the generic list API to inject the security groups
    # known by the cloud provider
    def list(self, request, *args, **kwargs):
        response = super(CloudProviderSecurityGroupListAPIView, self).list(
            request,
            *args,
            **kwargs)

        # only admins get to see all the groups on the account
        if not request.user.is_superuser:
            return response

        # Grab the groups from the provider and inject them into the response,
        # removing the known managed security groups first
        provider = self.get_provider()
        driver = provider.get_driver()
        provider_groups = driver.get_security_groups()
        for group in provider.security_groups.all():
            if group.name in provider_groups:
                del provider_groups[group.name]

        # Filter these too
        query_name = request.QUERY_PARAMS.get('name', '')
        for name, data in provider_groups.items():
            if query_name.lower() not in name.lower():
                del provider_groups[name]

        response.data['provider_groups'] = provider_groups
        return response


class CloudProviderVPCSubnetListAPIView(generics.ListAPIView):
    """
    """

    def get_provider(self):
        pk = self.kwargs[self.lookup_field]
        return models.CloudProvider.objects.get(pk=pk)

    def list(self, request, *args, **kwargs):
        provider = self.get_provider()
        driver = provider.get_driver()

        subnets = driver.get_vpc_subnets()
        return Response({
            'results': serializers.VPCSubnetSerializer(subnets, many=True).data
        })
