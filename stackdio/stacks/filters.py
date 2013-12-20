import django_filters
from .models import Stack

class StackFilter(django_filters.FilterSet):
    class Meta:
        model = Stack
        fields = ('title',)

