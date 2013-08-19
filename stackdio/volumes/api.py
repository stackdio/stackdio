import logging
import celery
from collections import defaultdict
from django.shortcuts import get_object_or_404

from rest_framework import (
    generics,
)

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
        return Volume.objects.filter(stack__user=self.request.user)


class VolumeDetailAPIView(generics.RetrieveAPIView):
    model = Volume
    serializer_class = VolumeSerializer

    def get_object(self):
        return get_object_or_404(Volume,
                                 pk=self.kwargs.get('pk'),
                                 stack__user=self.request.user)

