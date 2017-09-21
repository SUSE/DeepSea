# -*- coding: utf-8 -*-
"""
This module is responsible for storing configuration options
"""
from __future__ import absolute_import


class Config(object):
    """
    Class that holds all configuration options
    """

    # the log file path location
    LOG_FILE_PATH = "/var/log/deepsea.log"

    # the log verbosity level
    LOG_LEVEL = "info"
