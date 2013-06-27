import logging
import celery
from collections import defaultdict

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


class VolumeDetailAPIView(generics.RetrieveAPIView):
    serializer_class = VolumeSerializer
