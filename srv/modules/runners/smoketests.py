# -*- coding: utf-8 -*-
"""
Smoketest specific runner
"""

from __future__ import absolute_import
from __future__ import print_function
import logging
import salt.client

log = logging.getLogger(__name__)


class SmoketestPillar(object):
    """
    Generates a pillar structure for overriding a storage configuration
    """

    def __init__(self, devices):
        """
        Initialize base pillar structure
        """
        self.base = {'ceph': {'storage': {'osds': {}}}}
        self.devices = devices

    def create(self, configuration):
        """
        Map functions
        """
        funcs = {'filestore': self.filestore,
                 'filestore2': self.filestore2,
                 'bluestore': self.bluestore,
                 'bluestore2': self.bluestore2,
                 'bluestore3': self.bluestore3,
                 'bluestored': self.bluestored}

        return funcs[configuration]()

    def checklist(self, configuration):
        """
        Return a list of the OSD devices

        Note: a bit long for a list comprehension
        """
        devices = []
        result = self.create(configuration)
        for device in result['ceph']['storage']['osds'].keys():
            if result['ceph']['storage']['osds'][device]['format'] != 'none':
                devices.append(device)
        return devices

    def filestore(self):
        """
        Return the first two devices set to a filestore format
        """
        osds = {}
        for device in self.devices[:2]:
            osds[device] = {'format': 'filestore'}
        for device in self.devices[2:]:
            osds[device] = {'format': 'none'}

        self.base['ceph']['storage']['osds'] = osds
        return self.base

    def filestore2(self):
        """
        Return the first two devices set to filestore with a separate
        journal on the third device
        """
        osds = {}
        for device in self.devices[:2]:
            osds[device] = {'format': 'filestore',
                            'journal': self.devices[2:3][0],
                            'journal_size': '100M'}
        for device in self.devices[2:]:
            osds[device] = {'format': 'none'}
        self.base['ceph']['storage']['osds'] = osds
        return self.base

    def bluestore(self):
        """
        Return the first two devices set to bluestore
        """
        osds = {}
        for device in self.devices[:2]:
            osds[device] = {'format': 'bluestore'}
        for device in self.devices[2:]:
            osds[device] = {'format': 'none'}

        self.base['ceph']['storage']['osds'] = osds
        return self.base

    def bluestore2(self):
        """
        Return the first two devices set to bluestore with a separate
        wal and db on the third device
        """
        osds = {}
        for device in self.devices[:2]:
            osds[device] = {'format': 'bluestore',
                            'db': self.devices[2:3][0],
                            'db_size': '100M',
                            'wal': self.devices[2:3][0],
                            'wal_size': '100M'}
        for device in self.devices[2:]:
            osds[device] = {'format': 'none'}

        self.base['ceph']['storage']['osds'] = osds
        return self.base

    def bluestore3(self):
        """
        Return the first two devices set to bluestore, the db on the third
        and the wal on the fourth.
        """
        osds = {}
        for device in self.devices[:2]:
            osds[device] = {'format': 'bluestore',
                            'db': self.devices[2:3][0],
                            'db_size': '100M',
                            'wal': self.devices[3:4][0],
                            'wal_size': '100M'}

        for device in self.devices[2:]:
            osds[device] = {'format': 'none'}

        self.base['ceph']['storage']['osds'] = osds
        return self.base

    def bluestored(self):
        """
        Return the first two devices set to encrypted bluestore
        """
        osds = {}
        for device in self.devices[:2]:
            osds[device] = {'format': 'bluestore',
                            'encryption': 'dmcrypt'}
        for device in self.devices[2:]:
            osds[device] = {'format': 'none'}

        self.base['ceph']['storage']['osds'] = osds
        return self.base


def pillar(minion, configuration):
    """
    Generate a pillar configuration to overwrite the existing pillar.  Removing
    keys from the pillar is cumbersome.  Rely on overriding unnecessary disks
    with a format of 'none'.
    """
    local = salt.client.LocalClient()
    devices = local.cmd(minion, 'cephdisks.filter', [])
    stpl = SmoketestPillar(devices[minion])
    return stpl.create(configuration)


def checklist(minion, configuration):
    """
    Save a checklist of devices on the minion
    """
    local = salt.client.LocalClient()
    devices = local.cmd(minion, 'cephdisks.filter', [])
    stpl = SmoketestPillar(devices[minion])
    contents = stpl.checklist(configuration)
    local.cmd(minion, 'file.write', ['/tmp/checklist', contents])
    return ""


def help_():
    """
    Usage
    """
    usage = ('salt-run :\n\n'
             '    \n'
             '\n\n'
             'salt-run :\n\n'
             '    \n'
             '\n\n')
    print(usage)
    return ""


__func_alias__ = {
                 'help_': 'help',
                 }
