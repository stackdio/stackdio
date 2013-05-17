from django.conf.urls import patterns, include, url

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

# Enable admin interface
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',

    # Admin interface
    url(r'^__private/admin/', include(admin.site.urls)),

    # API v1 root endpoint -- add additional URLs to urls.py in
    # the api_v1 module. 
    url(r'^api/', include('api_v1.urls')),

)
