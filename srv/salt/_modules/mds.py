# -*- coding: utf-8 -*-

"""
This module adds some MDS specific functions. Determining the name is its
original use.
"""

import logging
# pylint: disable=incompatible-py3-code
log = logging.getLogger(__name__)


def get_name(host):
    """
    In most cases we use the hostname of the machine as the MDS name. However
    MDS names must not start with a digit, so filter those out and prefix them
    with "mds.".
    """
    if host[0].isdigit():
        return 'mds.{}'.format(host)
    else:
        return host
