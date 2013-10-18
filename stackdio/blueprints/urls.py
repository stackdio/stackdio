from django.conf.urls import patterns, include, url

from .api import (
    BlueprintListAPIView,
    BlueprintDetailAPIView,
)

urlpatterns = patterns('blueprints.api',

    url(r'^blueprints/$',
        BlueprintListAPIView.as_view(), 
        name='blueprint-list'),

    url(r'^blueprints/(?P<pk>[0-9]+)/$', 
        BlueprintDetailAPIView.as_view(), 
        name='blueprint-detail'),
)


