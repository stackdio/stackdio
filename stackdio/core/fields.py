# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
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

from __future__ import absolute_import

import json
import logging
import warnings

import six
from django.conf import settings
from django.db import models
from django.db.utils import DEFAULT_DB_ALIAS
from rest_framework import relations
from rest_framework.fields import CharField

from stackdio.core.utils import PasswordStr
from stackdio.core.warnings import StackdioWarning

logger = logging.getLogger(__name__)


POSTGRES_ENGINES = ('django.db.backends.postgresql', 'django.db.backends.postgresql_psycopg2')


class DeletingFileField(models.FileField):
    """
    Borrowed from: https://gist.github.com/889692

    FileField subclass that deletes the referenced file when the model object
    itself is deleted.

    WARNING: Be careful using this class - it can cause data loss! This class
    makes at attempt to see if the file's referenced elsewhere, but it can get
    it wrong in any number of cases.
    """
    def contribute_to_class(self, cls, name, **kwargs):
        super(DeletingFileField, self).contribute_to_class(cls, name)
        models.signals.post_delete.connect(self.delete_file, sender=cls)

    def delete_file(self, instance, sender, **kwargs):
        file = getattr(instance, self.attname)
        # If no other object of this type references the file,
        # and it's not the default value for future objects,
        # delete it from the backend.
        if file and file.name != self.default and\
           not sender._default_manager.filter(**{self.name: file.name}):
            file.delete(save=False)
        elif file:
            # Otherwise, just close the file, so it doesn't tie up resources.
            file.close()


class JSONDict(dict):
    """
    Hack so repr() called by dumpdata will output JSON instead of
    Python formatted data.  This way fixtures will work!
    """
    def __repr__(self):
        return json.dumps(self)


class JSONUnicode(six.text_type):
    """
    As above
    """
    def __repr__(self):
        return json.dumps(self)


class JSONList(list):
    """
    As above
    """
    def __repr__(self):
        return json.dumps(self)


# Define our custom JSON field - this should just be used for
# storage, you can't search on this field
class SimpleJSONField(models.TextField):
    """
    Pulled from django-extensions, adapted for our needs
    """

    def __init__(self, *args, **kwargs):
        default = kwargs.get('default', None)
        if default is None:
            kwargs['default'] = '{}'
        elif isinstance(default, (list, dict)):
            kwargs['default'] = json.dumps(default)
        super(SimpleJSONField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if value is None or value == '':
            return {}
        elif isinstance(value, six.string_types):
            res = json.loads(value)
            if isinstance(res, dict):
                return JSONDict(**res)
            elif isinstance(res, six.string_types):
                return JSONUnicode(res)
            elif isinstance(res, list):
                return JSONList(res)
            return res
        else:
            return value

    def from_db_value(self, value, expression, connection, context):
        # Should be the same as to_python, just need to implement it
        return self.to_python(value)

    def get_prep_value(self, value):
        value = models.Field.get_prep_value(self, value)

        if value is None and self.null:
            return None
        # default values come in as strings; only non-strings should be
        # run through `dumps`
        if not isinstance(value, six.string_types):
            value = json.dumps(value)

        return value

    def deconstruct(self):
        name, path, args, kwargs = super(SimpleJSONField, self).deconstruct()
        if self.default == '{}':
            del kwargs['default']
        return name, path, args, kwargs


if settings.DATABASES[DEFAULT_DB_ALIAS]['ENGINE'] in POSTGRES_ENGINES:
    # postgres is available!  use the built-in json field

    from django.contrib.postgres.fields import JSONField as DjangoJSONField

    class JSONField(DjangoJSONField):
        pass

else:
    # no postgres :( for testing only, use our custom JSONField

    class JSONField(SimpleJSONField):
        _warned = False

        @staticmethod
        def __new__(cls, *args, **kwargs):
            if not cls._warned:
                warnings.warn(
                    'Using stackdio.core.fields.JSONField on a non-postgres database is NOT '
                    'recommended for production.  Please switch to postgres.',
                    StackdioWarning,
                )
                cls._warned = True

            # SimpleJSONField.__new__ goes all the way up to object(), so we don't need to
            # pass it any of the args or kwargs
            return SimpleJSONField.__new__(cls)


class PasswordField(CharField):
    def __init__(self, **kwargs):
        # Don't allow trimming of whitespace for passwords
        kwargs.pop('trim_whitespace', False)
        kwargs.setdefault('style', {})['input_type'] = 'password'
        self.trim_whitespace = False
        super(PasswordField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return PasswordStr(data)

    def to_representation(self, value):
        return PasswordStr(value)


class HyperlinkedField(relations.HyperlinkedIdentityField):
    """
    Sometimes we want to have a link field that doesn't have a lookup_field.
    This allows for that to happen.
    """
    def get_url(self, obj, view_name, request, format):
        return self.reverse(view_name, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        raise relations.ObjectDoesNotExist('%s should never have an associated object.'
                                           % self.__class__.__name__)


class HyperlinkedParentField(relations.HyperlinkedIdentityField):
    parent_attr = None
    parent_lookup_field = 'pk'
    parent_lookup_url_kwarg = None

    def __init__(self, view_name=None, **kwargs):
        self.parent_attr = kwargs.pop('parent_attr', self.parent_attr)

        assert self.parent_attr is not None, 'The `parent_attr` argument is required.'

        self.parent_attr = self.parent_attr.split('.')

        self.parent_lookup_field = kwargs.pop('parent_lookup_field', self.parent_lookup_field)

        # Set a default
        default_parent_lookup_url_kwarg = self.parent_lookup_url_kwarg \
            or 'parent_{}'.format(self.parent_lookup_field)

        # set the parameter
        self.parent_lookup_url_kwarg = kwargs.pop('parent_lookup_url_kwarg',
                                                  default_parent_lookup_url_kwarg)

        super(HyperlinkedParentField, self).__init__(view_name, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        middle_obj = obj

        for field in self.parent_attr:
            middle_obj = getattr(middle_obj, field)

        parent_obj = middle_obj
        parent_lookup_value = getattr(parent_obj, self.parent_lookup_field)

        lookup_value = getattr(obj, self.lookup_field)

        kwargs = {
            self.lookup_url_kwarg: lookup_value,
            self.parent_lookup_url_kwarg: parent_lookup_value,
        }
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        lookup_value = view_kwargs[self.lookup_url_kwarg]
        parent_lookup_value = view_kwargs[self.parent_lookup_url_kwarg]
        lookup_kwargs = {
            self.lookup_field: lookup_value,
            self.parent_lookup_field: parent_lookup_value,
        }
        return self.get_queryset().get(**lookup_kwargs)


class HyperlinkedPermissionsField(relations.HyperlinkedIdentityField):

    def __init__(self, view_name, permission_lookup_field, **kwargs):
        assert permission_lookup_field is not None, (
            'The `permission_lookup_field` argument is required.'
        )
        self.permission_lookup_field = permission_lookup_field
        self.permission_lookup_url_kwarg = kwargs.pop('permission_lookup_url_kwarg',
                                                      self.permission_lookup_field)
        super(HyperlinkedPermissionsField, self).__init__(view_name, **kwargs)

    def get_object(self, view_name, view_args, view_kwargs):
        raise relations.ObjectDoesNotExist('%s is a read only field, so the object isn\'t needed.'
                                           % self.__class__.__name__)


class HyperlinkedModelPermissionsField(HyperlinkedPermissionsField):

    def get_url(self, obj, view_name, request, format):
        # This is a little hack-y.  Not sure if I like it.
        permission_lookup_obj = obj.get('user') or obj.get('group')
        permission_lookup_value = getattr(permission_lookup_obj, self.permission_lookup_field)

        kwargs = {
            self.permission_lookup_url_kwarg: permission_lookup_value,
        }

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class HyperlinkedObjectPermissionsField(HyperlinkedPermissionsField):

    def get_url(self, obj, view_name, request, format):

        lookup_value = getattr(self.get_parent_object(), self.lookup_field)
        # This is a little hack-y.  Not sure if I like it.
        permission_lookup_obj = obj.get('user') or obj.get('group')
        permission_lookup_value = getattr(permission_lookup_obj, self.permission_lookup_field)

        kwargs = {
            self.lookup_url_kwarg: lookup_value,
            self.permission_lookup_url_kwarg: permission_lookup_value,
        }

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)

    def get_parent_object(self):
        view = self.context['view']
        return view.get_permissioned_object()
