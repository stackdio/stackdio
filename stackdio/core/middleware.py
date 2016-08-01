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

from django.http import HttpResponseRedirect
from django.conf import settings

logger = logging.getLogger(__name__)


class LoginRedirectMiddleware(object):
    """
    Redirect any requests that aren't authenticated to the login URL
    """

    def process_request(self, request):
        assert hasattr(request, 'user'), (
            "The login redirect middleware requires authentication middleware "
            "to be installed. Edit your MIDDLEWARE_CLASSES setting to insert "
            "'django.contrib.auth.middleware.AuthenticationMiddleware' before "
            "'stackdio.core.middleware.LoginRedirectMiddleware'."
        )

        if self.should_redirect(request):
            return HttpResponseRedirect(self.get_redirect_url(request))

    def should_redirect(self, request):
        return not request.get_full_path().startswith(settings.LOGIN_URL) \
               and not self.is_api_endpoint(request.get_full_path()) \
               and not request.user.is_authenticated()

    def is_api_endpoint(self, path):
        return path.startswith('/api/')

    def get_redirect_url(self, request):
        redirect_url = settings.LOGIN_URL
        if request.path != '/':
            redirect_url = '{0}?next={1}'.format(redirect_url, request.path)
        return redirect_url
