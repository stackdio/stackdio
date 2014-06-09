from django.conf.urls import patterns, url

from . import api

urlpatterns = patterns(
    'stacks.api',

    url(r'^hosts/$',
        api.HostListAPIView.as_view(),
        name='host-list'),

    url(r'^hosts/(?P<pk>[0-9]+)/$',
        api.HostDetailAPIView.as_view(),
        name='host-detail'),

    url(r'^stacks/$',
        api.StackListAPIView.as_view(),
        name='stack-list'),

    url(r'^stacks/public/$',
        api.StackPublicListAPIView.as_view(),
        name='stack-public-list'),

    url(r'^stacks/(?P<pk>[0-9]+)/$',
        api.StackDetailAPIView.as_view(),
        name='stack-detail'),

    url(r'^stacks/(?P<pk>[0-9]+)/hosts/$',
        api.StackHostsAPIView.as_view(),
        name='stack-hosts'),

    url(r'^stacks/(?P<pk>[0-9]+)/fqdns/$',
        api.StackFQDNListAPIView.as_view(),
        name='stack-fqdns'),

    url(r'^stacks/(?P<pk>[0-9]+)/volumes/$',
        api.StackVolumesAPIView.as_view(),
        name='stack-volumes'),

    url(r'^stacks/(?P<pk>[0-9]+)/properties/$',
        api.StackPropertiesAPIView.as_view(),
        name='stack-properties'),

    url(r'^stacks/(?P<pk>[0-9]+)/history/$',
        api.StackHistoryAPIView.as_view(),
        name='stack-history'),

    url(r'^stacks/(?P<pk>[0-9]+)/provisioning_errors/$',
        api.StackProvisioningErrorsAPIView.as_view(),
        name='stack-provisioning-errors'),

    url(r'^stacks/(?P<pk>[0-9]+)/orchestration_errors/$',
        api.StackOrchestrationErrorsAPIView.as_view(),
        name='stack-orchestration-errors'),

    url(r'^stacks/(?P<pk>[0-9]+)/logs/$',
        api.StackLogsAPIView.as_view(),
        name='stack-logs'),

    url(r'^stacks/(?P<pk>[0-9]+)/logs/(?P<log>.*)$',
        api.StackLogsDetailAPIView.as_view(),
        name='stack-logs-detail'),

    url(r'^stacks/(?P<pk>[0-9]+)/action/$',
        api.StackActionAPIView.as_view(),
        name='stack-action'),

    url(r'^stacks/(?P<pk>[0-9]+)/security_groups/$',
        api.StackSecurityGroupsAPIView.as_view(),
        name='stack-security-groups'),
)
