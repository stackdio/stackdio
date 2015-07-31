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


import logging

from django.contrib import messages, auth
from django.shortcuts import redirect
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class RootView(TemplateView):
    template_name = 'stackdio/home.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return super(RootView, self).get(request, *args, **kwargs)
        else:
            return redirect('login')


class LoginView(TemplateView):
    template_name = 'stackdio/login.html'

    def post(self, request):
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)

        if user is not None and user.is_active:
            # Login the user
            auth.login(request, user)
            messages.success(request, 'Successful login!')
            return redirect('index')
        else:
            # Failed
            messages.error(request, 'Sorry, your username and password are '
                                    'incorrect - please try again.')
            return self.get(request)


def logout(request):
    auth.logout(request)
    messages.success(request, 'You are now logged out. You may log in again '
                              'below.')
    return redirect('index')
