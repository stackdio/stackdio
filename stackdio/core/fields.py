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

from django.db import models
from rest_framework import relations

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
