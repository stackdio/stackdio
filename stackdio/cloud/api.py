import logging
import yaml
import os
import fnmatch

from collections import defaultdict

from django.conf import settings
from django.http import Http404

from rest_framework import (
    generics,
    parsers,
    permissions,
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core import (
    renderers as core_renderers,
)

from core.exceptions import BadRequest, ResourceConflict

from .utils import (
    write_cloud_providers_file,
    write_cloud_profiles_file,
)

from .models import (
    CloudProvider,
    CloudProviderType,
    CloudInstanceSize,
    CloudProfile,
    Snapshot,
    CloudZone,
    SecurityGroup,
)

from .serializers import (
    CloudProviderSerializer,
    CloudProviderTypeSerializer,
    CloudInstanceSizeSerializer,
    CloudProfileSerializer,
    SnapshotSerializer,
    CloudZoneSerializer,
    SecurityGroupSerializer,
)

logger = logging.getLogger(__name__)


class CloudProviderTypeListAPIView(generics.ListAPIView):
    model = CloudProviderType
    serializer_class = CloudProviderTypeSerializer


class CloudProviderTypeDetailAPIView(generics.RetrieveAPIView):
    model = CloudProviderType
    serializer_class = CloudProviderTypeSerializer


class CloudProviderListAPIView(generics.ListCreateAPIView):
    model = CloudProvider
    serializer_class = CloudProviderSerializer
    permission_classes = (permissions.DjangoModelPermissions,)

    def post_save(self, obj, created=False):
        
        data = self.request.DATA
        files = self.request.FILES
        logger.debug(data)
        logger.debug(obj)

        # Lookup provider type
        try:
            driver = obj.get_driver()

            # Levarage the driver to generate its required data that
            # will be serialized down to yaml and stored in both the database
            # and the salt cloud providers file
            provider_data = driver.get_provider_data(data, files)
            
            # Generate the yaml and store in the database
            yaml_data = {}
            yaml_data[obj.slug] = provider_data
            obj.yaml = yaml.safe_dump(yaml_data,
                                      default_flow_style=False)
            obj.save()

            # Recreate the salt cloud providers file
            write_cloud_providers_file()

        except CloudProviderType.DoesNotExist, e:
            err_msg = 'Provider types does not exist.'
            logger.exception(err_msg)
            raise BadRequest(err_msg)


class CloudProviderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    model = CloudProvider
    serializer_class = CloudProviderSerializer
    permission_classes = (permissions.DjangoModelPermissions,)

    def destroy(self, *args, **kwargs):
        # TODO: need to prevent the delete if infrastructure is still up
        # that depends on this provider

        # ask the driver to clean up after itsef since it's no longer needed
        driver = self.get_object().get_driver()
        driver.destroy()

        ret = super(CloudProviderDetailAPIView, self).destroy(*args, **kwargs)

        # Recreate the salt cloud providers file to clean up this provider
        write_cloud_providers_file()
        write_cloud_profiles_file()
        return ret


class CloudInstanceSizeListAPIView(generics.ListAPIView):
    model = CloudInstanceSize
    serializer_class = CloudInstanceSizeSerializer


class CloudInstanceSizeDetailAPIView(generics.RetrieveAPIView):
    model = CloudInstanceSize
    serializer_class = CloudInstanceSizeSerializer


class CloudProfileListAPIView(generics.ListCreateAPIView):
    model = CloudProfile
    serializer_class = CloudProfileSerializer
    permission_classes = (permissions.DjangoModelPermissions,)

    def post_save(self, obj, created=False):
        write_cloud_profiles_file()


class CloudProfileDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    model = CloudProfile
    serializer_class = CloudProfileSerializer
    permission_classes = (permissions.DjangoModelPermissions,)

    def destroy(self, *args, **kwargs):
        # TODO: need to prevent the delete if infrastructure is still up
        # that depends on this profile
        ret = super(CloudProfileDetailAPIView, self).destroy(*args, **kwargs)

        # Recreate the salt cloud providers file
        write_cloud_profiles_file()
        return ret


class SnapshotListAPIView(generics.ListCreateAPIView):
    model = Snapshot
    serializer_class = SnapshotSerializer
    permission_classes = (permissions.DjangoModelPermissions,)


class SnapshotDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    model = Snapshot
    serializer_class = SnapshotSerializer
    permission_classes = (permissions.DjangoModelPermissions,)


class CloudZoneListAPIView(generics.ListAPIView):
    model = CloudZone
    serializer_class = CloudZoneSerializer


class CloudZoneDetailAPIView(generics.RetrieveAPIView):
    model = CloudZone
    serializer_class = CloudZoneSerializer


class SecurityGroupListAPIView(generics.ListCreateAPIView):
    '''
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
    '''

    model = SecurityGroup
    serializer_class = SecurityGroupSerializer
    parser_classes = (parsers.JSONParser,)

    def get_queryset(self):
        # if admin, get them all
        if self.request.user.is_superuser:
            return self.model.objects.all().with_rules()

        # if user, only get what they own
        else:
            return self.request.user.security_groups.all().with_rules()

    def create(self, request, *args, **kwargs):
        name = request.DATA.get('name')
        description = request.DATA.get('description')
        provider_id = request.DATA.get('cloud_provider')
        is_default = request.DATA.get('is_default', False)
        owner = request.user

        if not owner.is_superuser:
            is_default = False
        elif not isinstance(is_default, bool):
            is_default = False

        provider = CloudProvider.objects.get(id=provider_id)
        driver = provider.get_driver()

        # check if the group already exists in our DB first
        try:
            existing_group = SecurityGroup.objects.get(
                name=name,
                cloud_provider=provider
            )
            raise ResourceConflict('Security group already '
                                                  'exists.')
        except SecurityGroup.DoesNotExist:
            # doesn't exist in our database
            pass
             
        # check if the group exists on the provider
        provider_group = None
        try:
            provider_group = driver.get_security_groups([name])[name]
            logger.debug('Security group already exists on the '
                         'provider: {0!r}'.format(provider_group))

            # only admins are allowed to use an existing security group
            # for security purposes
            if not owner.is_superuser:
                raise PermissionDenied('Security group already exists on the '
                                       'cloud provider and only admins are '
                                       'allowed to import them.')
        except (KeyError, PermissionDenied):
            raise
        except Exception, e:
            logger.exception('WTF')
            # doesn't exist on the provider either, we'll create it now
            provider_group = None

        # admin is using an existing group, use the existing group id
        if provider_group:
            group_id = provider_group['id']
            description = provider_group['description']
        else:
            # create a new group
            group_id = driver.create_security_group(name, description)

        # create a new group in the DB
        group_obj = SecurityGroup.objects.create(
            name=name,
            description=description,
            group_id=group_id,
            cloud_provider=provider,
            owner=owner,
            is_default=is_default
        )

        serializer = SecurityGroupSerializer(group_obj, context={
            'request': request
        })
        return Response(serializer.data)


class SecurityGroupDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    '''
    Lists and creates new security groups.

    ### GET

    Retrieves the detail for the security group as defined by its
    `pk` identifier in the URL. The associated `rules` and 
    `active_hosts` fields will be populated like with the full
    list.

    # PUT

    Updates an existing security group's details. Currently, only
    the is_default field may be modified and only by admins.

    # TODO
    ### PUT (old, needs to be refactored)

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

    ### DELETE

    Removes the corresponding security group from stackd.io as well as
    from the underlying cloud provider. **NOTE** that if the security
    group is currently being used, then it can not be removed. You
    must first terminate all machines depending on the security group
    and then delete it.

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
    '''

    model = SecurityGroup
    serializer_class = SecurityGroupSerializer
    parser_classes = (parsers.JSONParser,)

    def get_object(self):
        kwargs = {'pk': self.kwargs[self.lookup_field]}
        if not self.request.user.is_superuser:
            kwargs['owner'] = self.request.user

        try:
            return self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            raise Http404()

    def update(self, request, *args, **kwargs):
        '''
        Allow admins to update the is_default field on security groups.
        '''
        if not request.user.is_superuser:
            raise PermissionDenied('Only admins are allowed to update '
                                   'security groups.')

        if 'is_default' not in request.DATA:
            raise BadRequest('is_default is the only field allowed to be updated.')

        is_default = request.DATA.get('is_default')
        if not isinstance(is_default, bool):
            raise BadRequest('is_default field must be a boolean.')

        # update the field value
        obj = self.get_object()
        obj.is_default = is_default
        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    def old_update(self, request, *args, **kwargs):
        logger.debug(request.DATA)
        security_group = self.get_object()
        driver = security_group.cloud_provider.get_driver()

        if request.DATA.get('action') == 'authorize':
            driver.authorize_security_group(security_group.name, request.DATA)
        elif request.DATA.get('action') == 'revoke':
            driver.revoke_security_group(security_group.name, request.DATA)
        else:
            raise BadRequest('Missing or invalid `action` parameter. Must be '
                             'one of \'authorize\' or \'revoke\'')

        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        sg = self.get_object()

        # Delete from AWS. This will throw the appropriate error
        # if the group is being used.
        driver = sg.cloud_provider.get_driver()
        driver.delete_security_group(sg.name)

        return super(SecurityGroupDetailAPIView, self).destroy(request, *args, **kwargs)

class CloudProviderSecurityGroupListAPIView(SecurityGroupListAPIView):
    '''
    Like the standard, top-level Security Group List API, this API will allow you 
    to create and pull security groups. The only significant difference is that
    GET requests will only return security groups associated with the provider.
    *For regular users*, this will only show security groups owned by you and
    associated with the provider. *For admins*, this will pull all security groups 
    on the provider, regardless of ownership.

    Additionally, admins may provide a query parameter and value 
    `filter=default` to only show the security groups that have been designated
    as "default" groups to be attached to all hosts started using this provider.

    See the standard, top-level Security Group API for further information.
    '''

    def get_provider(self):
        pk = self.kwargs[self.lookup_field]
        return CloudProvider.objects.get(pk=pk)

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
        
        # Grab the groups from the provider and inject them into the response
        driver = self.get_provider().get_driver()
        provider_groups = driver.get_security_groups()
        response.data['provider_groups'] = provider_groups
        return response

