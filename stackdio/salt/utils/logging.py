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

from __future__ import absolute_import, print_function, unicode_literals


import logging
from logging.handlers import WatchedFileHandler

from salt.log.setup import LOG_LEVELS


logger = logging.getLogger(__name__)
root_logger = logging.getLogger()


def setup_logfile_logger(log_path, log_level=None, log_format=None, date_format=None):
    """
    Set up logging to a file.
    """
    # Create the handler
    handler = WatchedFileHandler(log_path, mode='a', encoding='utf-8', delay=0)

    if log_level:
        # Grab and set the level
        level = LOG_LEVELS.get(log_level.lower(), logging.ERROR)
        handler.setLevel(level)

    # Set the default console formatter config
    if not log_format:
        log_format = '%(asctime)s [%(name)s][%(levelname)s] %(message)s'
    if not date_format:
        date_format = '%Y-%m-%d %H:%M:%S'

    formatter = logging.Formatter(log_format, datefmt=date_format)

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    return handler
