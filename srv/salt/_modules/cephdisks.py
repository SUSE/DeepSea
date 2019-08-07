# -*- coding: utf-8 -*-
# pylint: disable=fixme,modernize-parse-error
"""
Query ceph-volume's API for devices on the node
"""

from __future__ import absolute_import
import logging
import re
# pytest: disable=import-error
log = logging.getLogger(__name__)


# pylint: disable=import-error
def load_ceph_volume_devices():
    """ To simplify import mocking in the tests

    ceph-volume is not present during unittesting.
    """
    try:
        from ceph_volume.util.device import Devices
        return Devices()
    except ImportError:
        log.error("Could not import from ceph_volume.util.device.")


# pylint: disable=import-error
def load_ceph_volume_device():
    """ To simplify import mocking in the tests

    ceph-volume is not present during unittesting.
    """
    try:
        from ceph_volume.util.device import Device
        return Device
    except ImportError:
        log.error("Could not import from ceph_volume.util.device.")


class Inventory(object):
    """ Inventory wrapper class for ceph-volume's device api """

    def __init__(self, **kwargs) -> None:
        self.kwargs: dict = kwargs
        self.devices = load_ceph_volume_devices().devices
        self.device = load_ceph_volume_device()
        self.root_disk = self._find_root_disk()

    @property
    def exclude_unavailable(self) -> bool:
        """ The available filter """
        return self.kwargs.get('exclude_unavailable', False)

    @property
    def exclude_cephdisk_member(self) -> bool:
        """ The available filter """
        return self.kwargs.get('exclude_cephdisk_member', False)

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

    @property
    def _min_osd_size(self) -> float:
        """ Minimum disk size to be used by ceph-volume (5GB) """
        return 5368709120.0

    # pylint: disable=redefined-outer-name, not-an-iterable
    def osd_list(self, devices: list) -> list:
        """
        Can and should probably be offloaded to ceph-volume upstream
        """
        assert isinstance(devices, list)
        if not devices:
            devices = self.devices
        else:
            devices = [self.device(path) for path in devices]
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

    @staticmethod
    # pylint: disable=inconsistent-return-statements
    def _find_root_disk() -> str:
        """ Return the root disk of a device set """
        with open('/proc/mounts', 'rb') as _fd:
            for _line in _fd.readlines():
                line = _line.decode()
                mount_point = line.split(' ')[1]
                if mount_point == '/':
                    device_path_full = line.split(' ')[0]
                    device_ident = device_path_full.split('/')[-1]
                    if device_ident.startswith('nvme'):
                        # nvme partitions are nvme0n1p1,p2,p3..
                        return re.sub(r'p\d+$', '', device_path_full)
                    return re.sub(r'\d+$', '', device_path_full)

    @staticmethod
    def _is_cdrom(path: str) -> bool:
        """ Always skip cdrom """
        if path.split('/')[-1].startswith('sr'):
            return True
        return False

    @staticmethod
    def _is_rbd(path: str) -> bool:
        """ Always skip rbd """
        if path.split('/')[-1].startswith('rbd'):
            return True
        return False

    def _has_sufficient_size(self, size: float) -> bool:
        """ Skip disks that are small than a defined threshold """
        # due to: todo http://tracker.ceph.com/issues/40776
        if size >= self._min_osd_size:
            return True
        return False

    def filter_(self) -> list:
        """
        Apply set filters and return list of devices
        """
        devs: list = list()
        for dev in self.devices:

            # Apply customizable filters
            if self.exclude_root_disk:
                # exclude the root (/) disk
                if self.root_disk == dev.path:
                    log.debug(
                        f"Skipping disk <{dev.path}> due to <root_disk> filter"
                    )
                    continue

            if self.exclude_cephdisk_member:
                # exclude disks that are used by cephdisk
                # due to: todo http://tracker.ceph.com/issues/40817
                if dev.is_ceph_disk_member:
                    log.debug(
                        f"Skipping disk <{dev.path}> due to <cephdisk_member> filter"
                    )
                    continue

            if self.exclude_unavailable:
                # exclude disks that are marked not 'available'
                if not dev.available:
                    log.debug(
                        f"Skipping disk <{dev.path}> due to <available> filter"
                    )
                    continue
            if self.exclude_used_by_ceph:
                # exlude disks that are used by ceph
                if dev.used_by_ceph:
                    log.debug(
                        f"Skipping disk <{dev.path}> due to <used_by_ceph> filter"
                    )
                    continue

            # Apply non-customizable filters
            if self._is_cdrom(dev.path):
                log.debug(f"Skipping disk <{dev.path}> due to <cdrom> filter")
                continue
            if self._is_rbd(dev.path):
                log.debug(f"Skipping disk <{dev.path}> due to <rbd> filter")
                continue
            if not self._has_sufficient_size(dev.size):
                log.debug(
                    f"Skipping disk <{dev.path}> due to <too_small> filter")
                continue
            # due to: todo http://tracker.ceph.com/issues/40799
            if dev.is_mapper and dev.is_encrypted:
                log.debug(
                    f"Skipping disk <{dev.path}> due to <mapper_and_encrypted> filter"
                )
                continue

            devs.append(dev)
        return devs

    def find_by_osd_id(self, osd_id_search: str) -> list:
        """
        Search through logical volumes to find matching
        osd_ids. This may also be offloaded to c-v in the future.
        """
        devs = list()
        for dev in self.devices:
            for _lv in dev.lvs:
                # each lv can have multiple volumes
                if not isinstance(_lv, list):
                    osd_id = _lv.tags.get('ceph.osd_id', '')
                    if str(osd_id_search) == str(osd_id) and _lv.tags.get(
                            'ceph.type') == 'block':
                        devs.append(dev)
                if isinstance(_lv, list):
                    for _vol in _lv:
                        # search volume's tags for ceph.osd_id
                        osd_id = _vol.tags.get('ceph.osd_id', '')
                        if str(osd_id_search) == str(osd_id) and _lv.tags.get(
                                'ceph.type') == 'block':
                            devs.append(dev)
        return devs


def get_(disk_path):
    """ Get a json report for a given device """
    device = load_ceph_volume_device()
    return device(disk_path).json_report()


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


def _list(**kwargs):
    """ List only devices that are used by ceph """
    kwargs.update(dict(exclude_used_by_ceph=False))
    return [x.json_report() for x in Inventory(**kwargs).filter_()]


def used(**kwargs):
    """ Alias for list """
    return _list(**kwargs)


def unused(**kwargs):
    """ List only devices that are not used by ceph and are available """
    kwargs.update(
        dict(
            exclude_used_by_ceph=True,
            exclude_unavailable=True,
            exclude_cephdisk_member=True))
    return [x.json_report() for x in Inventory(**kwargs).filter_()]


def devices(**kwargs):
    """ List device paths"""
    return [x.path for x in Inventory(**kwargs).filter_() if x.path]


# pylint: disable=redefined-outer-name
def osd_list(devices, **kwargs):
    """ Get a list of osds for that node or set of devices """
    assert isinstance(devices, list)
    return Inventory(**kwargs).osd_list(devices)


def help_():
    """ Helper dummy """
    print("HELP DUMMY")


__func_alias__ = {
    'all_': 'all',
    '_list': 'list',
    'help_': 'help',
    'get_': 'get',
}
