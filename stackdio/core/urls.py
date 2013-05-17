from django.conf.urls import patterns, include, url

from .api import UserListAPIView, UserDetailAPIView

urlpatterns = patterns('training.api',

    url(r'^users/$',
        UserListAPIView.as_view(), 
        name='user-list'),

    url(r'^users/(?P<pk>[0-9]+)/$', 
        UserDetailAPIView.as_view(), 
        name='user-detail'),

)
