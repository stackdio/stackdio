from django.conf.urls import patterns, url
from . import api

urlpatterns = patterns(
    'training.api',

    url(r'^users/$',
        api.UserListAPIView.as_view(),
        name='user-list'),

    url(r'^users/(?P<pk>[0-9]+)/$',
        api.UserDetailAPIView.as_view(),
        name='user-detail'),

    url(r'^settings/$',
        api.UserSettingsDetailAPIView.as_view(),
        name='usersettings-detail'),

    url(r'^settings/change_password/$',
        api.ChangePasswordAPIView.as_view(),
        name='change_password'),

    url(r'^version/$',
        api.VersionAPIView.as_view(),
        name='version'),

)
