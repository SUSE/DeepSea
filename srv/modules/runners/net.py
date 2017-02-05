#!/usr/bin/python

import salt.client
from netaddr import IPNetwork, IPAddress

def ping(cluster = None):
    """
    Ping all addresses from all addresses on all minions.  If cluster is passed,
    restrict addresses to public and cluster networks.

    Note: Some optimizations could be done here in the multi module (such as 
    skipping the source and destination when they are the same).  However, the
    unoptimized version is taking ~2.5 seconds on 18 minions with 72 addresses 
    for success.  Failures take between 6 to 12 seconds.  Optimizations should
    focus there.

    TODO: Convert commented out print statements to log.debug
    """
    local = salt.client.LocalClient()
    if cluster:
        search = "I@cluster:{}".format(cluster)
        networks = local.cmd(search , 'pillar.item', [ 'cluster_network', 'public_network' ], expr_form="compound")
        #print networks
        total = local.cmd(search , 'grains.get', [ 'ipv4' ], expr_form="compound")
        #print addresses
        addresses = []
        for host in sorted(total.iterkeys()):
            if 'cluster_network' in networks[host]:
                addresses.extend(_address(total[host], networks[host]['cluster_network'])) 
            if 'public_network' in networks[host]:
                addresses.extend(_address(total[host], networks[host]['public_network'])) 
    else:
        search = "*"
        addresses = local.cmd(search , 'grains.get', [ 'ipv4' ], expr_form="compound")
    
        addresses = _flatten(addresses.values())
        # Lazy loopback removal - use ipaddress when adding IPv6
        addresses.remove('127.0.0.1')
    #print addresses
    results = local.cmd(search, 'multi.ping', addresses, expr_form="compound")
    #print results
    _summarize(len(addresses), results)

def _address(addresses, network):
    """
    Return all addresses in the given network
    
    Note: list comprehension vs. netaddr vs. simple
    """
    matched = []
    for address in addresses:
        if IPAddress(address) in IPNetwork(network):
            matched.append(address)
    return matched


def _flatten(l):
    """
    Flatten a array of arrays
    """
    return list(set(item for sublist in l for item in sublist))


def _summarize(total, results):
    """
    Summarize the successes, failures and errors across all minions
    """
    success = []
    failed = []
    errored = []
    for host in sorted(results.iterkeys()):
        if results[host]['succeeded'] == total:
            success.append(host)
        if 'failed' in results[host]:
            failed.append("{} from {}".format(results[host]['failed'], host)) 
        if 'errored' in results[host]:
            errored.append("{} from {}".format(results[host]['errored'], host)) 

    print "Succeeded: {} addresses from {} minions".format(total, len(success))
    if failed:
        print "Failed: \n    {}".format("\n    ".join(failed))
    if errored:
       print "Errored: \n    {}".format("\n    ".join(errored))
