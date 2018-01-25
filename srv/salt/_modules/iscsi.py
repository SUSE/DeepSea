# -*- coding: utf-8 -*-

"""
iSCSI execution module

This module allows to query information about iSCSI targets served by a gateway
"""

from __future__ import absolute_import

import glob
import os

__virtualname__ = 'iscsi'

__iscsi_path__ = '/sys/kernel/config/target/iscsi'


def _local_network_addresses():
    """
    Returns the network addresses of this minion
    """
    interfaces = __grains__['ip_interfaces']
    result = []
    for _, addresses in interfaces.items():
        result.extend(addresses)
    return result


def _read_bool(file_path):
    """
    Reads an int value from a file and converts it into a bool value
    """
    with open(file_path, 'r') as file_d:
        return bool(int(file_d.read()))


def _read_int(file_path):
    """
    Reads an int value from a file and returns it
    """
    with open(file_path, 'r') as file_d:
        return int(file_d.read())


def targets():
    """
    Retrieves the information of the iSCSI targets currently deployed in this gateway
    """
    if not os.path.exists(__iscsi_path__):
        return {}

    local_addresses = _local_network_addresses()

    result = {}
    for target_path in glob.glob('{}/iqn.*'.format(__iscsi_path__)):
        target_id = target_path.replace('{}/'.format(__iscsi_path__), '')
        result[target_id] = {}
        for tpg_path in glob.glob('{}/tpgt_*'.format(target_path)):
            for portal_path in glob.glob('{}/np/*'.format(tpg_path)):
                portal_id = portal_path.replace('{}/np/'.format(tpg_path), '')
                portal_id = portal_id[:portal_id.find(':')]

                if portal_id not in local_addresses:
                    break

                if 'enabled' not in result[target_id]:
                    result[target_id]['enabled'] = True
                enabled = _read_bool('{}/enable'.format(tpg_path))
                result[target_id]['enabled'] = result[target_id]['enabled'] and enabled
                if not result[target_id]['enabled']:
                    result[target_id]['message'] = 'Target is not enabled. Please review ' \
                                                    'its configuration'
        if 'enabled' not in result[target_id]:
            result[target_id]['enabled'] = False
            result[target_id]['message'] = 'No portals defined for target'

        result[target_id]['sessions'] = _read_int('{}/fabric_statistics/iscsi_instance/sessions'
                                                  .format(target_path))

    return result


def __virtual__():
    """
    Salt module virtual function
    """
    return __virtualname__
