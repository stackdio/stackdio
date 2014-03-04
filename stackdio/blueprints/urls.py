from django.conf.urls import patterns, url

from . import api

urlpatterns = patterns(
    'blueprints.api',

    url(r'^blueprints/$',
        api.BlueprintListAPIView.as_view(),
        name='blueprint-list'),

    url(r'^blueprints/(?P<pk>[0-9]+)/$',
        api.BlueprintDetailAPIView.as_view(),
        name='blueprint-detail'),

    url(r'^blueprints/(?P<pk>[0-9]+)/properties/$',
        api.BlueprintPropertiesAPIView.as_view(),
        name='blueprint-properties'),

    # List of publicly available blueprints
    url(r'^blueprints/public/$',
        api.BlueprintPublicAPIView.as_view(),
        name='blueprint-public-list'),
)
