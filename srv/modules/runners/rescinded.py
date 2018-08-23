# -*- coding: utf-8 -*-
# pylint: disable=visually-indented-line-with-same-indent-as-next-logical-line
# pylint: disable=modernize-parse-error
#
# The salt-api calls functions with keywords that are not needed
# pylint: disable=unused-argument
"""
The collection of functions for OSDs that are no longer present.
"""

from __future__ import absolute_import
from __future__ import print_function
import logging
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client

log = logging.getLogger(__name__)


def help_():
    """
    Usage
    """
    usage = ('salt-run rescinded.ids:\n\n'
             '    Returns the list of OSDs for minions that are no longer storage nodes\n'
             '\n\n'
             'salt-run rescinded.osds:\n\n'
             '    Returns the list of OSDs for minions that are no longer mounted\n'
             '\n\n'
             'salt-run rescinded.orphaned_hosts:\n\n'
             '    Returns the list of all orphaned CRUSH host buckets\n'
             '\n\n'
             'salt-run rescinded.nodes:\n\n'
             '    Returns list of minions that are no longer storage nodes *and*\n'
             '    also appear in the list of orphaned CRUSH host buckets\n'
             '\n\n'
             'salt-run rescinded.delete_orphaned_host_buckets:\n\n'
             '    Deletes any host buckets that were orphaned by this run of Stage 5\n'
             '\n\n')
    print(usage)
    return ""


def ids(cluster='ceph', **kwargs):
    """
    List the OSD ids of minions that are not storage nodes
    """
    search = "I@cluster:{}".format(cluster)
    local = salt.client.LocalClient()
    pillar_data = local.cmd(search, 'pillar.items', [], tgt_type="compound")
    _ids = []
    for minion in pillar_data:
        if ('roles' in pillar_data[minion] and
            'storage' in pillar_data[minion]['roles']):
            continue
        data = local.cmd(minion, 'osd.list', [], tgt_type="glob")
        _ids.extend(data[minion])
    return _ids


def osds(cluster='ceph'):
    """
    List the OSD ids that are no longer mounted
    """
    search = "I@cluster:{} and I@roles:storage".format(cluster)
    local = salt.client.LocalClient()
    data = local.cmd(search, 'osd.rescinded', [], tgt_type="compound")
    _ids = []
    for minion in data:
        if isinstance(data[minion], list):
            _ids.extend(data[minion])
        else:
            log.debug(data[minion])
    return list(set(_ids))


def orphaned_hosts(cluster='ceph'):
    """
    List any orphaned host entries in the CRUSH map
    """
    search = "I@cluster:{} and I@roles:master".format(cluster)
    local = salt.client.LocalClient()
    data = local.cmd(search, 'osd.tree_from_master', [], tgt_type="compound")
    osd_tree = data[list(data.keys())[0]]
    subtree = [x for x in osd_tree['nodes']
               if x['type'] == 'host' and len(x['children']) == 0]
    orphaned_hosts_list = [x['name'] for x in subtree]
    if orphaned_hosts_list:
        log.debug("rescinded.orphaned_hosts: found orphaned CRUSH hosts ->{}<-"
                  .format(','.join(orphaned_hosts_list)))
    else:
        log.debug("osd.orphaned: no orphaned CRUSH hosts found")
    assert isinstance(orphaned_hosts_list, list),\
        "List of orphaned CRUSH host entries is not a list"
    return orphaned_hosts_list


def nodes(cluster='ceph', **kwargs):
    """
    List the short hostnames of minions that are not storage nodes
    and whose corresponding CRUSH host buckets are now orphaned
    """
    search = "I@cluster:{}".format(cluster)
    local = salt.client.LocalClient()
    pillar_data = local.cmd(search, 'pillar.items', [], tgt_type="compound")
    _crushhosts_to_delete = []
    _orphaned_hosts = orphaned_hosts()
    for minion in pillar_data:
        if ('roles' in pillar_data[minion] and
            'storage' in pillar_data[minion]['roles']):
            continue
        shorthost = local.cmd(minion, 'grains.get', ['host'], tgt_type="glob")[minion]
        if shorthost in _orphaned_hosts:
            _crushhosts_to_delete.append(shorthost)
        else:
            log.debug("{} not found in {}".format(shorthost, _orphaned_hosts))
    log.debug("rescinded.nodes: _crushhosts_to_delete is ->{}<-"
              .format(_crushhosts_to_delete))
    return _crushhosts_to_delete


def delete_orphaned_host_buckets(cluster='ceph', **kwargs):
    """
    Use rescinded.nodes runners to get a list of CRUSH hosts to delete,
    and then delete them using cmd.run.
    """
    search = "I@cluster:{} and I@roles:master".format(cluster)
    local = salt.client.LocalClient()
    _crushhosts_to_delete = nodes()
    for shorthost in _crushhosts_to_delete:
        cmd = 'ceph osd crush remove {}'.format(shorthost)
        cmd_result = local.cmd(
                         search,
                         'cmd.run',
                         [cmd],
                         tgt_type="compound"
                     )
        log.debug("rescinded.delete_orphaned_host_buckets ran {}"
                  " on master, and it returned {}".format(cmd, cmd_result))


__func_alias__ = {
                 'help_': 'help',
                 }
