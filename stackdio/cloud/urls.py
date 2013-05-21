from django.conf.urls import patterns, include, url

from .api import CloudProviderListAPIView, CloudProviderDetailAPIView

urlpatterns = patterns('cloud.api',

    url(r'^providers/$',
        CloudProviderListAPIView.as_view(), 
        name='provider-list'),

    url(r'^providers/(?P<pk>[0-9]+)/$', 
        CloudProviderDetailAPIView.as_view(), 
        name='provider-detail'),


)


