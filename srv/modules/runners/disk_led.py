# -*- coding: utf-8 -*-
"""
This runner is used to turn on/off the ident and fault LED of a disk.
"""
from __future__ import absolute_import

import logging
import re

import salt.client

log = logging.getLogger(__name__)


def _process(hostname, device_name, led, status):
    """
    Turn on/off the specified LED of the disk on the given host.
    """
    assert not device_name.startswith('/dev/')
    assert led in ['ident', 'fault']

    local_client = salt.client.LocalClient()
    device_file = '/dev/{}'.format(device_name)
    status = 'on' if status in [True, 'on'] else 'off'

    # Get the configuration of the command to turn on/off the ident
    # or fault LED on the target host.
    result = local_client.cmd(
        hostname, 'pillar.get', ['disk_led:cmd'], tgt_type='compound')
    if not result or hostname not in result.keys():
        raise RuntimeError(
            'Failed to get "disk_led:cmd" configuration from pillar')
    cmd_cfg = result[hostname]
    if not isinstance(cmd_cfg, dict):
        raise RuntimeError('Invalid "disk_led:cmd" configuration')

    print('Turning {} the {} LED of disk "{}" on host "{}" ...'.format(
        status, led, device_file, hostname))
    _cmd_run(hostname, cmd_cfg[led][status].format(device_file=device_file))


def _cmd_run(hostname, cmd):
    """
    Run the specified command line.
    .. note:: This function has been introduced for easier unit testing.
    """
    local_client = salt.client.LocalClient()
    result = local_client.cmd(
        hostname, 'cmd.shell', [cmd], tgt_type='compound', full_return=True)
    if result and hostname in result.keys():
        if result[hostname]['retcode'] != 0:
            raise RuntimeError('Failed to execute "{}" on "{}": {}'.format(
                cmd, hostname, result[hostname]['ret']))


def device(hostname, identifier, led, status):
    """
    Manage the storage enclosure LED by device name and host.
    :param hostname: The host where the storage device is located.
    :type hostname: str
    :param identifier: The storage device identifier, e.g.
        - sdg
        - SanDisk_X400_M.2_1260_512GB_558924904728
        - <VENDOR>_<MODEL>_<SERIAL>
    :type identifier: str
    :param led: The LED to be processed. This can be 'ident' or 'fault'.
    :type led: str
    :param status: Set to 'on' to switch on the light, otherwise 'off'.
    :type status: str
    """
    device_name = None
    local_client = salt.client.LocalClient()

    grains = local_client.cmd(
        hostname, 'grains.get', ['disks'], tgt_type='compound')
    if hostname in grains:
        # Process list of device names.
        # {
        #   ...
        #   'data1.ceph': ['dm-1', 'vdf', 'vdd', 'sdg', ...],
        #   ...
        # }
        for disk in grains[hostname]:
            if disk == identifier:
                device_name = disk
                break

            # Get all udev-created device symlinks.
            # {
            #   'data1.ceph': [
            #     'disk/by-id/wwn-0x4003c435a4d43cd8',
            #     'disk/by-path/pci-0000:00:15.0-ata-3',
            #     'disk/by-id/ata-SanDisk_X400_M.2_2280_512GB_26453645624767'
            #   ]
            # }
            device_links = local_client.cmd(
                hostname,
                'udev.links', ['/dev/{}'.format(disk)],
                tgt_type='compound')

            for device_link in device_links[hostname]:
                # pylint: disable=line-too-long
                # Search for device names like:
                # - Crucial_CT1024M550SSD1_14160C164100 (disk/by-id/(ata|scsi|.+)-Crucial_CT1024M550SSD1_14160C164100)
                # - wwn-0x4021b384a4d42ca5 (disk/by-id/wwn-0x4021b384a4d42ca5)
                if re.match(r'^.+\/(ata|scsi|wwn)-{}$'.format(identifier),
                            device_link):
                    device_name = disk
                    break

    if device_name is not None:
        _process(hostname, device_name, led, status)
        return ''
    return 'Could not find device "{}" on host "{}"'.format(
        identifier, hostname)
