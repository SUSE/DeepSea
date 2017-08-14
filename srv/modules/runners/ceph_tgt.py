# -*- coding: utf-8 -*-

import salt.client
import sys
import os
import logging

log = logging.getLogger(__name__)

class CephTgt(object):
    """
    """

    def __init__(self, **kwargs):
        """
        """
        self.local = salt.client.LocalClient()
        self.ceph_tgt = self._query()
        self.matches = self._matches()
       

    def _query(self):
        """
        """
        # When search matches no minions, salt prints to stdout.  
        # Suppress stdout.
        _stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

        ret = self.local.cmd('*' , 'saltutil.pillar_refresh')
        minions = self.local.cmd('*' , 'pillar.get', [ 'ceph_tgt' ], 
                            expr_form="compound")
        sys.stdout = _stdout
        for minion in minions:
            if minions[minion]:
                return minions[minion]
           
        
        log.error("ceph_tgt is not set")
        return []

    def _matches(self):
        """
        """
        if self.ceph_tgt:
            # When search matches no minions, salt prints to stdout.  
            # Suppress stdout.
            _stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            matches = self.local.cmd(self.ceph_tgt , 'pillar.get', [ 'id' ], 
                                expr_form="compound")
            sys.stdout = _stdout
            return matches.keys()
        return []

def show(**kwargs):
    """
    """
    target = CephTgt()
    return target.ceph_tgt

def matches(**kwargs):
    target = CephTgt()
    return target.matches
