from django.conf.urls import patterns, include, url

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns

# Enable admin interface
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    # Main application
    url(r'^$', 'core.views.index', name='index'),

    # Session views
    url(r'^login/$', 'core.views.login', name='login'),
    url(r'^logout/$', 'core.views.logout', name='logout'),

    # Admin interface
    url(r'^__private/admin/', include(admin.site.urls)),

    # API v1 root endpoint -- add additional URLs to urls.py in
    # the api_v1 module. 
    url(r'^api/', include('api_v1.urls')),
)

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])

##
# Default login/logout views. Without this you won't get the login/logout links
# in the views.
##
urlpatterns += patterns('',
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
)
