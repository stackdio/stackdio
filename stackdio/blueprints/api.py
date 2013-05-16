from .models import *

from rest_framework import generics

from .serializers import UserSerializer

class BlueprintListAPIView(generics.ListAPIView):

    model = Blueprint
    serializer_class = BlueprintSerializer

