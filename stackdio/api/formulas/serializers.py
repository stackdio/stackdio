# -*- coding: utf-8 -*-

# Copyright 2017,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import unicode_literals

import collections
import logging

import six
from django.db.models import URLField
from rest_framework import serializers
from stackdio.api.formulas import models, utils, validators
from stackdio.api.formulas.exceptions import InvalidFormula, InvalidFormulaComponent
from stackdio.core.mixins import CreateOnlyFieldsMixin
from stackdio.core.serializers import (
    StackdioHyperlinkedModelSerializer,
    StackdioParentHyperlinkedModelSerializer,
)

logger = logging.getLogger(__name__)


class FormulaSerializer(CreateOnlyFieldsMixin, StackdioHyperlinkedModelSerializer):
    # Link fields
    properties = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-properties')
    components = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-component-list',
        lookup_url_kwarg='parent_pk')
    valid_versions = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-valid-version-list',
        lookup_url_kwarg='parent_pk')
    action = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-action',
        lookup_url_kwarg='parent_pk')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-object-user-permissions-list',
        lookup_url_kwarg='parent_pk')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-object-group-permissions-list',
        lookup_url_kwarg='parent_pk')

    class Meta:
        model = models.Formula
        fields = (
            'id',
            'url',
            'title',
            'description',
            'uri',
            'ssh_private_key',
            'default_version',
            'root_path',
            'created',
            'modified',
            'properties',
            'components',
            'valid_versions',
            'action',
            'user_permissions',
            'group_permissions',
        )

        read_only_fields = (
            'title',
            'description',
            'default_version',
            'root_path',
            'status',
            'status_detail',
        )

        extra_kwargs = {
            'ssh_private_key': {'write_only': True},
        }

    # Add in our custom URL field
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping[URLField] = validators.FormulaURLField

    def validate(self, attrs):
        uri = attrs.get('uri')
        priv_key = attrs.get('ssh_private_key')

        # If a new private key is passed in with no URI,
        # then set the URI to that of the current instance
        if priv_key is not None and uri is None and self.instance is not None:
            uri = self.instance.uri

        if uri:
            with utils.get_gitfs(uri, priv_key) as gitfs:
                gitfs.update()

                logger.warning(gitfs.dir_list({'saltenv': 'base'}))

                errors = collections.defaultdict(list)

                try:
                    formula_info = validators.validate_specfile(gitfs)
                except InvalidFormula as e:
                    formula_info = None
                    errors['uri'].append(six.text_type(e))

                if formula_info:
                    # Add the info into the attrs
                    attrs['title'] = formula_info.title
                    attrs['description'] = formula_info.description
                    attrs['root_path'] = formula_info.root_path

                    # Then validate the components
                    for component in formula_info.components:
                        try:
                            validators.validate_component(gitfs, component)
                        except InvalidFormulaComponent as e:
                            errors['uri'].append(six.text_type(e))

                if errors:
                    raise serializers.ValidationError(errors)

        return attrs


class FormulaActionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    available_actions = ('update',)

    action = serializers.ChoiceField(available_actions, write_only=True)

    def to_representation(self, instance):
        """
        We just want to return a serialized formula object here.  Returning an object with
        the action in it just doesn't make much sense.
        """
        return FormulaSerializer(instance, context=self.context).to_representation(instance)

    def do_update(self):
        formula = self.instance
        formula.get_gitfs().update()

    def save(self, **kwargs):
        action = self.validated_data['action']

        formula_actions = {
            'update': self.do_update
        }

        formula_actions[action]()

        return self.instance


class FormulaVersionSerializer(serializers.ModelSerializer):
    formula = serializers.SlugRelatedField(slug_field='uri', queryset=models.Formula.objects.all())

    class Meta:
        model = models.FormulaVersion
        fields = (
            'formula',
            'version',
        )

        extra_kwargs = {
            'version': {'allow_null': True},
        }

    def validate(self, attrs):
        formula = attrs['formula']
        version = attrs.get('version')

        if version is None:
            # If it's None, this version should be deleted, so no need to do any further checks
            return attrs

        # Verify that the version is either a branch, tag, or commit hash
        if version not in formula.get_valid_versions():
            err_msg = '{0} cannot be found to be a branch, tag, or commit hash'.format(version)
            raise serializers.ValidationError({
                'version': [err_msg]
            })

        return attrs

    def create(self, validated_data):
        # Somewhat of a hack, but if the object already exists, we want to update the current one
        content_obj = validated_data['content_object']
        formula = validated_data['formula']
        try:
            version = content_obj.formula_versions.get(formula=formula)
            # Provide a way to remove a formula version (set it to none)
            if validated_data['version'] is None:
                version.delete()
                return version

            # Otherwise update it
            return self.update(version, validated_data)
        except models.FormulaVersion.DoesNotExist:
            pass

        if validated_data['version'] is None:
            raise serializers.ValidationError({
                'version': ['This field may not be null or blank.']
            })

        return super(FormulaVersionSerializer, self).create(validated_data)


class FormulaComponentSerializer(StackdioParentHyperlinkedModelSerializer):
    # Possibly required
    formula = serializers.SlugRelatedField(slug_field='uri',
                                           queryset=models.Formula.objects.all(), required=False)

    class Meta:
        model = models.FormulaComponent
        parent_attr = 'content_object'
        fields = (
            'formula',
            'title',
            'description',
            'sls_path',
            'order',
        )

        extra_kwargs = {
            'order': {'min_value': 0, 'default': serializers.CreateOnlyDefault(0)}
        }

    def validate(self, attrs):
        formula = attrs.get('formula', None)
        sls_path = attrs['sls_path']

        # Grab the formula versions out of the content object
        content_object = self.context.get('content_object')

        if content_object:
            # Only validate here if we have a content object to get formula versions from.
            formula_versions = content_object.formula_versions.all()

            version_map = {}

            # Build the map of formula -> version
            for version in formula_versions:
                version_map[version.formula] = version.version

            if formula is None:
                # Do some validation if the formula isn't passed in
                all_components = models.Formula.all_components(version_map)

                if sls_path not in all_components:
                    raise serializers.ValidationError({
                        'sls_path': ['sls_path `{0}` does not exist.'.format(sls_path)]
                    })

                # This means the component exists.  We'll check to make sure it doesn't
                # span multiple formulas.
                sls_formulas = all_components[sls_path]
                if len(sls_formulas) > 1:
                    err_msg = ('sls_path `{0}` is contained in multiple formulas.  '
                               'Please specify one.')
                    raise serializers.ValidationError({
                        'sls_path': [err_msg.format(sls_path)]
                    })

                # Be sure to throw the formula in!
                attrs['formula'] = sls_formulas[0]
            else:
                # If they provided a formula, validate the sls_path is in that formula
                validators.validate_formula_component(attrs, version_map)

        return attrs
