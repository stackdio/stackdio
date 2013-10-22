import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Formula, FormulaComponent

logger = logging.getLogger(__name__)


class FormulaComponentSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = FormulaComponent
        fields = (
            'id',
            'title',
            'description',
            'formula',
            'sls_path',
        )


class FormulaSerializer(serializers.HyperlinkedModelSerializer):

    components = FormulaComponentSerializer(many=True)

    class Meta:
        model = Formula 
        fields = (
            'id',
            'url',
            'title',
            'description',
            'public',
            'uri',
            'root_path',
            'components',
            'created',
            'modified',
            'status',
            'status_detail',
        )

