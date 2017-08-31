# -*- coding: utf-8 -*-

import salt.client
import logging
import pprint
import os
import sys
import re

log = logging.getLogger(__name__)

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


def public_addresses(tuples = False, host = False, **kwargs):

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
    result = local.cmd(search , 'public.address', [], expr_form="compound")

    sys.stdout = _stdout

    if tuples:
        if host:
            addresses = [ [k.split('.')[0],v] for k, v in result.items() ]
        else:
            addresses = [ [k,v] for k, v in result.items() ]
    else:
        addresses = []
        for entry in result:
            addresses.append(result[entry])
    return addresses


def attr(host = False, **kwargs):
    """
    Return a paired list of minions and a given attribute
    """
    criteria = []
    attribute = None
    for key in kwargs:
        if key[0] == "_":
            continue
        if key == 'attr':
            attribute = kwargs['attr']
            continue
        criteria.append("I@{}:{}".format(key, kwargs[key]))

    search = " and ".join(criteria)

    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    local = salt.client.LocalClient()
    minions = local.cmd(search , 'pillar.get', [ attribute ], expr_form="compound")

    sys.stdout = _stdout

    if host:
        pairs = [ [k.split('.')[0],v] for k, v in minions.items() ]
    else:
        pairs = [ [k,v] for k, v in minions.items() ]
    return pairs

def from_(pillar, *args, **kwargs):
    """
    Return a list of roles and corresponding grains for the provided pillar
    argument.

    salt-run select.from rgw_configurations host fqdn
    salt-run select.from pillar=data, attr="host, fqdn"

    Note: Support the second form because Jinja hates us.
    """

    if 'attr' in kwargs:
        args = re.split(',\s*', kwargs['attr'])

    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    local = salt.client.LocalClient()
    search = "I@roles:master"
    result = local.cmd(search , 'pillar.get', [ pillar ], expr_form="compound")

    results = []
    sys.stdout = _stdout
    for master in result:
        if result[master]:
            for role in result[master].keys():
                minion_list = minions(roles=role)
                for minion in minion_list:
                    grains_result = local.cmd(minion , 'grains.item',  list(args)).values()[0]
                    small = [ role ]
                    for arg in list(args):
                        small.append(grains_result[arg])
                    results.append(small)
                
    if results:
        return results
    return [ [ None ] * (1 + len(args)) ]

__func_alias__ = {
                 'from_': 'from',
                 }
