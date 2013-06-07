from django.conf.urls import patterns, include, url

from .api import (
    CloudProviderTypeListAPIView, 
    CloudProviderTypeDetailAPIView,
    CloudProviderListAPIView, 
    CloudProviderDetailAPIView,
    CloudInstanceSizeListAPIView, 
    CloudInstanceSizeDetailAPIView,
    CloudProfileListAPIView, 
    CloudProfileDetailAPIView,
    CloudProfileScriptsListAPIView,
    SaltRolesListAPIView,
)


urlpatterns = patterns('cloud.api',

    url(r'^provider_types/$',
        CloudProviderTypeListAPIView.as_view(), 
        name='cloudprovidertype-list'),

    url(r'^provider_types/(?P<pk>[0-9]+)/$', 
        CloudProviderTypeDetailAPIView.as_view(), 
        name='cloudprovidertype-detail'),

    url(r'^providers/$',
        CloudProviderListAPIView.as_view(), 
        name='cloudprovider-list'),

    url(r'^providers/(?P<pk>[0-9]+)/$', 
        CloudProviderDetailAPIView.as_view(), 
        name='cloudprovider-detail'),

    url(r'^instance_sizes/$',
        CloudInstanceSizeListAPIView.as_view(), 
        name='cloudinstancesize-list'),

    url(r'^instance_sizes/(?P<pk>[0-9]+)/$', 
        CloudInstanceSizeDetailAPIView.as_view(), 
        name='cloudinstancesize-detail'),

    url(r'^profiles/$',
        CloudProfileListAPIView.as_view(), 
        name='cloudprofile-list'),

    url(r'^profile_scripts/$',
        CloudProfileScriptsListAPIView.as_view(), 
        name='cloudprofilescripts-list'),

    url(r'^profiles/(?P<pk>[0-9]+)/$', 
        CloudProfileDetailAPIView.as_view(), 
        name='cloudprofile-detail'),

    url(r'^roles/$',
        SaltRolesListAPIView.as_view(), 
        name='saltroles-list'),

)


