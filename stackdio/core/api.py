
from django.contrib.auth import get_user_model

from rest_framework.response import Response
from rest_framework import (
    generics,
    permissions,
    parsers,
    views,
)

from core.exceptions import BadRequest

from .serializers import (
    UserSerializer,
    UserSettingsSerializer,
)

from .models import (
    UserSettings,
)


class UserListAPIView(generics.ListAPIView):

    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)


class UserDetailAPIView(generics.RetrieveAPIView):

    model = get_user_model()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)


class UserSettingsDetailAPIView(generics.RetrieveUpdateAPIView):

    model = UserSettings
    serializer_class = UserSettingsSerializer

    def get_object(self):
        return self.request.user.settings


class ChangePasswordAPIView(views.APIView):
    '''
    API that handles changing your account password. Note that 
    only PUT requests are available on this endpoint. Below
    are the required parameters of the JSON object you will PUT.

    @curent_password: Your current password.
    @new_password: Your new password you want to change to.
    @confirm_password: Confirm your new password.
    '''

    parser_classes = (parsers.JSONParser,)

    def put(self, request, *args, **kwargs):
        current_password = request.DATA.get('current_password')
        new_password = request.DATA.get('new_password')
        confirm_password = request.DATA.get('confirm_password')

        errors = []
        if not current_password:
            errors.append('Current password field is required.')
        if not new_password:
            errors.append('New password field is required.')
        if not confirm_password:
            errors.append('New password confirmation field is required.')
        if errors:
            raise BadRequest(dict(errors=errors))

        if not request.user.check_password(current_password):
            errors.append('You entered an incorrect current password value.')
        if new_password != confirm_password:
            errors.append('Your new password and password confirmation fields do not match.')
        if errors:
            raise BadRequest(dict(errors=errors))

        # change the password
        request.user.set_password(new_password)
        request.user.save()

        return Response()
