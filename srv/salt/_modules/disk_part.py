# -*- coding: utf-8 -*-

"""
disk management
"""

from __future__ import absolute_import
import json
import logging

log = logging.getLogger(__name__)


def configured():
    """
    Return the osds from the ceph namespace or original namespace, optionally
    filtered by attributes.
    """
    _devices = []
    if 'ceph' in __pillar__ and 'storage' in __pillar__['ceph'] and \
       'osds' in __pillar__['ceph']['storage']:
        _devices = __pillar__['ceph']['storage']['osds']
    log.debug("devices: {}".format(_devices))

    return _devices


def create():
    """
    Create a single partition on OSD drives for LVM deployment
    """
    for device in configured():
        _create_part(device)
    return "success"


def _create_part(device):
    """
    Use sgdisk to create a single partition
    """
    _rc, _out, _err = __salt__['helper.run'](['sgdisk', '-og', device])
    _rc, start, _err = __salt__['helper.run'](['sgdisk', '-F', device])
    _rc, end, _err = __salt__['helper.run'](['sgdisk', '-E', device])
    _rc, _out, _err = __salt__['helper.run'](['sgdisk',
                                              '-n',
                                              '1:{}:{}'.format(start, end),
                                              device])
    return '{}1'.format(device)


def remove():
    """
    remove all lvm related stuctures and parts from OSD drives
    """
    _remove_lvs_and_vgs()
    _remove_pvs()
    _zap_parts()


def _remove_lvs_and_vgs():
    """
    remove volume groups and logical volumes
    """
    _rc, out, _err = __salt__['helper.run'](['lvs', '--reportformat', 'json'])
    lvs = json.loads(out)
    vg_names = ['{}'.format(lv['vg_name']) for lv in lvs['report'][0]['lv']]
    _rc, _out, _err = __salt__['helper.run'](['vgremove', '-y'] + vg_names)


def _remove_pvs():
    """
    remove physical volume
    """
    _rc, out, _err = __salt__['helper.run'](['pvs', '--reportformat', 'json'])
    pvs = json.loads(out)
    pv_names = ['{}'.format(pv['pv_name']) for pv in pvs['report'][0]['pv']]
    _rc, _out, _err = __salt__['helper.run'](['pvremove', '-y'] + pv_names)


def _zap_parts():
    """
    remove partition
    """
    for device in configured():
        _rc, _out, _err = __salt__['helper.run'](['sgdisk', '-Z', device])
