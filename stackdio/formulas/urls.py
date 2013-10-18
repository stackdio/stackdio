from django.conf.urls import patterns, include, url

from .api import (
    FormulaListAPIView,
    FormulaDetailAPIView,
    FormulaComponentDetailAPIView,
)

urlpatterns = patterns('formulas.api',

    url(r'^formulas/$',
        FormulaListAPIView.as_view(), 
        name='formula-list'),

    url(r'^formulas/(?P<pk>[0-9]+)/$', 
        FormulaDetailAPIView.as_view(), 
        name='formula-detail'),

    url(r'^formula_components/(?P<pk>[0-9]+)/$', 
        FormulaComponentDetailAPIView.as_view(), 
        name='formulacomponent-detail'),
)


