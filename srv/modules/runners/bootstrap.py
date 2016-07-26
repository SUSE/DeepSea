#!/usr/bin/python

import salt.client
import ipaddress
import pprint
import yaml
import os
from os import stat
from pwd import getpwuid
from os.path import dirname

def all(cluster = 'ceph', overwrite = False):
    '''
    Generate pillar/ceph/cluster/{minion_id}.sls for all connected minions
    to bootstrap a ceph cluster

    This runner writes pillar data containing the cluster a minion will belong to.
    This data can then be found in /srv/pillar/ceph/cluster/. Minion that have
    already been assigned to a cluster will be skipped. To overwrite existing
    assignments pass overwrite=True.
    The default cluster name is 'ceph'. Pass cluster='Foo' to change the
    cluster name to Foo.

    CLI Example:

    .. code-block:: bash

        # bootstrap all connected unassigned minions to cluster "ceph"
        salt-run bootstrap.all
        # bootstrap all connected unassigned minions to cluster "ses"
        salt-run bootstrap.all cluster=ses
        # bootstrap all connected (maybe assigned) minions to cluster "ceph"
        salt-run bootstrap.all overwrite=True
    '''

    return _get_minions_and_write_data('*', cluster, overwrite)

def selection(selector, cluster = 'ceph', overwrite = False):
    '''
    Generate pillar/ceph/cluster/{minion_id}.sls for all minions that match
    selector to bootstrap a ceph cluster. This runner accepts compund salt
    targets.
    See https://docs.saltstack.com/en/latest/topics/targeting/compound.html

    This runner writes pillar data containing the cluster a minion will belong to.
    This data can then be found in /srv/pillar/ceph/cluster/. Minion that have
    already been assigned to a cluster will be skipped. To overwrite existing
    assignments pass overwrite=True.
    The default cluster name is 'ceph'. Pass cluster='Foo' to change the
    cluster name to Foo.

    CLI Example:

    .. code-block:: bash

        # bootstrap all unassigned minions with ceph in their hsotname to cluster "ceph"
        salt-run bootstrap.selection '*ceph*'
    '''

    print 'bootstraping all nodes that match {}'.format(selector)
    return _get_minions_and_write_data(selector, cluster, overwrite)


def _get_minions_and_write_data(selector, cluster, overwrite):
    # Keep yaml human readable/editable
    friendly_dumper = yaml.SafeDumper
    friendly_dumper.ignore_aliases = lambda self, data: True
    cluster_dir = '/srv/pillar/ceph/cluster'

    local = salt.client.LocalClient()
    node_count = 0
    master_count = 0
    skipped_count = 0
    cluster_minions = local.cmd(selector, 'grains.get', ['nodename'], expr_form="compound")
    for minion in cluster_minions.keys():
        master = local.cmd(minion, 'grains.get', ['master'])
        filename = '{}/{}.sls'.format(cluster_dir, minion)
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

        # verify that user salt has ownership cluster_dir
        if getpwuid(stat(cluster_dir).st_uid).pw_name != 'salt':
            raise Exception('Please make sure {dir} is owned by the salt user.'.format(dir=cluster_dir))

        with open(filename, 'w') as yml:
            yml.write(yaml.dump(contents, Dumper=friendly_dumper, default_flow_style=False))
    # refresh pillar data here so a subsequent run of this runner will not
    # overwrite already assigned minion
    local.cmd(selector, 'saltutil.refresh_pillar', [], expr_form="compound")
    return '''wrote cluster config to {}/
    newly assigned nodes:\t{}
    masters:\t\t\t{}
    skipped nodes:\t\t{}'''.format(cluster_dir, node_count, master_count, skipped_count)
