from django.conf.urls import patterns, include, url

from .api import BlueprintListAPIView

urlpatterns = patterns('blueprints.api',

    url(r'^$',
        BlueprintListAPIView.as_view(), 
        name='blueprint-list'),
)


