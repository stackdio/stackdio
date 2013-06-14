from django.conf.urls import patterns, include, url

from .api import (
    StackListAPIView, 
    StackDetailAPIView,
    StackHostsAPIView, 
    StackDetailAPIView,
    HostListAPIView, 
    HostDetailAPIView,
    SaltRoleListAPIView,
    SaltRoleDetailAPIView,
)

urlpatterns = patterns('stacks.api',

    url(r'^hosts/$',
        HostListAPIView.as_view(), 
        name='host-list'),

    url(r'^hosts/(?P<pk>[0-9]+)/$', 
        HostDetailAPIView.as_view(), 
        name='host-detail'),

    url(r'^stacks/$',
        StackListAPIView.as_view(), 
        name='stack-list'),

    url(r'^stacks/(?P<pk>[0-9]+)/$', 
        StackDetailAPIView.as_view(), 
        name='stack-detail'),

    url(r'^stacks/(?P<pk>[0-9]+)/hosts$', 
        StackHostsAPIView.as_view(), 
        name='stack-hosts'),

    url(r'^roles/$', 
        SaltRoleListAPIView.as_view(), 
        name='saltrole-list'),

    url(r'^roles/(?P<pk>[0-9]+)/$', 
        SaltRoleDetailAPIView.as_view(), 
        name='saltrole-detail'),

)


