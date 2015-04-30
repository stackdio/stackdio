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


from nose.tools import raises
import requests
import json


class Test:
    def setup(self):
        print "setting up"

    def teardown(self):
        print "tearing down"

    def testURISuccess(self):
        r = requests.get('http://127.0.0.1:8000/api/provider_types/', auth=('testuser', 'password'))
        print "r.status_code == %i" % r.status_code
        assert r.status_code == 200

    def testNoneOrMoreExist(self):
        r = requests.get('http://127.0.0.1:8000/api/provider_types/', auth=('testuser', 'password'))
        if r.json()['count'] == 0:
            assert True
        else:
            assert len(r.json()['results']) > 0
