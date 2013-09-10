import logging
import yaml
import os
import fnmatch

from collections import defaultdict

from django.conf import settings

from rest_framework import (
    generics,
    parsers,
    permissions,
)
from rest_framework.response import Response

from core import (
    renderers as core_renderers,
    exceptions as core_exceptions,
)

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
)

from .serializers import (
    CloudProviderSerializer,
    CloudProviderTypeSerializer,
    CloudInstanceSizeSerializer,
    CloudProfileSerializer,
    SnapshotSerializer,
    CloudZoneSerializer,
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
            raise core_exceptions.BadRequest(err_msg)



class CloudProviderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    model = CloudProvider
    serializer_class = CloudProviderSerializer
    permission_classes = (permissions.DjangoModelPermissions,)

    def destroy(self, *args, **kwargs):
        # ask the driver to clean up after itsef since it's no longer needed
        driver = self.get_object().get_driver()
        driver.destroy()

        ret = super(CloudProviderDetailAPIView, self).destroy(*args, **kwargs)

        # Recreate the salt cloud providers file to clean up this provider
        write_cloud_providers_file()
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

