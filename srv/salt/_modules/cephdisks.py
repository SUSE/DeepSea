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
    def exclude_available(self) -> bool:
        """ The available filter """
        return self.kwargs.get('exclude_available', False)

    @property
    def exclude_used_by_ceph(self) -> bool:
        """ The used_by_ceph filter """
        # This also returns disks that are marked as
        # 'destroyed' is that valid?
        return self.kwargs.get('exclude_used_by_ceph', False)

    @property
    def exclude_root_disk(self) -> bool:
        """ The root_disk filter """
        return self.kwargs.get('exclude_root_disk', True)

    def osd_list(self, devices=[]) -> list:
        """
        Can and should probably be offloaded to ceph-volume upstream
        """
        assert type(devices) == list
        if not devices:
            devices = self.devices.devices
        else:
            devices = [Device(path) for path in devices]
        osd_ids: list = list()
        lvs: list = [x.lvs for x in devices]
        # list of all lvs of all disks
        for _lv in lvs:
            # each lv can have multiple volumes
            for _vol in _lv:
                # search volume's tags for ceph.osd_id
                osd_id: str = _vol.tags.get('ceph.osd_id', '')
                if osd_id:
                    osd_ids.append(osd_id)
        return osd_ids

    def _is_root_disk(self, path: str) -> bool:
        """ Return True/False if disk is root disk """
        rc, stdout, stderr = __salt__['helper.run'](
            "mount|grep ' / '|cut -d' ' -f 1 | sed 's/[0-9]//g'")
        if not rc == 0:
            log.warning("Could not determine root disk. Command failed")
            return False
        return stdout == path

    def filter_(self) -> list:
        """
        Apply set filters and return list of devices
        """
        devs: list = list()
        for dev in self.devices.devices:
            # Apply known filters
            if self.exclude_root_disk:
                if self._is_root_disk(dev.path):
                    log.debug("Skipping disk due to <root_disk> filter")
                    continue
            if self.exclude_available:
                if dev.available:
                    log.debug("Skipping disk due to <available> filter")
                    continue
            if self.exclude_used_by_ceph:
                if dev.used_by_ceph:
                    log.debug("Skipping disk due to <used_by_ceph> filter")
                    continue
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


def get_(disk_path):
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


def all_(**kwargs):
    """ List all devices regardless of used or not
    also exclude root disk by default
    """
    kwargs.update(dict(exclude_root_disk=True))
    return [x.json_report() for x in Inventory(**kwargs).filter_()]


def used(**kwargs):
    """ List only devices that are used by ceph """
    kwargs.update(dict(exclude_used_by_ceph=False))
    return [x.json_report() for x in Inventory(**kwargs).filter_()]


def unsed(**kwargs):
    """ List only devices that are not used by ceph and are available """
    kwargs.update(dict(exclude_used_by_ceph=True, exclude_available=False))
    return [x.json_report() for x in Inventory(**kwargs).filter_()]


def devices(**kwargs):
    """ List device paths"""
    return [x.path for x in Inventory(**kwargs).filter_() if x.path]


def osd_list(devices=[], **kwargs):
    """ Get a list of osds for that node or set of devices """
    return Inventory(**kwargs).osd_list(devices)


def help_():
    """ Helper dummy """
    print("HELP DUMMY")


__func_alias__ = {
    'all_': 'all',
    'used': 'list',
    'help_': 'help',
    'filter_': 'filter',
    'get_': 'get',
}
