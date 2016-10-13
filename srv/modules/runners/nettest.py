#!/usr/bin/python

import salt.client
import select

def minion_link_ipv4(host = False, **kwargs):
    """
    Return list of (minion, ipv4) touples

    The minion match the search criteria, and the ip addresses are from minions
    that also match the search criteria, but returned touples are never for
    minions with thier own ip addresses.
    """
    node_list = select.minions(host, **kwargs)
    local_client = salt.client.LocalClient()
    node_ip_map = {}
    for node in node_list:
        ipv4_list = set()
        address_list = local_client.cmd(node, 'grains.get', ['ipv4'])
        for addr in address_list[node]:
            if addr == '127.0.0.1':
                continue
            ipv4_list.add(addr)
        node_ip_map[node] = ipv4_list
    output = []
    for node_src in node_list:
        for node_dest in node_list:
            if node_dest == node_src:
                continue
            for ipv4 in node_ip_map[node_dest]:
                output.append((node_src, ipv4))
    return output
