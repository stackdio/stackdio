from rest_framework import generics

from .models import CloudProvider
from .serializers import CloudProviderSerializer

class CloudProviderListAPIView(generics.ListAPIView):

    model = CloudProvider
    serializer_class = CloudProviderSerializer


class CloudProviderDetailAPIView(generics.RetrieveDestroyAPIView):

    model = CloudProvider
    serializer_class = CloudProviderSerializer