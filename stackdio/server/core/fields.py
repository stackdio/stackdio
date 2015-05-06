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


from django.db import models


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
