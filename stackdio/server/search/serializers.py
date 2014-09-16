import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

from blueprints.models import Blueprint
from formulas.models import Formula
from stacks.models import Stack

logger = logging.getLogger(__name__)


class SearchSerializer(serializers.Serializer):
    pass


class SearchResultTypeField(serializers.Field):
    '''
    Tricks a read-only field into returning the value we want
    it to return instead of leveraging a value on the model.
    '''
    def __init__(self, result_type):
        self.result_type = result_type
        super(SearchResultTypeField, self).__init__(source='pk')

    def to_native(self, obj):
        return self.result_type


class BlueprintSearchSerializer(serializers.HyperlinkedModelSerializer):
    result_type = SearchResultTypeField('blueprint')
    class Meta:
        model = Blueprint
        fields = ('id', 'url', 'title', 'description', 'result_type')


class FormulaSearchSerializer(serializers.HyperlinkedModelSerializer):
    result_type = SearchResultTypeField('formula')
    class Meta:
        model = Formula
        fields = ('id', 'url', 'title', 'description', 'result_type')


class StackSearchSerializer(serializers.HyperlinkedModelSerializer):
    result_type = SearchResultTypeField('stack')
    class Meta:
        model = Stack
        fields = ('id', 'url', 'title', 'description', 'result_type')

