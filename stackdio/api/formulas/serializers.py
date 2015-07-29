# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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


import logging
from urlparse import urlsplit, urlunsplit

import git
from rest_framework import serializers

from stackdio.core.fields import PasswordField
from . import models, tasks

logger = logging.getLogger(__name__)


class FormulaComponentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.FormulaComponent
        fields = (
            'title',
            'description',
            'sls_path',
        )


class FormulaSerializer(serializers.HyperlinkedModelSerializer):
    # Non-model fields
    git_password = PasswordField(write_only=True, required=False, allow_blank=True)

    # Link fields
    properties = serializers.HyperlinkedIdentityField(view_name='formula-properties')
    components = serializers.HyperlinkedIdentityField(view_name='formula-component-list')
    action = serializers.HyperlinkedIdentityField(view_name='formula-action')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='formula-object-user-permissions-list')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='formula-object-group-permissions-list')

    class Meta:
        model = models.Formula
        fields = (
            'url',
            'title',
            'description',
            'uri',
            'private_git_repo',
            'git_username',
            'git_password',
            'access_token',
            'root_path',
            'created',
            'modified',
            'status',
            'status_detail',
            'properties',
            'components',
            'action',
            'user_permissions',
            'group_permissions',
        )

        read_only_fields = (
            'title',
            'description',
            'private_git_repo',
            'root_path',
            'status',
            'status_detail',
        )

        extra_kwargs = {
            'access_token': {'default': serializers.CreateOnlyDefault(False)},
        }

    def validate(self, attrs):
        uri = attrs['uri']
        git_username = attrs.get('git_username')

        errors = {}

        if git_username:
            # We only need validation if a non-empty username is provided
            access_token = attrs['access_token']
            git_password = attrs.get('git_password')

            if not access_token and not git_password:
                err_msg = 'Your git password is required if you\'re not using an access token.'
                errors.setdefault('access_token', []).append(err_msg)
                errors.setdefault('git_password', []).append(err_msg)

            if access_token and git_password:
                err_msg = 'If you are using an access_token, you may not provide a password.'
                errors.setdefault('access_token', []).append(err_msg)
                errors.setdefault('git_password', []).append(err_msg)

            # Add the git username to the uri if necessary
            parse_res = urlsplit(uri)
            if '@' not in parse_res.netloc:
                new_netloc = '{0}@{1}'.format(git_username, parse_res.netloc)
                attrs['uri'] = urlunsplit((
                    parse_res.scheme,
                    new_netloc,
                    parse_res.path,
                    parse_res.query,
                    parse_res.fragment
                ))

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class FormulaPropertiesSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if obj is not None:
            # Make it work two different ways.. ooooh
            if isinstance(obj, models.Formula):
                return obj.properties
            else:
                return obj
        return {}

    def to_internal_value(self, data):
        return data


class FormulaActionSerializer(serializers.Serializer):
    available_actions = ('update',)

    action = serializers.CharField(write_only=True)
    git_password = PasswordField(write_only=True, required=False, allow_blank=True)

    def validate(self, attrs):
        formula = self.instance
        action = attrs['action']

        if action not in self.available_actions:
            raise serializers.ValidationError({
                'action': ['{0} is not a valid action.'.format(action)]
            })

        git_password = attrs.get('git_password')
        if formula.private_git_repo and not formula.access_token:
            if not git_password:
                raise serializers.ValidationError({
                    'git_password': ['This is a required field on private formulas.']
                })

        return attrs

    def to_representation(self, instance):
        """
        We just want to return a serialized formula object here.  Returning an object with
        the action in it just doesn't make much sense.
        """
        return FormulaSerializer(
            instance,
            context=self.context
        ).to_representation(instance)

    def do_update(self):
        formula = self.instance
        git_password = self.validated_data.get('git_password', '')
        logger.debug(type(git_password))
        formula.set_status(
            models.Formula.IMPORTING,
            'Importing formula...this could take a while.'
        )
        tasks.update_formula.si(formula.id, git_password).apply_async()

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
        version = attrs['version']

        if version is None:
            # If it's None, this version should be deleted, so no need to do any further checks
            return attrs

        repo = git.Repo(formula.get_repo_dir())

        branches = [str(b.name) for b in repo.branches]
        tags = [str(t.name) for t in repo.tags]
        commit_hashes = [str(c.hexsha) for c in repo.iter_commits()]

        # Verify that the version is either a branch, tag, or commit hash

        if version not in branches + tags + commit_hashes:
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
