from django.conf.urls import patterns, include, url

# Enable admin interface
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'stackdio.views.home', name='home'),
    # url(r'^stackdio/', include('stackdio.foo.urls')),

    # Admin interface
    url(r'^__private/admin/', include(admin.site.urls)),
)
