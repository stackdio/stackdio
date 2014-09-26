import logging

from django.shortcuts import get_object_or_404

from rest_framework import (
    generics,
    permissions,
)

from core.permissions import AdminOrOwnerPermission
from .models import (
    Volume,
)
from .serializers import (
    VolumeSerializer,
)

logger = logging.getLogger(__name__)


class VolumeListAPIView(generics.ListAPIView):
    model = Volume
    serializer_class = VolumeSerializer

    def get_queryset(self):
        return Volume.objects.filter(stack__owner=self.request.user)


class VolumeAdminListAPIView(generics.ListAPIView):
    model = Volume
    serializer_class = VolumeSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        return self.model.objects.all()


class VolumeDetailAPIView(generics.RetrieveAPIView):
    model = Volume
    serializer_class = VolumeSerializer
    permission_classes = (AdminOrOwnerPermission,)

    # def get_object(self):
    #     return get_object_or_404(Volume,
    #                              pk=self.kwargs.get('pk'),
    #                              stack__owner=self.request.user)

