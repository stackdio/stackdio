from django.conf.urls import patterns, include, url

from .api import StackListAPIView, StackDetailAPIView
from .api import HostListAPIView

urlpatterns = patterns('stacks.api',

    url(r'^stacks/$',
        StackListAPIView.as_view(), 
        name='stack-list'),

    url(r'^stacks/(?P<pk>[0-9]+)/$', 
        StackDetailAPIView.as_view(), 
        name='stack-detail'),

    url(r'^hosts/$',
        HostListAPIView.as_view(), 
        name='host-list'),
)


