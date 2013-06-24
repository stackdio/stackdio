from nose.tools import raises
import requests
import json

class Test:
    def setup(self):
        print "setting up"

    def teardown(self):
        print "tearing down"

    def testURISuccess(self):
        r = requests.get('http://127.0.0.1:8000/api/roles/', auth=('testuser', 'password'))
        print "r.status_code == %i" % r.status_code
        assert r.status_code == 200

    def testNoneOrMoreExist(self):
        r = requests.get('http://127.0.0.1:8000/api/roles/', auth=('testuser', 'password'))
        if r.json()['count'] == 0:
            assert True
        else:
            assert len(r.json()['results']) > 0
