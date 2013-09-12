from django.conf.urls import patterns, include, url

from .api import (
    UserListAPIView,
    UserDetailAPIView,
    UserSettingsDetailAPIView,
    ChangePasswordAPIView,
)

urlpatterns = patterns('training.api',

    url(r'^users/$',
        UserListAPIView.as_view(), 
        name='user-list'),

    url(r'^users/(?P<pk>[0-9]+)/$', 
        UserDetailAPIView.as_view(), 
        name='user-detail'),

    url(r'^settings/$',
        UserSettingsDetailAPIView.as_view(), 
        name='usersettings-detail'),

    url(r'^settings/change_password/$',
        ChangePasswordAPIView.as_view(), 
        name='change_password'),

)
