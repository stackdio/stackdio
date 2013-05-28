import logging
import yaml

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
    get_cloud_providers,
    write_cloud_providers_file,
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

class CloudProviderTypeListAPIView(generics.ListAPIView):


    model = CloudProviderType
    serializer_class = CloudProviderTypeSerializer


class CloudProviderTypeDetailAPIView(generics.RetrieveAPIView):


    model = CloudProviderType
    serializer_class = CloudProviderTypeSerializer

class CloudProviderListAPIView(generics.ListCreateAPIView):


    model = CloudProvider
    serializer_class = CloudProviderSerializer

    def post_save(self, obj, created=False):
        
        data = self.request.DATA
        logger.debug(data)
        logger.debug(obj)
        provider_classes = get_cloud_providers()

        # lookup provider type
        try:
            provider_type = CloudProviderType.objects.get(id=data.get('provider_type'))

            # Add the private key to data
            data['private_key_path'] = obj.private_key_file.path

            for provider_class in provider_classes:
                logger.debug('PROVIDER CLASS {}'.format(provider_class))
                logger.debug('PROVIDER CLASS SHORT NAME {}'.format(provider_class.SHORT_NAME))
                if provider_class.SHORT_NAME == provider_type.type_name:
                    provider_data = provider_class.get_provider_data(data)
                    break
            
            yaml_data = {}
            yaml_data[obj.slug] = provider_data
            obj.yaml = yaml.safe_dump(yaml_data,
                                      default_flow_style=False)
            obj.save()

            # recreate the salt cloud providers file
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

class CloudProfileListAPIView(generics.ListAPIView):


    model = CloudProfile
    serializer_class = CloudProfileSerializer


class CloudProfileDetailAPIView(generics.RetrieveAPIView):


    model = CloudProfile
    serializer_class = CloudProfileSerializer
