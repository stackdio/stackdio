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

from django.contrib.contenttypes.models import ContentType

from stackdio.core.notifications.tasks import generate_notifications


def trigger_event(event_tag, content_object):
    """
    Trigger an event on a given object.  Things may be listening for this event
    (like notification channels)
    """
    # Find the content type
    ctype = ContentType.objects.get_for_model(content_object)

    # Start up the celery task
    generate_notifications.si(event_tag, content_object.pk, ctype.id).apply_async()
