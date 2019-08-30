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
    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)

    return __utils__['status.get_sys_versions'](cluster_name)


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
