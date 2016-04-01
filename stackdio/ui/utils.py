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

from django.db.models import Model


def get_object_list(user, model_cls, pk_field='id'):
    assert issubclass(model_cls, Model)

    model_name = model_cls._meta.model_name

    object_list = []
    for obj in model_cls.objects.all():
        if user.has_perm('view_%s' % model_name, obj):
            object_list.append({
                'id': getattr(obj, pk_field),
                'can_delete': user.has_perm('delete_%s' % model_name, obj),
                'can_update': user.has_perm('update_%s' % model_name, obj),
            })
    return object_list
