import logging
import yaml
import os
import fnmatch

from collections import defaultdict

from django.conf import settings

from rest_framework import (
    generics,
    parsers,
)
from rest_framework.response import Response

from core import (
    renderers as core_renderers,
    exceptions as core_exceptions,
)

from .utils import (
    get_provider_type_and_class,
    write_cloud_providers_file,
    write_cloud_profiles_file,
    findRoles,
)

from .models import (
    CloudProvider,
    CloudProviderType,
    CloudInstanceSize,
    CloudProfile,
)

from .serializers import (
    CloudProviderSerializer,
    CloudProviderTypeSerializer,
    CloudInstanceSizeSerializer,
    CloudProfileSerializer,
)

logger = logging.getLogger(__name__)


class SaltRolesListAPIView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        slsFiles = []
        roles = []
        for root, dirs, files in os.walk(settings.SALT_ROOT):
            for filename in fnmatch.filter(files, '*.sls'):
                slsFiles.append(os.path.join(root, filename))

        for slsFile in slsFiles:
            for role in findRoles(slsFile, '^(?:(\s){4}-\s{1})(?!match\:)'):
                roles.append(role.split('-')[1].strip())

        return Response(roles)


class CloudProviderTypeListAPIView(generics.ListAPIView):
    model = CloudProviderType
    serializer_class = CloudProviderTypeSerializer


class CloudProviderTypeDetailAPIView(generics.RetrieveAPIView):
    model = CloudProviderType
    serializer_class = CloudProviderTypeSerializer


class CloudProfileScriptsListAPIView(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        scripts = [{'os': k, 'script': v} for k,v in [choice for choice in CloudProfile.SCRIPT_CHOICES]]
        return Response(scripts)


class CloudProviderListAPIView(generics.ListCreateAPIView):
    model = CloudProvider
    serializer_class = CloudProviderSerializer

    def post_save(self, obj, created=False):
        
        data = self.request.DATA
        files = self.request.FILES
        logger.debug(data)
        logger.debug(obj)

        # Lookup provider type
        try:
            provider_type, provider_class = \
                get_provider_type_and_class(data.get('provider_type'))

            # Instantiate the class with the saved ORM object
            provider = provider_class(obj)

            # Levarage the provider to generate its required data that
            # will be serialized down to yaml and stored in both the database
            # and the salt cloud providers file
            provider_data = provider.get_provider_data(data, files)
            
            # Generate the yaml and store in the database
            yaml_data = {}
            yaml_data[obj.slug] = provider_data
            obj.yaml = yaml.safe_dump(yaml_data,
                                      default_flow_style=False)
            obj.save()

            # Recreate the salt cloud providers file
            write_cloud_providers_file()

        except CloudProviderType.DoesNotExist, e:
            raise core_exceptions.BadRequest('Provider types does not exist.')


class CloudProviderDetailAPIView(generics.RetrieveDestroyAPIView):
    model = CloudProvider
    serializer_class = CloudProviderSerializer


class CloudInstanceSizeListAPIView(generics.ListAPIView):
    model = CloudInstanceSize
    serializer_class = CloudInstanceSizeSerializer


class CloudInstanceSizeDetailAPIView(generics.RetrieveAPIView):
    model = CloudInstanceSize
    serializer_class = CloudInstanceSizeSerializer


class CloudProfileListAPIView(generics.ListCreateAPIView):
    model = CloudProfile
    serializer_class = CloudProfileSerializer

    def post_save(self, obj, created=False):
        write_cloud_profiles_file()


class CloudProfileDetailAPIView(generics.RetrieveDestroyAPIView):
    model = CloudProfile
    serializer_class = CloudProfileSerializer


