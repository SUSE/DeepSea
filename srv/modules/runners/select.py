#!/usr/bin/python

import salt.client
import pprint

def minions(**kwargs):
    """
    Just left as an example of massaging data for Jinja
    """
    criteria = []
    for key in kwargs:
        if key[0] == "_":
            continue
        criteria.append("I@{}:{}".format(key, kwargs[key]))

    search = " and ".join(criteria)

    local = salt.client.LocalClient()
    minions = local.cmd(search , 'pillar.get', [ 'id' ], expr_form="compound")
    return minions.keys()

def one_minion(**kwargs):
    ret = minions(**kwargs)
    if ret:
        return ret[0]
    else:
        return 
