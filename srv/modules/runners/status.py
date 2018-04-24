# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
"""
Intended for general status of clusters.
"""

from __future__ import absolute_import
from __future__ import print_function
from collections import Counter
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client
import salt.ext.six as six


def _get_data(cluster_name='ceph'):
    """
    Query grains, run commands for current versions
    """
    local = salt.client.LocalClient()
    search = "I@cluster:{}".format(cluster_name)
    # grains might be inaccurate or not up to date because they are designed
    # to hold static data about the minion. In case of an update though, the
    # data will change.  grains are refreshed on reboot(restart of the service).
    os_codename = local.cmd(search, 'grains.get', ['oscodename'], tgt_type="compound")
    salt_version = local.cmd(search, 'grains.get', ['saltversion'], tgt_type="compound")
    ceph_version = local.cmd(search, 'cmd.shell', ['ceph --version'], tgt_type="compound")

    return os_codename, salt_version, ceph_version


def help_():
    """
    Usage
    """
    usage = ('salt-run status.report:\n\n'
             '    Summarizes OS, Ceph and Salt versions\n'
             '\n\n')
    print(usage)
    return ""


# pylint: disable=no-else-return
def report(cluster_name='ceph', stdout=True, return_data=False):
    """
    Creates a report that tries to find the most common versions from:
      * OS Version and Codename
      * Ceph version
      * Salt version
    and prints it out.
    In addition you will also be presented with the minions that don't match
    one of the most_common_versions
    """
    os_codename, salt_version, ceph_version = _get_data(cluster_name)
    unsynced_nodes = {'out of sync': {}}
    common_keys = {'ceph': {}, 'salt': {}, 'os': {}}

    def _organize(minion_data):
        """
        Finds unsync'd nodes
        """
        key_ident = minion_data[0]
        minion_data_dct = minion_data[1]
        counter_obj = Counter(list(minion_data_dct.values()))
        most_common_item = None
        if counter_obj.most_common():
            most_common_item = counter_obj.most_common()[0][0]
        if most_common_item:
            common_keys.update({key_ident: most_common_item})
            for node, value in six.iteritems(minion_data_dct):
                if value != most_common_item:
                    if node not in list(unsynced_nodes['out of sync'].keys()):
                        unsynced_nodes['out of sync'][node] = {}
                    unsynced_nodes['out of sync'][node].update({key_ident: value})

    for minion_data in [('os', os_codename), ('ceph', ceph_version), ('salt', salt_version)]:
        _organize(minion_data)

    if stdout:
        for key in common_keys:
            print("  {}: {}".format(key, common_keys[key]))
        print()
        if unsynced_nodes['out of sync']:
            for node in unsynced_nodes['out of sync']:
                print("  {}:".format(node))
                for key in unsynced_nodes['out of sync'][node]:
                    print("    {}: {}".format(key, unsynced_nodes['out of sync'][node][key]))
    if return_data:
        return {'statusreport': [common_keys, unsynced_nodes]}
    else:
        return ""

__func_alias__ = {
                 'help_': 'help',
                 }
