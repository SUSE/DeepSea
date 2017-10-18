# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods,modernize-parse-error
#
# The salt-api calls functions with keywords that are not needed
# pylint: disable=unused-argument
"""
The deepsea_minions variable is in /srv/pillar/ceph/deepsea_minions.sls.  For
those sites with existing Salt minions that should not be storage hosts, this
variable can be customized to any Salt target.
"""

import sys
import os
import logging
import salt.client

log = logging.getLogger(__name__)


class DeepseaMinions(object):
    """
    The deepsea_minions pillar variable constrains which minions to use.
    """

    def __init__(self, **kwargs):
        """
        Initialize client and variables
        """
        self.local = salt.client.LocalClient()
        self.deepsea_minions = self._query()
        self.matches = self._matches()

    def _query(self):
        """
        Returns the value of deepsea_minions
        """
        # When search matches no minions, salt prints to stdout.
        # Suppress stdout.
        _stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

        # Relying on side effect - pylint: disable=unused-variable
        ret = self.local.cmd('*', 'saltutil.pillar_refresh')
        minions = self.local.cmd('*', 'pillar.get', ['deepsea_minions'],
                                 expr_form="compound")
        sys.stdout = _stdout
        for minion in minions:
            if minions[minion]:
                return minions[minion]

        log.error("deepsea_minions is not set")
        return []

    def _matches(self):
        """
        Returns the list of matched minions
        """
        if self.deepsea_minions:
            # When search matches no minions, salt prints to stdout.
            # Suppress stdout.
            _stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            result = self.local.cmd(self.deepsea_minions,
                                    'pillar.get',
                                    ['id'],
                                    expr_form="compound")
            sys.stdout = _stdout
            return result.keys()
        return []


def help_():
    """
    Usage
    """
    usage = ('salt-run deepsea_minions.show:\n\n'
             '    Displays deepsea_minions value\n'
             '\n\n'
             'salt-run deepsea_minions.matches:\n\n'
             '    Returns an array of matched minions\n'
             '\n\n')
    print usage
    return ""


def show(**kwargs):
    """
    Returns deepsea_minions value
    """
    target = DeepseaMinions()
    return target.deepsea_minions


def matches(**kwargs):
    """
    Returns array of matched minions
    """
    target = DeepseaMinions()
    return target.matches

__func_alias__ = {
                 'help_': 'help',
                 }
