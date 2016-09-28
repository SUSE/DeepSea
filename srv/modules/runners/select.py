#!/usr/bin/python

import salt.client
import pprint
import os
import sys

def minions(host = False, **kwargs):
    """
    Some targets needs to match all minions within a search criteria.
    """
    criteria = []
    for key in kwargs:
        if key[0] == "_":
            continue
        criteria.append("I@{}:{}".format(key, kwargs[key]))

    search = " and ".join(criteria)

    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    local = salt.client.LocalClient()
    minions = local.cmd(search , 'pillar.get', [ 'id' ], expr_form="compound")

    sys.stdout = _stdout

    if host:
        return ([ k.split('.')[0] for k in minions.keys() ])
    return minions.keys()

def one_minion(**kwargs):
    """
    Some steps only need to be run once, but on any minion in a specific
    search.  Return the first matching key.
    """
    ret = minions(**kwargs)
    if ret:
        return ret[0]
    else:
        return 
