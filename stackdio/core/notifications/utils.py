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

import importlib
from collections import namedtuple

from django.conf import settings

from stackdio.core.config import StackdioConfigException
from stackdio.core.notifiers import BaseNotifier

NotifierConfig = namedtuple('NotifierConfig', ['name', 'class_path', 'options'])


# global registry of notifier configs
notifier_configs = {}

# global registry of notifier classes
notifier_classes = {}

# global registry of notifier instances
notifier_instances = {}


def get_notifier_list():
    notifier_config = settings.STACKDIO_CONFIG.get('notifiers', {})

    return notifier_config.keys()


def get_all_notifiers():
    notifier_list = get_notifier_list()

    ret = []

    for notifier in notifier_list:
        ret.append(get_notifier_config(notifier))

    return ret


def get_notifier_config(name):
    """
    Get the notifier config object from the notifier name
    :param name: the name of the notifier defined in the config file
    :rtype: stackdio.core.notifications.utils.NotifierConfig
    :return: the config object
    """
    if name not in notifier_configs:
        notifier_config = settings.STACKDIO_CONFIG.get('notifiers', {})

        if name not in notifier_config:
            raise StackdioConfigException('Notifier {} not found.'.format(name))

        ret = notifier_config[name]

        if not isinstance(ret, dict):
            raise StackdioConfigException('Notifier config for {} was not a dict.'.format(name))

        if 'class' not in ret:
            raise StackdioConfigException('Notifier config for {} is missing '
                                          'a `class` attribute.'.format(name))

        # options are optional, don't fail if they're not there
        options = ret.get('options', {})

        notifier_configs[name] = NotifierConfig(name, ret['class'], options)

    return notifier_configs[name]


def get_notifier_class(name):
    """
    Get the imported notifier class
    :param name: the notifier name
    :rtype: abc.ABCMeta
    :return: the notifier class object
    """
    if name not in notifier_classes:
        notifier_config = get_notifier_config(name)

        try:
            module_path, class_name = notifier_config.class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            notifier_class = getattr(module, class_name)
        except (ImportError, ValueError):
            msg = 'Could not import notifier: {0}'.format(notifier_config.class_path)
            raise StackdioConfigException(msg)

        if not issubclass(notifier_class, BaseNotifier):
            raise StackdioConfigException('The provided class for {} was not a '
                                          'subclass of BaseNotifier.'.format(name))

        notifier_classes[name] = notifier_class

    return notifier_classes[name]


def get_notifier_instance(name):
    """
    Get the instance of the given notifier
    :param name: the notifier name
    :rtype: BaseNotifier
    :return: the notifier instance
    """
    # Cache the notifier instance so we have 1 of each type of notifier instance
    if name not in notifier_instances:
        notifier_config = get_notifier_config(name)
        notifier_class = get_notifier_class(name)

        notifier_instances[name] = notifier_class(**notifier_config.options)

    return notifier_instances[name]
