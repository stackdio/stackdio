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

from functools import wraps

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache


def django_cache(cache_key, timeout=None):
    """
    decorator to cache the result of a function in the django cache
    """

    def wrapper(func):

        @wraps(func)
        def wrapped(self):
            ctype = ContentType.objects.get_for_model(self)

            final_cache_key = cache_key.format(ctype=ctype.pk, id=self.id)

            cached_item = cache.get(final_cache_key)

            if cached_item is None:
                cached_item = func(self)
                cache.set(final_cache_key, cached_item, timeout)

            return cached_item

        return wrapped

    return wrapper
