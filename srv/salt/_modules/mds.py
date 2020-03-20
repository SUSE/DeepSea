# -*- coding: utf-8 -*-

"""
This module adds some MDS specific functions. Determining the name is its
original use.
"""

from __future__ import absolute_import
import logging
# pylint: disable=incompatible-py3-code
log = logging.getLogger(__name__)


def get_name(host, i=0):
    """
    In most cases we use the hostname of the machine as the MDS name. However
    MDS names must not start with a digit, so filter those out and prefix them
    with "mds.".
    """
    name = host
    if host[0].isdigit():
        name = 'mds.{}'.format(name)
    if i != 0:
        name = '{}-{}'.format(name, i + 1)
    return name
