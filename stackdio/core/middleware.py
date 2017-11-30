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

from __future__ import unicode_literals

import logging

from django.conf import settings
from django.http import HttpResponseRedirect

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

        if not self.should_allow(request) and not self.allow_from_user_agent(request):
            # Request not allowed - redirect to login
            return HttpResponseRedirect(self.get_redirect_url(request))

    @staticmethod
    def allow_from_user_agent(request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        if user_agent in settings.USER_AGENT_WHITELIST:
            request.META['ALLOWED_FROM_USER_AGENT'] = True
            return True
        else:
            return False

    def should_allow(self, request):
        user = request.user
        path = request.get_full_path()

        return path.startswith(settings.LOGIN_URL) \
            or path.startswith(settings.STATIC_URL) \
            or self.is_api_endpoint(path) \
            or user.is_authenticated()

    def is_api_endpoint(self, path):
        return path.startswith('/api/')

    def get_redirect_url(self, request):
        redirect_url = settings.LOGIN_URL
        if request.path != '/':
            redirect_url = '{0}?next={1}'.format(redirect_url, request.path)
        return redirect_url
