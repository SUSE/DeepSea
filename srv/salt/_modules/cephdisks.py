# -*- coding: utf-8 -*-
# pylint: disable=fixme,modernize-parse-error
"""
Query ceph-volume's API for devices on the node
"""

from __future__ import absolute_import
import logging
# pytest: disable=import-error
log = logging.getLogger(__name__)
try:
    from ceph_volume.util.device import Devices, Device
except ModuleNotFoundError:
    log.debug("Could not load ceph_volume. Make sure to install ceph")
except ImportError:
    log.debug("Could not load ceph_volume. Make sure to install ceph")


class Inventory(object):
    """ Inventory wrapper class for ceph-volume's device api """

    def __init__(self, **kwargs) -> None:
        self.kwargs: dict = kwargs
        self.devices = Devices()

    @property
    def available_filter(self) -> bool:
        """ The available filter """
        return self.kwargs.get('available', None)

    @property
    def used_by_ceph_filter(self) -> bool:
        """ The used_by_ceph filter """
        # This also returns disks that are marked as
        # 'destroyed' is that valid?
        return self.kwargs.get('used_by_ceph', True)

    def osd_list(self) -> list:
        """
        Can and should probably be offloaded to ceph-volume upstream
        """
        osd_ids: list = list()
        lvs: list = [x.lvs for x in self.devices.devices]
        # list of all lvs of all disks
        for _lv in lvs:
            # each lv can have multiple volumes
            for _vol in _lv:
                # search volume's tags for ceph.osd_id
                osd_id: str = _vol.tags.get('ceph.osd_id', '')
                if osd_id:
                    osd_ids.append(osd_id)
        return osd_ids

    def filter_(self) -> list:
        """
        Apply set filters and return list of devices
        """
        devs: list = list()
        for dev in self.devices.devices:
            # Apply known filters
            if self.available_filter:
                if dev.available is self.available_filter:
                    devs.append(dev)
                    continue
            elif self.used_by_ceph_filter:
                if dev.used_by_ceph is self.used_by_ceph_filter:
                    devs.append(dev)
                    continue
            else:
                devs.append(dev)
        return devs

    def find_by_osd_id(self, osd_id_search: str) -> list:
        """
        Search through logical volumes to find matching
        osd_ids. This may also be offloaded to c-v in the future.
        """
        devs = list()
        for dev in self.devices.devices:
            for _lv in dev.lvs:
                # each lv can have multiple volumes
                if not isinstance(_lv, list):
                    osd_id = _lv.tags.get('ceph.osd_id', '')
                    if str(osd_id_search) == str(osd_id):
                        devs.append(dev)
                if isinstance(_lv, list):
                    for _vol in _lv:
                        # search volume's tags for ceph.osd_id
                        osd_id = _vol.tags.get('ceph.osd_id', '')
                        if str(osd_id_search) == str(osd_id):
                            devs.append(dev)
        return devs


def get_(disk_path) -> dict:
    """ Get a json report for a given device """
    return Device(disk_path).json_report()


def find_by_osd_id(osd_id, **kwargs):
    """ Find OSD by it's osd id """
    return [
        x.json_report() for x in Inventory(**kwargs).find_by_osd_id(osd_id)
    ]


def attr_list(**kwargs):
    """ List supported attributes of drives """
    report = list()
    default = "Not available"
    for device in Inventory(**kwargs).filter_():
        dev = device.json_report()
        if device.path:
            model = dev.get('sys_api', {}).get('model', default)
            vendor = dev.get('sys_api', {}).get('vendor', default)
            size = dev.get('sys_api', {}).get('human_readable_size', default)
            rotational = dev.get('sys_api', {}).get('rotational', default)
            path = dev.get('path')
            report.append({
                path:
                dict(
                    model=model,
                    vendor=vendor,
                    size=size,
                    rotational=rotational)
            })
    return report


def devices(**kwargs):
    """ List device paths"""
    return [x.path for x in Inventory(**kwargs).filter_() if x.path]


def all_(**kwargs):
    """ List all devices regardless of used or not """
    return [x.json_report() for x in Inventory(**kwargs).devices.devices]


def list_(**kwargs):
    """ List only devices that are used by ceph """
    kwargs.update(dict(used_by_ceph=True))
    return [x.json_report() for x in Inventory(**kwargs).filter_()]


def osd_list(**kwargs):
    """ Get a list of osds for that node """
    return Inventory(**kwargs).osd_list()


def help_():
    """ Helper dummy """
    print("HELP DUMMY")


__func_alias__ = {
    'all_': 'all',
    'list_': 'list',
    'help_': 'help',
    'filter_': 'filter',
    'get_': 'get',
}
