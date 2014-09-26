import django_filters
from .models import Blueprint

class BlueprintFilter(django_filters.FilterSet):
    class Meta:
        model = Blueprint
        fields = ('title',)

