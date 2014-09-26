import django_filters
from .models import Formula


class FormulaFilter(django_filters.FilterSet):
    component = django_filters.CharFilter(name='components__sls_path')

    class Meta:
        model = Formula
        fields = ('title', 'uri', 'root_path', 'component', 'status')
