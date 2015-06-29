# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import generics
from rest_framework.response import Response

from . import serializers


class UserListAPIView(generics.ListAPIView):
    queryset = get_user_model().objects.exclude(id=settings.ANONYMOUS_USER_ID)
    serializer_class = serializers.PublicUserSerializer
    lookup_field = 'username'


class UserDetailAPIView(generics.RetrieveAPIView):
    queryset = get_user_model().objects.exclude(id=settings.ANONYMOUS_USER_ID)
    serializer_class = serializers.PublicUserSerializer
    lookup_field = 'username'


class GroupListAPIView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    lookup_field = 'name'


class GroupDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    lookup_field = 'name'


class CurrentUserDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordAPIView(generics.GenericAPIView):
    """
    API that handles changing your account password. Note that
    only POST requests are available on this endpoint. Below
    are the required parameters of the JSON object you will PUT.

    @current_password: Your current password.
    @new_password: Your new password you want to change to.
    """

    serializer_class = serializers.ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        instance = request.user
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
