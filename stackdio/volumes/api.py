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

# from .models import (
#     Volume,
# )

from .serializers import (
    VolumeSerializer, 
)

logger = logging.getLogger(__name__)


class VolumeListAPIView(generics.ListCreateAPIView):
    serializer_class = VolumeSerializer

    def get(self, request, *args, **kwargs):
        return Response([{'id': 1, 'title': 'Sample Volume 1', 'description': 'Sample volume description'},{'id': 2, 'title': 'Sample Volume 3', 'description': 'Sample volume description'},{'id': 3, 'title': 'Sample Volume 4', 'description': 'Sample volume description'},{'id':4, 'title': 'Sample Volume 10', 'description': 'Sample volume description'}])


class VolumeDetailAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = VolumeSerializer

    def get(self, request, *args, **kwargs):
        return Response({'title': 'Sample Volume'})

