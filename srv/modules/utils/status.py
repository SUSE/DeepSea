# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4
"""
Helper for upgrade.status and status.report runners
"""
from __future__ import absolute_import
import salt.client


def get_sys_versions(cluster_name='ceph'):
    """
    Query grains, run commands for current versions
    """
    local = salt.client.LocalClient()
    search = "I@cluster:{}".format(cluster_name)
    # grains might be inaccurate or not up to date because they are designed
    # to hold static data about the minion. In case of an update though, the
    # data will change.  grains are refreshed on reboot(restart of the service).
    os_codename = local.cmd(search, 'grains.get', ['oscodename'], tgt_type="compound")

    # If any nodes are down, the value of each item in the dict will be False.
    # We can use this to modify the search string for the subsequent two calls,
    # which will save 30 seconds of execution time (15 seconds per call) if any
    # nodes are down.  So if any nodes are down, this function will take about
    # 15 seconds to return (because the first search included down nodes), rather
    # than 45 seconds (which is a very long time to stare at a blinking cursor)
    down_nodes = [node for node in os_codename if not os_codename[node]]
    if down_nodes:
        search += " and not ( {} )".format("or ".join(down_nodes))

    salt_version = local.cmd(search, 'grains.get', ['saltversion'], tgt_type="compound")
    ceph_version = local.cmd(search, 'cmd.shell',
                             ['test -e /usr/bin/ceph && ceph --version || echo "Not installed"'],
                             tgt_type="compound")

    # Better to indicate the node is down or inaccessible than just the bool False
    for node in down_nodes:
        os_codename[node] = salt_version[node] = ceph_version[node] = "Unknown (node down?)"

    return os_codename, salt_version, ceph_version
