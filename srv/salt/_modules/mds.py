# -*- coding: utf-8 -*-

"""
This module adds some MDS specific functions. Determining the name is its
original use.
"""

from __future__ import absolute_import
import logging
from os import listdir
from os.path import isdir, isfile
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


def get_local_daemon_count():
    p = '/var/lib/ceph/mds/'
    dirs = [d for d in listdir(p) if isdir('{}/{}'.format(p, d)) and
            isfile('{}/{}/keyring'.format(p, d))]
    return len(dirs)
