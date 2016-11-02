#!/usr/bin/python

import salt.client
import select
import logging

log = logging.getLogger(__name__)


def _get_minion_ipv4_dict(**kwargs):
    """
    Return dict of minion, ipv4 list

    The minion match the search criteria, and the ip addresses are from minions
    that also match the search criteria, but returned touples are never for
    minions with thier own ip addresses.
    """
    node_list = select.minions(**dict(kwargs, host=False))
    local_client = salt.client.LocalClient()
    node_ip_map = {}
    for node in node_list:
        ipv4_list = set()
        address_list = local_client.cmd(node, 'grains.get', ['ipv4'])
        if not node in address_list.keys():
            log.error("Failed getting ipv4 address from node:{node}".format(node=node))
            log.warning("Skipping all tests for node:{node}".format(node=node))
            continue
        for addr in address_list[node]:
            if addr == '127.0.0.1':
                continue
            ipv4_list.add(addr)
        node_ip_map[node] = ipv4_list
    return node_ip_map


def minion_link_ipv4(**kwargs):
    """
    Return list of (minion, ipv4) touples

    The minion match the search criteria, and the ip addresses are from minions
    that also match the search criteria, but returned touples are never for
    minions with thier own ip addresses.
    """
    node_ip_map = _get_minion_ipv4_dict(**kwargs)
    output = []
    for node_src in node_ip_map.keys():
        for node_dest in node_ip_map.keys():
            if node_dest == node_src:
                continue
            for ipv4 in node_ip_map[node_dest]:
                output.append((node_src, ipv4))
    return output


def minion_link_ipv4_parallel(**kwargs):
    """
    Return list of ([minion], ipv4) touples

    The minion match the search criteria, and the ip addresses are from minions
    that also match the search criteria, but returned touples are never for
    minions with thier own ip addresses.
    """
    node_ip_map = _get_minion_ipv4_dict(**kwargs)
    output = []
    node_set = set(node_ip_map.keys())
    for node_src in node_ip_map.keys():
        node_src_set = node_set.difference(set([node_src]))
        for ipv4 in node_ip_map[node_src]:
            output.append((','.join(node_src_set), ipv4))
    return output
