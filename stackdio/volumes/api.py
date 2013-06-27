import logging
import celery
from collections import defaultdict

from rest_framework import (
    generics,
    parsers,
    serializers,
)
from rest_framework.response import Response

from core.exceptions import ResourceConflict

from .models import (
    Volume,
)

from .serializers import (
    VolumeSerializer, 
)

logger = logging.getLogger(__name__)


class VolumeListAPIView(generics.ListCreateAPIView):
    model = Volume
    serializer_class = VolumeSerializer


class VolumeDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = VolumeSerializer
