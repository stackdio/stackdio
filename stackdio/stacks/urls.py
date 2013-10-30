from django.conf.urls import patterns, include, url

from . import api

urlpatterns = patterns('stacks.api',

    url(r'^hosts/$',
        api.HostListAPIView.as_view(), 
        name='host-list'),

    url(r'^hosts/(?P<pk>[0-9]+)/$', 
        api.HostDetailAPIView.as_view(), 
        name='host-detail'),

    url(r'^stacks/$',
        api.StackListAPIView.as_view(), 
        name='stack-list'),

    url(r'^stacks/(?P<pk>[0-9]+)/$', 
        api.StackDetailAPIView.as_view(), 
        name='stack-detail'),

    url(r'^stacks/(?P<pk>[0-9]+)/hosts/$', 
        api.StackHostsAPIView.as_view(), 
        name='stack-hosts'),

    url(r'^stacks/(?P<pk>[0-9]+)/volumes/$', 
        api.StackVolumesAPIView.as_view(), 
        name='stack-volumes'),
)

