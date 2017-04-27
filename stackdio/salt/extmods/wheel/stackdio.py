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

from __future__ import absolute_import

# Import python libs
import os
import hashlib

# Import salt libs
import salt.key
import salt.crypt
import salt.utils


def pre_accept(id_=None, keysize=2048):
    if id_ is None:
        id_ = hashlib.sha512(os.urandom(32)).hexdigest()
    ret = {'priv': '',
           'pub': ''}
    trusted_dir = os.path.join(__opts__['pki_dir'], 'trusted_minion_keys')
    if not os.path.isdir(trusted_dir):
        os.makedirs(trusted_dir)
    priv = salt.crypt.gen_keys(trusted_dir, id_, keysize)
    pub = '{0}.pub'.format(priv[:priv.rindex('.')])
    with salt.utils.fopen(priv) as fp_:
        ret['priv'] = fp_.read()
    with salt.utils.fopen(pub) as fp_:
        ret['pub'] = fp_.read()
    os.remove(priv)
    return ret
