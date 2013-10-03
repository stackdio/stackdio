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
    CloudZoneListAPIView, 
    CloudZoneDetailAPIView,
    SnapshotListAPIView,
    SnapshotDetailAPIView,
    SecurityGroupListAPIView,
    SecurityGroupDetailAPIView,
    SecurityGroupRulesAPIView,
    CloudProviderSecurityGroupListAPIView,
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

    url(r'^providers/(?P<pk>[0-9]+)/security_groups/$', 
        CloudProviderSecurityGroupListAPIView.as_view(), 
        name='cloudprovider-securitygroup-list'),

    url(r'^instance_sizes/$',
        CloudInstanceSizeListAPIView.as_view(), 
        name='cloudinstancesize-list'),

    url(r'^instance_sizes/(?P<pk>[0-9]+)/$', 
        CloudInstanceSizeDetailAPIView.as_view(), 
        name='cloudinstancesize-detail'),

    url(r'^profiles/$',
        CloudProfileListAPIView.as_view(), 
        name='cloudprofile-list'),

    url(r'^profiles/(?P<pk>[0-9]+)/$', 
        CloudProfileDetailAPIView.as_view(), 
        name='cloudprofile-detail'),

    url(r'^snapshots/$',
        SnapshotListAPIView.as_view(), 
        name='snapshot-list'),

    url(r'^snapshots/(?P<pk>[0-9]+)/$', 
        SnapshotDetailAPIView.as_view(), 
        name='snapshot-detail'),

    url(r'^zones/$',
        CloudZoneListAPIView.as_view(), 
        name='cloudzone-list'),

    url(r'^zones/(?P<pk>[0-9]+)/$', 
        CloudZoneDetailAPIView.as_view(), 
        name='cloudzone-detail'),

    url(r'^security_groups/$',
        SecurityGroupListAPIView.as_view(), 
        name='securitygroup-list'),

    url(r'^security_groups/(?P<pk>[0-9]+)/$', 
        SecurityGroupDetailAPIView.as_view(), 
        name='securitygroup-detail'),

    url(r'^security_groups/(?P<pk>[0-9]+)/rules/$', 
        SecurityGroupRulesAPIView.as_view(), 
        name='securitygroup-rules'),

)


