#!/usr/bin/python

import salt.client
import ipaddress
import pprint
import yaml
import os
from os.path import dirname

def all(cluster = 'ceph', overwrite = False):
    """
    Generate pillar/ceph/cluster/{minion_id}.sls to bootstrap a ceph cluster

    This runner writes pillar data containing the cluster a minion will belong to.
    This data can then be found in /srv/pillar/ceph/cluster/. Minion that have
    already been assigned to a cluster will be skipped. To overwrite existing
    assignments pass overwrite=True.
    The default cluster name is 'ceph'. Pass cluster='Foo' to change the
    cluster name to Foo.
    """

    # Keep yaml human readable/editable
    friendly_dumper = yaml.SafeDumper
    friendly_dumper.ignore_aliases = lambda self, data: True
    cluster_dir = '/srv/pillar/ceph/cluster'

    local = salt.client.LocalClient()
    node_count = 0
    master_count = 0
    skipped_count = 0
    cluster_minions = local.cmd('*', 'grains.get', ['nodename'])
    for minion in cluster_minions.keys():
        master = local.cmd(minion, 'grains.get', ['master'])
        filename = "{}/{}.sls".format(cluster_dir, minion)
        contents = {}

        # check if minion has a cluster assigned already
        assigned_cluster = local.cmd(minion, 'pillar.get', ['cluster'])
        if (not overwrite and assigned_cluster[minion] != ''):
            skipped_count += 1
            continue

        # check if minion is also master
        if (master[minion] == '127.0.0.1' or master[minion] == minion):
            print 'recognized {} as master'.format(minion)
            contents['cluster'] = 'unassigned'
            master_count += 1
        else:
            contents['cluster'] = cluster
            node_count += 1

        with open(filename, "w") as yml:
            yml.write(yaml.dump(contents, Dumper=friendly_dumper, default_flow_style=False))
    # TODO refresh pillar here? otherwise a successive run of this runner will
    # overwrite previous assignment since the pillar data has not been updated
    return """wrote cluster config to {}/
    newly assigned nodes:\t{}
    masters:\t\t\t{}
    skipped nodes:\t\t{}""".format(cluster_dir, node_count, master_count, skipped_count)
