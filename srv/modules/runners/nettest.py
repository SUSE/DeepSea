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


def _minion_link_ipv4_parallel_pair(**kwargs):
    """
    Return list of [(minion, ipv4), ...] touples where no minion is listed twice in one result.

    The minion match the search criteria, and the ip addresses are from minions
    that also match the search criteria.

    Returned touple lists never include the same minion.
    Returned touples are never for minions with thier own ip addresses.
    Returned list of tuples never contain the the same minion or ip address in the list.

    Use case is network tests such as iperf.
    """
    node_ip_map = _get_minion_ipv4_dict(**kwargs)
    # Get a map to find node from ip
    ip_node_map = {}
    for node_id in node_ip_map.keys():
        for ipv4 in node_ip_map[node_id]:
            if ipv4 in ip_node_map.keys():
                msg = "Duplicate IP address on {node1} and {node2}".format(
                    node1 = node_id,
                    node2 = ip_node_map[ipv4]
                    )
                log.error(msg)
                continue
            ip_node_map[ipv4] = node_id
    tests_needed = set()
    for node_src in node_ip_map.keys():
        for node_dest in node_ip_map.keys():
            if node_dest == node_src:
                continue
            for ipv4 in node_ip_map[node_dest]:
                tests_needed.add((node_src, ipv4))
    output = []
    while len(tests_needed) > 0:
        busy_nodes = set()
        selected_tests = set()
        # now run through each test
        for test in tests_needed:
            node1 = test[0]
            if node1 in busy_nodes:
                continue
            ipv4 = test[1]
            node2 = ip_node_map[ipv4]
            if node2 in busy_nodes:
                continue
            busy_nodes.add(node1)
            busy_nodes.add(node2)
            selected_tests.add(test)
        output.append(list(selected_tests))
        tests_needed = tests_needed.difference(selected_tests)
    return output


def minion_link_ipv4_parallel_pair(**kwargs):
    """
    Return list of [(minionlist, ipv4list)] touples where no minion is listed twice in one result.
    minionlist and ipv4list are CSV items to make passing as comand line parameters easier.

    The minion match the search criteria, and the ip addresses are from minions
    that also match the search criteria.

    Returned touple lists never include the same minion.
    Returned touples are never for minions with thier own ip addresses.

    Use case is network tests such as iperf.
    """
    output = []
    list_tests_run = _minion_link_ipv4_parallel_pair(**kwargs)
    for test_run in list_tests_run:
        minion_list = []
        ipv4_list = []
        for minion, ipv4 in test_run:
            minion_list.append(minion)
            ipv4_list.append(ipv4)
        output.append((','.join(minion_list),','.join(ipv4_list)))
    return output
