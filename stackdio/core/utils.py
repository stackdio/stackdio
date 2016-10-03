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


import collections

import six
from django.conf import settings
from django.conf.urls import url
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie


class FakeQuerySet(object):
    """
    Fake queryset class to make filters magically work even though we just have a list
    """
    def __init__(self, model, groups):
        self.model = model
        self._groups = groups

    def __len__(self):
        return len(self._groups)

    def __getitem__(self, item):
        return self._groups[item]

    def all(self):
        return self

    def filter(self, **kwargs):
        """
        This is VERY naive, but it works for what we want
        """
        ret = []
        for group in self._groups:
            for k, v in kwargs.items():
                spl = k.split('__')
                if len(spl) > 1:
                    if spl[1] == 'icontains':
                        if v.lower() in getattr(group, spl[0]).lower():
                            ret.append(group)
                else:
                    if getattr(group, k) == v:
                        ret.append(group)
        return FakeQuerySet(self.model, ret)


class PasswordStr(six.text_type):
    """
    Used so that passwords aren't logged in the celery task log
    """

    def __repr__(self):
        return '*' * len(self)


def recursively_sort_dict(d):
    ret = collections.OrderedDict()
    for k, v in sorted(d.items(), key=lambda x: x[0]):
        if isinstance(v, dict):
            ret[k] = recursively_sort_dict(v)
        else:
            ret[k] = v
    return ret


# Thanks Alex Martelli
# http://goo.gl/nENTTt
def recursive_update(d, u):
    """
    Recursive update of one dictionary with another. The built-in
    python dict::update will erase existing values.
    :param d: the base dict object  -  *Will be changed*
    :param u: the secondary dict object, to be merged into d.  Values in d will be overwritten by u.
    :return: the merged dict object
    :rtype: dict
    """
    for key, new_val in u.items():
        old_val = d.get(key, {})
        if isinstance(new_val, collections.Mapping) and isinstance(old_val, collections.Mapping):
            # Only make the recursive call if both the old and new values are mappings
            d[key] = recursive_update(old_val, new_val)
        else:
            # Otherwise just directly assign the new value
            d[key] = new_val
    return d


def get_urls(urllist, pre=''):
    """
    Return a list of all urls in a given urlpatterns object.  Will recurse down the include tree.
    :param urllist: the original list of url patterns
    :param pre: the string to append to the front of the url at the given level
    :return: a generator that yields strings of full url patterns
    """
    for entry in urllist:
        pattern = entry.regex.pattern.replace('^', '').replace('$', '')
        yield pre + pattern
        if hasattr(entry, 'url_patterns'):
            for subentry in get_urls(entry.url_patterns, pre + pattern):
                yield subentry


def cached_url(regex, view, kwargs=None, name=None, prefix='',
               timeout=settings.CACHE_MIDDLEWARE_SECONDS, user_sensitive=True):
    view = cache_page(timeout)(view)
    if user_sensitive:
        view = vary_on_cookie(view)
    return url(regex, view, kwargs, name, prefix)
