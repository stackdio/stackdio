from django.conf.urls.defaults import patterns, url
from .api import BlueprintListAPIView


urlpatterns = patterns('blueprints.api',

    url(r'^$',
        BlueprintListAPIView.as_view(), 
        name='blueprint-list'),
)


