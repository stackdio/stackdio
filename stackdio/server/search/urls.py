from django.conf.urls import patterns, include, url

from . import api

urlpatterns = patterns('search.api',

    url(r'^search/$',
        api.SearchAPIView.as_view(), 
        name='search'),
)


