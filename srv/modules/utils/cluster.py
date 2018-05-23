# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
#
# The salt-api calls functions with keywords that are not needed
# pylint: disable=unused-argument
"""
Functions related to the ceph cluster
"""


from __future__ import absolute_import
from __future__ import print_function
import logging


log = logging.getLogger(__name__)


def name():
    """
    Return the cluster name from the ceph namespace, original namespace
    or default to 'ceph'
    """
    if 'ceph' in __pillar__ and 'cluster' in __pillar__['ceph']:
        return __pillar__['ceph']['cluster']
    if 'cluster' in __pillar__:
        return __pillar__['cluster']
    return 'ceph'


def help_():
    """
    Usage
    """
    usage = ('salt-run cluster.name: \n\n'
             '    Returns a name of the cluster\n'
             '\n\n')
    print(usage)
    return ""


__func_alias__ = {
    'help_': 'help',
}
