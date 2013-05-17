from django.conf.urls import patterns, include, url

from .api import StackListAPIView, HostListAPIView

urlpatterns = patterns('stacks.api',

    url(r'^stacks$',
        StackListAPIView.as_view(), 
        name='stack-list'),

    url(r'^hosts$',
        HostListAPIView.as_view(), 
        name='host-list'),
)


