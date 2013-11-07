from django.conf.urls import patterns, include, url

from . import api

urlpatterns = patterns('formulas.api',

    url(r'^formulas/$',
        api.FormulaListAPIView.as_view(), 
        name='formula-list'),

    url(r'^formulas/(?P<pk>[0-9]+)/$', 
        api.FormulaDetailAPIView.as_view(), 
        name='formula-detail'),

    url(r'^formula_components/(?P<pk>[0-9]+)/$', 
        api.FormulaComponentDetailAPIView.as_view(), 
        name='formulacomponent-detail'),

    # List of publicly available formulas
    url(r'^formulas/public/$',
        api.FormulaPublicAPIView.as_view(), 
        name='formula-public'),
)


