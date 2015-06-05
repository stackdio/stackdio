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


import collections


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
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = recursive_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
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
