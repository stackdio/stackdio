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

    # API root endpoint and additional app endpoints. Pretty much
    # each application will need to pull in their urls.py here
    # if they want to be added to be discoverable
    url(r'^api/', include('api_v1.urls')),

)
