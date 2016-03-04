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

import logging

from django.db import models
from rest_framework import relations
from rest_framework.fields import CharField

from stackdio.core.utils import PasswordStr

logger = logging.getLogger(__name__)


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

    def __init__(self, view_name, parent_relation_field, **kwargs):
        assert parent_relation_field is not None, (
            'The `parent_relation_field` argument is required.'
        )

        self.parent_relation_field = parent_relation_field.split('.')
        self.parent_lookup_field = kwargs.pop('parent_lookup_field', 'pk')
        self.parent_lookup_url_kwarg = kwargs.pop('parent_lookup_url_kwarg',
                                                  self.parent_lookup_field)
        super(HyperlinkedParentField, self).__init__(view_name, **kwargs)

    def get_url(self, obj, view_name, request, format):
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk is None:
            return None

        middle_obj = obj

        for field in self.parent_relation_field:
            middle_obj = getattr(middle_obj, field)

        parent_obj = middle_obj

        parent_lookup_value = getattr(parent_obj, self.parent_lookup_field)
        lookup_value = getattr(obj, self.lookup_field)

        kwargs = {
            self.parent_lookup_url_kwarg: parent_lookup_value,
            self.lookup_url_kwarg: lookup_value,
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
