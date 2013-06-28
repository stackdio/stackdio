from django.conf.urls import patterns, include, url

from .api import (
    VolumeListAPIView, 
    VolumeDetailAPIView,
)

urlpatterns = patterns('volumes.api',

    url(r'^volumes/$',
        VolumeListAPIView.as_view(), 
        name='volume-list'),

    url(r'^volumes/(?P<pk>[0-9]+)/$', 
        VolumeDetailAPIView.as_view(), 
        name='volume-detail'),

)


