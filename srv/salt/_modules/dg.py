#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=incompatible-py3-code
""" This module will match disks based on applied filter rules

Internally this will be called 'DriveGroups'
"""

from __future__ import absolute_import
import json
import re
import logging
import os
from collections import namedtuple
from typing import Tuple
log = logging.getLogger(__name__)
try:
    # pylint: disable=unused-import
    from ceph_volume.util.device import Device
except ModuleNotFoundError:
    log.debug("Could not load ceph_volume. Make sure to install ceph")
except ImportError:
    log.debug("Could not load ceph_volume. Make sure to install ceph")

USAGE = """

The (D)rive (G)roup module exists to filter for devices on the node
based on the drive group specification received from the master.

It mainly exposes three functions (They are not ment to be called manually)

All function expect valid drive group specs as arguments.

list_drives:

This returns a dict() of matching drives.

c_v_commands:

Constructs valid ceph-volume calls based on the drive group specs and returns them

deploy:

A simple function that calls c_v_commands and executes it on the minion.


To call from the commandline:

`salt-call dg.<func> 'filter_args={'key': 'value'}'`


"""


class FilterNotSupported(Exception):
    """ A critical error when the user specified filter is unsupported
    """
    pass


class UnitNotSupported(Exception):
    """ A critical error which encouters when a unit is parsed which
    isn't supported.
    """
    pass


class ConfigError(Exception):
    """ A critical error which is encountered when a configuration is not supported
    or is invalid.
    """
    pass


class Filter(object):
    """ Filter class to assign properties to bare filters.

    This is a utility class that tries to simplify working
    with information comming from a textfile (drive_group.yaml)

    """

    def __init__(self, **kwargs):
        self.name: str = str(kwargs.get('name', None))
        self.matcher = kwargs.get('matcher', None)
        self.value: str = str(kwargs.get('value', None))
        self._assign_matchers()
        log.debug("Initializing filter for {} with value {}".format(
            self.name, self.value))

    @property
    def is_matchable(self) -> bool:
        """ A property to indicate if a Filter has a matcher

        Some filter i.e. 'limit' or 'osd_per_device' are valid filter
        attributes but cannot be applied to a disk set. In this case
        we return 'None'
        :return: If a matcher is present True/Flase
        :rtype: bool
        """
        return self.matcher is not None

    def _assign_matchers(self) -> None:
        """ Assign a matcher based on filter_name

        This method assigns an individual Matcher based
        on `self.name` and returns it.
        """
        if self.name == "size":
            self.matcher = SizeMatcher(self.name, self.value)
        elif self.name == "model":
            self.matcher = SubstringMatcher(self.name, self.value)
        elif self.name == "vendor":
            self.matcher = SubstringMatcher(self.name, self.value)
        elif self.name == "rotational":
            self.matcher = EqualityMatcher(self.name, self.value)
        elif self.name == "all":
            self.matcher = AllMatcher(self.name, self.value)
        else:
            log.debug("No suitable matcher for {} could be found.")

    def __repr__(self) -> str:
        """ Visual representation of the filter
        """
        return 'Filter<{}>'.format(self.name)


# pylint: disable=too-few-public-methods
class Matcher(object):
    """ The base class to all Matchers

    It holds utility methods such as _virtual, _get_disk_key
    and handles the initialization.

    """

    def __init__(self, key: str, value: str) -> None:
        """ Initialization of Base class

        :param str key: Attribute like 'model, size or vendor'
        :param str value: Value of attribute like 'X123, 5G or samsung'
        """
        self.key: str = key
        self.value: str = value
        self.fallback_key: str = ''
        self.virtual: bool = self._virtual()

    # pylint: disable=no-self-use
    def _virtual(self) -> bool:
        """ Detect if any of the hosts is virtual

        In vagrant(libvirt) environments the 'model' flag is not set.
        I assume this is flag is set everywhere else. However:

        This can possibly lead to bugs since all our testing
        runs on virtual environments. This is subject to be
        moved/changed/removed
        """
        virtual: str = __grains__['virtual']
        if virtual != "physical":
            log.debug("I seem to be a VM")
            return True
        return False

    # pylint: disable=inconsistent-return-statements
    def _get_disk_key(self, disk: dict) -> str:
        """ Helper method to safely extract values form the disk dict

        There is a 'key' and a _optional_ 'fallback' key that can be used.
        The reason for this is that the output of ceph-volume is not always
        consistent (due to a bug currently, but you never know).
        There is also a safety measure for a disk_key not existing on
        virtual environments. ceph-volume apparently sources its information
        from udev which seems to not populate certain fields on VMs.

        :param dict disk: A disk representation
        :raises: A generic Exception when no disk_key could be found.
        :return: A disk value
        :rtype: str
        """

        def findkeys(node, key_val):
            """ Find keys in non-flat dict recursively """
            if isinstance(node, list):
                for i in node:
                    for key in findkeys(i, key_val):
                        yield key
            elif isinstance(node, dict):
                if key_val in node:
                    yield node[key_val]
                for j in node.values():
                    for key in findkeys(j, key_val):
                        yield key

        disk_value: str = list(findkeys(disk, self.key))
        if not disk_value and self.fallback_key:
            disk_value = list(findkeys(disk, self.fallback_key))
        if disk_value:
            return disk_value[0]
        if self.virtual:
            log.info(
                "Virtual-env detected. Not raising Exception on missing keys."
                " {} and {} appear not to be present".format(
                    self.key, self.fallback_key))
            return ''
        else:
            raise Exception("No value found for {} or {}".format(
                self.key, self.fallback_key))

    def compare(self, disk: dict):
        """ Implements a valid comparison method for a SubMatcher
        This will get overwritten by the individual classes

        :param dict disk: A disk representation
        """
        pass


# pylint: disable=too-few-public-methods
class SubstringMatcher(Matcher):
    """ Substring matcher subclass
    """

    def __init__(self, key: str, value: str, fallback_key=None) -> None:
        Matcher.__init__(self, key, value)
        self.fallback_key = fallback_key

    def compare(self, disk: dict) -> bool:
        """ Overwritten method to match substrings

        This matcher does substring matching
        :param dict disk: A disk representation (see base for examples)
        :return: True/False if the match succeeded
        :rtype: bool
        """
        if not disk:
            return False
        disk_value: str = self._get_disk_key(disk)
        if str(self.value) in str(disk_value):
            return True
        return False


# pylint: disable=too-few-public-methods
class AllMatcher(Matcher):
    """ All matcher subclass
    """

    def __init__(self, key: str, value: str, fallback_key=None) -> None:
        Matcher.__init__(self, key, value)
        self.fallback_key = fallback_key

    def compare(self, disk: dict) -> bool:
        """ Overwritten method to match all

        A rather dump matcher that just accepts all disks
        (regardless of the value)
        # note:
            Should it be possible to set all: False ?
            I don't think so.. We have limit for that
        :param dict disk: A disk representation (see base for examples)
        :return: always True
        :rtype: bool
        """
        if not disk:
            return False
        return True


# pylint: disable=too-few-public-methods
class EqualityMatcher(Matcher):
    """ Equality matcher subclass
    """

    def __init__(self, key: str, value: str) -> None:
        Matcher.__init__(self, key, value)

    def compare(self, disk: dict) -> bool:
        """ Overwritten method to match equality

        This matcher does value comparison
        :param dict disk: A disk representation
        :return: True/False if the match succeeded
        :rtype: bool
        """
        if not disk:
            return False
        disk_value: str = self._get_disk_key(disk)
        if int(disk_value) == int(self.value):
            return True
        return False


class UnitHelper(object):
    """ Container class for sizing related methods """

    @property
    def supported_suffixes(self) -> list:
        """ Only power of 10 notation is supported
        """
        return ["MB", "GB", "TB", "M", "G", "T"]

    def _normalize_suffix(self, suffix: str) -> str:
        """ Normalize any supported suffix
        Since the Drive Groups are user facing, we simply
        can't make sure that all users type in the requested
        form. That's why we have to internally agree on one format.
        It also checks if any of the supported suffixes was used
        and raises an Exception otherwise.
        :param str suffix: A suffix ('G') or ('M')
        :return: A normalized output
        :rtype: str
        """
        if suffix not in self.supported_suffixes:
            raise UnitNotSupported("Unit '{}' not supported".format(suffix))
        if suffix == "G":
            return "GB"
        if suffix == "T":
            return "TB"
        if suffix == "M":
            return "MB"
        return suffix

    def parse_suffix(self, obj: str) -> str:
        """ Wrapper method to find and normalize a prefix
        :param str obj: A size filtering string ('10G')
        :return: A normalized unit ('GB')
        :rtype: str
        """
        return self._normalize_suffix(re.findall(r"[a-zA-Z]+", obj)[0].upper())

    @staticmethod
    # pylint: disable=inconsistent-return-statements
    def to_byte(tpl: Tuple) -> float:
        """ Convert any supported unit to bytes
        :param tuple tpl: A tuple with ('10', 'GB')
        :return: The converted byte value
        :rtype: float
        """
        value = float(tpl[0])
        suffix = tpl[1]
        if suffix == "MB":
            return value * 1e+6
        elif suffix == "GB":
            return value * 1e+9
        elif suffix == "TB":
            return value * 1e+12
        # checkers force me to return something, although
        # it's not quite good to return something here.. ignore?
        return 0.00


class SizeMatcher(Matcher, UnitHelper):
    """ Size matcher subclass
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, key: str, value: str) -> None:
        # The 'key' value is overwritten here because
        # the user_defined attribute does not neccessarily
        # correspond to the desired attribute
        # requested from the inventory output
        Matcher.__init__(self, key, value)
        UnitHelper.__init__(self)
        self.key: str = "human_readable_size"
        self.fallback_key: str = "size"
        self._high = None
        self._high_suffix = None
        self._low = None
        self._low_suffix = None
        self._exact = None
        self._exact_suffix = None
        self._parse_filter()

    @property
    def low(self) -> Tuple:
        """ Getter for 'low' matchers
        """
        return self._low, self._low_suffix

    @low.setter
    def low(self, low: Tuple) -> None:
        """ Setter for 'low' matchers
        """
        self._low, self._low_suffix = low

    @property
    def high(self) -> Tuple:
        """ Getter for 'high' matchers
        """
        return self._high, self._high_suffix

    @high.setter
    def high(self, high: Tuple) -> None:
        """ Setter for 'high' matchers
        """
        self._high, self._high_suffix = high

    @property
    def exact(self) -> Tuple:
        """ Getter for 'exact' matchers
        """
        return self._exact, self._exact_suffix

    @exact.setter
    def exact(self, exact: Tuple) -> None:
        """ Setter for 'exact' matchers
        """
        self._exact, self._exact_suffix = exact

    def _get_k_v(self, data: str) -> Tuple:
        """ Helper method to extract data from a string

        It uses regex to extract all digits and calls parse_suffix
        which also uses a regex to extract all letters and normalizes
        the resulting suffix.

        :param str data: A size filtering string ('10G')
        :return: A Tuple with normalized output (10, 'GB')
        :rtype: tuple
        """
        return (re.findall(r"\d+", data)[0], self.parse_suffix(data))

    def _parse_filter(self):
        """ Identifies which type of 'size' filter is applied

        There are four different filtering modes:

        1) 10G:50G (high-low)
           At least 10G but at max 50G of size

        2) :60G
           At max 60G of size

        3) 50G:
           At least 50G of size

        4) 20G
           Exactly 20G in size

        This method uses regex to identify and extract this information
        and raises if none could be found.
        """
        low_high = re.match(r"\d+[A-Z]{1,2}:\d+[A-Z]{1,2}", self.value)
        if low_high:
            low, high = low_high.group().split(":")
            self.low = self._get_k_v(low)
            self.high = self._get_k_v(high)

        low = re.match(r"\d+[A-Z]{1,2}:$", self.value)
        if low:
            self.low = self._get_k_v(low.group())

        high = re.match(r"^:\d+[A-Z]{1,2}", self.value)
        if high:
            self.high = self._get_k_v(high.group())

        exact = re.match(r"^\d+[A-Z]{1,2}$", self.value)
        if exact:
            self.exact = self._get_k_v(exact.group())

        if not self.low and not self.high and not self.exact:
            raise Exception("Couldn't parse {}".format(self.value))

    # pylint: disable=inconsistent-return-statements, too-many-return-statements
    def compare(self, disk: dict) -> bool:
        """ Convert MB/GB/TB down to bytes and compare

        1) Extracts information from the to-be-inspected disk.
        2) Depending on the mode, apply checks and return

        # This doesn't seem very solid and _may_
        be re-factored


        """
        if not disk:
            return False
        disk_value = self._get_disk_key(disk)
        # This doesn't neccessarily have to be a float.
        # The current output from ceph-volume gives a float..
        # This may change in the future..
        # todo: harden this paragraph
        if not disk_value:
            log.warning("Could not retrieve value for disk")
            return False

        disk_size = float(re.findall(r"\d+\.\d+", disk_value)[0])
        disk_suffix = self.parse_suffix(disk_value)
        disk_size_in_byte = self.to_byte((disk_size, disk_suffix))

        if all(self.high) and all(self.low):
            if disk_size_in_byte <= self.to_byte(
                    self.high) and disk_size_in_byte >= self.to_byte(self.low):
                return True
            # is a else: return False neccessary here?
            # (and in all other branches)
            log.debug("Disk didn't match for 'high/low' filter")

        elif all(self.low) and not all(self.high):
            if disk_size_in_byte >= self.to_byte(self.low):
                return True
            log.debug("Disk didn't match for 'low' filter")

        elif all(self.high) and not all(self.low):
            if disk_size_in_byte <= self.to_byte(self.high):
                return True
            log.debug("Disk didn't match for 'high' filter")

        elif all(self.exact):
            if disk_size_in_byte == self.to_byte(self.exact):
                return True
            log.debug("Disk didn't match for 'exact' filter")
        else:
            log.debug("Neither high, low, nor exact was given")
            raise Exception("No filters applied")
        return False


class Inventory(object):
    """
    Inventory class that calls out to cephdisks
    """

    def __init__(self, cephdisks_mode='unused'):
        self.cephdisks_mode = cephdisks_mode

    @property
    def disks(self) -> list:
        """ Returns a list of disks (json_report)"""
        return __salt__[f'cephdisks.{self.cephdisks_mode}']()


# pylint: disable=too-many-public-methods
class DriveGroup(object):
    """ The Drive-Group class

    Targets one node and applies filters on the node's inventory.
    It mainly exposes:

    `data_devices`
    `wal_devices`
    `db_devices`
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, filter_args: dict, cephdisks_mode='unused') -> None:
        self.filter_args: dict = filter_args
        log.debug("Initializing DriveGroups with {}".format(self.filter_args))
        self._check_filter_support()
        self._data_devices = None
        self._disks = Inventory(cephdisks_mode=cephdisks_mode).disks
        self._wal_devices = None
        self._db_devices = None
        self.prop = namedtuple("Property", 'ident can_have_osds devices')

    @property
    def db_slots(self) -> dict:
        """ Property of db_slots

        db_slots are essentially ratio indicators
        :return: The value of db_slots
        :rtype: dict
        """
        return self.filter_args.get("db_slots", False)

    @property
    def wal_slots(self) -> dict:
        """ Property of wal_slots

        wal_slots are essentially ratio indicators
        """
        return self.filter_args.get("wal_slots", False)

    @property
    def encryption(self) -> dict:
        """ Property of encryption

        True/Flase if encryption is enabled
        """
        return self.filter_args.get("encryption", False)

    @property
    def data_device_attrs(self) -> dict:
        """ Data Device attributes
        """
        return self.filter_args.get("data_devices", dict())

    @property
    def db_device_attrs(self) -> dict:
        """ Db Device attributes
        """
        return self.filter_args.get("db_devices", dict())

    @property
    def wal_device_attrs(self) -> dict:
        """ Wal Device attributes
        """
        return self.filter_args.get("wal_devices", dict())

    @property
    def journal_device_attrs(self) -> dict:
        """ Journal Device attributes
        """
        return self.filter_args.get("journal_devices", dict())

    @property
    def journal_size(self) -> int:
        """
        Journal size
        """
        raw_value = self.filter_args.get("journal_size", '')
        return self.parse_sizes(raw_value, ident='journal_size')

    @staticmethod
    def parse_sizes(raw_inp: str, ident='') -> int:
        """ receives a size (either raw or with tb,mb suffixes)
            and returns it in byte respresentation
        """
        try:
            size = re.findall(r"\d+", raw_inp)[0]
            suffix = UnitHelper().parse_suffix(raw_inp)
        except IndexError:
            log.info(f"Looks like {ident} was defined using bytes.")
            if raw_inp:
                return int(raw_inp)
            return ''
        return int(UnitHelper().to_byte((size, suffix)))

    @property
    def block_wal_size(self) -> int:
        """ Wal Device attributes
        """
        raw_value = self.filter_args.get("block_wal_size", '')
        return self.parse_sizes(raw_value, ident='wal_size')

    @property
    def block_db_size(self) -> int:
        """ Wal Device attributes
        """
        raw_value = self.filter_args.get("block_db_size", '')
        return self.parse_sizes(raw_value, ident='db_size')

    @property
    def format(self) -> str:
        """
        On-disk-format - Filestore/Bluestore
        """
        return self.filter_args.get("format", "bluestore")

    @property
    def osds_per_device(self) -> str:
        """
        Number of OSD processes per device
        """
        return self.filter_args.get("osds_per_device", "")

    @property
    def data_devices(self) -> list:
        """ Filter for (bluestore/filestore) DATA devices
        """
        log.debug("Scanning for data devices")
        return self._filter_devices(self.data_device_attrs)

    @property
    def data_device_properties(self) -> dict:
        """ Property for data  """
        return self.prop(
            can_have_osds=True,
            ident='data_devices',
            devices=self.data_devices)

    @property
    def wal_devices(self) -> list:
        """ Filter for bluestore WAL devices
        """
        log.debug("Scanning for WAL devices")
        return self._filter_devices(self.wal_device_attrs)

    @property
    def wal_device_properties(self) -> dict:
        """ Property for wal """
        return self.prop(
            can_have_osds=False, ident='wal_devices', devices=self.wal_devices)

    @property
    def db_devices(self) -> list:
        """ Filter for bluestore DB devices
        """
        log.debug("Scanning for db devices")
        return self._filter_devices(self.db_device_attrs)

    @property
    def db_device_properties(self) -> dict:
        """ Property for db """
        return self.prop(
            can_have_osds=False, ident='db_devices', devices=self.db_devices)

    @property
    def journal_devices(self) -> list:
        """ Filter for filestore journal devices
        """
        log.debug("Scanning for journal devices")
        return self._filter_devices(self.journal_device_attrs)

    @property
    def journal_device_properties(self) -> dict:
        """ Property for journal """
        return self.prop(
            can_have_osds=False,
            ident='journal_devices',
            devices=self.journal_devices)

    @property
    def disks(self) -> list:
        """
        Disks found in the inventory
        """
        return self._disks

    @staticmethod
    def _limit_reached(device_filter, len_devices: int,
                       disk_path: str) -> bool:
        """ Check for the <limit> property and apply logic

        If a limit is set in 'device_attrs' we have to stop adding
        disks at some point.

        If limit is set (>0) and len(devices) >= limit

        :param int len_devices: Length of the already populated device set/list
        :param str disk_path: The disk identifier (for logging purposes)
        :return: True/False if the device should be added to the list of devices
        :rtype: bool
        """
        limit = int(device_filter.get('limit', 0))

        if limit > 0 and len_devices >= limit:
            log.info("Refuse to add {} due to limit policy of <{}>".format(
                disk_path, limit))
            return True
        return False

    def _filter_devices(self, device_filter: dict) -> list:
        """ Filters devices with applied filters

        Iterates over all applied filter (there can be multiple):

        size: 10G:50G
        model: Fujitsu
        rotational: 1

        Question: #############################
        This currently acts as a OR gate. Should this be a AND gate?
        Question: #############################

        Iterates over all known disk and checks
        for matches by using the matcher subclasses.

        :param dict device_filter: Device filter as in description above
        :return: Set of devices that matched the filter
        :rtype set:
        """
        devices: list = list()
        for name, val in device_filter.items():
            _filter = Filter(name=name, value=val)
            for disk in self.disks:
                log.debug("Processing disk {}".format(disk.get('path')))
                # continue criterias
                if not _filter.is_matchable:
                    log.debug(
                        "Ignoring disk {}. Filter is not matchable".format(
                            disk.get('path')))
                    continue

                if not _filter.matcher.compare(disk):
                    log.debug("Ignoring disk {}. Filter did not match".format(
                        disk.get('path')))
                    continue

                if not self._has_mandatory_idents(disk):
                    log.debug(
                        "Ignoring disk {}. Missing mandatory idents".format(
                            disk.get('path')))
                    continue

                if self._limit_reached(device_filter, len(devices),
                                       disk.get('path')):
                    log.debug("Ignoring disk {}. Limit reached".format(
                        disk.get('path')))
                    continue

                if disk not in devices:
                    log.debug('Adding disk {}'.format(disk.get("path")))
                    devices.append(disk)

        # This disk is already taken and must not be re-assigned.
        for taken_device in devices:
            if taken_device in self.disks:
                self.disks.remove(taken_device)
        # return sorted([x.get('path') for x in devices])
        return sorted([x for x in devices],
                      key=lambda dev: dev.get('path', ''))

    @staticmethod
    def _has_mandatory_idents(disk: dict) -> bool:
        """ Check for mandatory indentification fields
        """
        if disk.get("path", None):
            log.debug("Found matching disk: {}".format(disk.get("path")))
            return True
        else:
            raise Exception(
                "Disk {} doesn't have a 'path' identifier".format(disk))

    @property
    def _supported_filters(self) -> list:
        """ List of supported filters
        """
        return [
            "size", "vendor", "model", "rotational", "limit",
            "osds_per_device", "all"
        ]

    def _check_filter_support(self) -> None:
        """ Iterates over attrs to check support
        """
        for attr in [
                self.data_device_attrs,
                self.wal_device_attrs,
                self.db_device_attrs,
        ]:
            self._check_filter(attr)

    def _check_filter(self, attr: dict) -> None:
        """ Check if the used filters are supported

        :param dict attr: A dict of filters
        :raises: FilterNotSupported if not supported
        :return: None
        """
        for applied_filter in list(attr.keys()):
            if applied_filter not in self._supported_filters:
                raise FilterNotSupported(
                    "Filtering for {} is not supported".format(applied_filter))


class Disk(object):
    """ Class to interface with LVM and Non-LVM disks. """

    def __init__(self, path):
        self.path = path
        self.device = Device(self.path)
        self.error = ''

    @property
    def is_available(self):
        """ availability property """
        return self.device.available

    @property
    def is_lvm_member(self):
        """ lvm_membership property """
        return self.device.is_lvm_member

    @property
    def is_ceph_disk_member(self):
        """ ceph_disk membership property """
        return self.device.is_ceph_disk_member

    @property
    def osd_ids(self):
        """ osd_id placeholder for a disk that is neither
        a lvm nor a ceph_disk OSD.
        """
        return []

    def get_handler(self):
        """ Return the correct handler """
        if self.is_available:
            return self
        if self.is_lvm_member:
            return LvmOSD(self.device)
        if self.is_ceph_disk_member:
            return CephDiskOSD(self.device)
        raise Exception("Could not detect OSD type")


class LvmOSD(object):
    """ LVM wrapper class """

    def __init__(self, device):
        self.device = device
        self.error = ''

    @property
    def osd_ids(self) -> list:
        """ gather osd_ids for LVM osds """
        osd_ids = []
        for _vol in self.device.lvs:
            # search lvolume tags for ceph.osd_id
            osd_id: str = _vol.tags.get('ceph.osd_id', '')
            if osd_id and (_vol.tags.get('ceph.type') == 'block'
                           or _vol.tags.get('ceph.type') == 'data'):
                osd_ids.append(osd_id)
        return osd_ids


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class CephDiskOSD(object):
    """
    I can't use decorated setters as I need to pass the uninstantiated
    function in order to map it to the respective data_fields.

    This is a container class for the discoverable OSD attributes
    """

    def __init__(self, device):
        """
        Takes `device` as a single argument.
        device is a object from ceph_volume.util.Device
        """
        self.device = device
        self.error = ''
        self._path: str = self._find_mount_point()
        self._osd_id: str = ''
        self._fsid: str = ''
        self._backend: str = ''
        self._block_data: str = ''
        self._block_db: str = ''
        self._block_wal: str = ''
        self._block_dmcrypt: str = ''
        self._journal: str = ''
        self.discover()

    def _find_data_partition(self) -> str:
        """ Find data partition in all partitions """
        partitions = self.device.sys_api.get('partitions', dict())
        for partition in list(partitions.keys()):
            part = Device(f"/dev/{partition}")
            if part.ceph_disk.type == 'data':
                return part.abspath
        return ''

    def _find_mount_point(self) -> str:
        """ Find mount point for ceph """
        data_partition = self._find_data_partition()
        if not data_partition:
            return ""
        with open('/proc/mounts', 'rb') as _fd:
            for _line in _fd.readlines():
                line = _line.decode()
                device_path_full = line.split(' ')[0]
                mount_point = line.split(' ')[1]
                if mount_point and device_path_full == data_partition:
                    return mount_point
            log.warning(
                f"Could not determine mount point for {data_partition}. Command failed"
            )
            self.error = "No OSD detected (Could not find mountpoint)"
            return "n/a"

    @property
    def path(self):
        """ path property """
        return self._path

    def _is_mounted(self) -> bool:
        """ Check if the path is mounted """
        return os.path.ismount(self.path)

    @staticmethod
    def _read_file_for(full_path: str) -> str:
        """
        Read link if .islink
        Read file if isfile
        unless path doesn't exist
        """
        if not os.path.exists(full_path):
            return ''
        if os.path.islink(full_path):
            return os.readlink(full_path)
        with open(full_path, 'r') as _fd:
            return _fd.read().strip()

    @property
    def data_fields(self) -> dict:
        """ Datafield mapping """
        return {
            'whoami': self.set_osd_id,
            'fsid': self.set_fsid,
            'type': self.set_backend,
            'block': self.set_block_data,
            'block.db': self.set_block_db,
            'block.wal': self.set_block_wal,
            'block.dmcrypt': self.set_block_dmcrypt,
            'journal': self.set_journal,
        }

    def dig(self) -> bool:
        """ Looks for data_fields and sets the discovered value """
        for field, setter_method in self.data_fields.items():
            log.debug(f"Processing {field}")
            setter_method(self._read_file_for(f"{self.path}/{field}"))
        return True

    def discover(self) -> bool:
        """ .dig method wrapper. Skips if the path is not mounted """
        if not self._is_mounted():
            log.debug(f"{self.path} is not mounted. Skipping")
            return False
        return self.dig()

    @property
    def osd_ids(self) -> list:
        """
        osd_id property

        It's a list since this needs to aligned with it's LvmOSD counterpart
        This list will always be len->1 since we never supported multiple OSDs on one device
        """
        if self._osd_id:
            return [str(self._osd_id)]
        return []

    def set_osd_id(self, osd_id: str) -> None:
        """ osd_id setter """
        log.debug(f"Setting osd_id value {osd_id}")
        self._osd_id = str(osd_id)

    @property
    def fsid(self) -> str:
        """ fsid property """
        return str(self._fsid)

    def set_fsid(self, osd_fsid: str) -> None:
        """ fsid setter """
        log.debug(f"Setting osd_fsid value {osd_fsid}")
        self._fsid = str(osd_fsid)

    @property
    def backend(self) -> str:
        """ backend property """
        return self._backend

    def set_backend(self, backend: str) -> None:
        """ backend setter """
        log.debug(f"Setting backend value {backend}")
        self._backend = backend

    @property
    def block_data(self) -> str:
        """ block property """
        return self._block_data

    def set_block_data(self, block_data: str) -> None:
        """ block data setter """
        log.debug(f"Setting block_data value {block_data}")
        self._block_data = block_data

    @property
    def block_db(self) -> str:
        """ block db property """
        return self._block_db

    def set_block_db(self, block_db: str) -> None:
        """ block db setter """
        log.debug(f"Setting block_db value {block_db}")
        self._block_db = block_db

    @property
    def block_wal(self) -> str:
        """ block wal property """
        return self._block_wal

    def set_block_wal(self, block_wal: str) -> None:
        """ block wal setter """
        log.debug(f"Setting block_wal value {block_wal}")
        self._block_wal = block_wal

    @property
    def block_dmcrypt(self) -> str:
        """ block dmcrypt property """
        return self._block_dmcrypt

    def set_block_dmcrypt(self, block_dmcrypt: str) -> None:
        """ block dmcrypt setter """
        log.debug(f"Setting block_dmcrypt value {block_dmcrypt}")
        self._block_dmcrypt = block_dmcrypt

    @property
    def journal(self) -> str:
        """ journal property """
        return self._journal

    def set_journal(self, journal: str) -> None:
        """ journal setter """
        log.debug(f"Setting journal value {journal}")
        self._journal = journal

    def report(self) -> str:
        """ formatted reporting """
        message: str = f"""
osd_id  : {self.osd_id:<1}
osd_fsid: {self.fsid:<1}
backend : {self.backend:<1}
data    : {self.block_data:<1}
db      : {self.block_db:<1}
wal     : {self.block_wal:<1}
journal : {self.journal:<1}
dmcrypt : {self.block_dmcrypt:<1}
        """
        return message

    def as_json(self) -> str:
        """ return attributes as json """
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            allow_nan=False,
            sort_keys=False,
            indent=4)

    def as_dict(self) -> dict:
        """ return attributes as dict """
        return self.__dict__


# pylint: disable=too-many-instance-attributes
class Output(object):
    """ Container class for user facing functions """

    def __init__(self, cephdisks_mode='unused', **kwargs):
        self.filter_args: dict = kwargs.get('filter_args', dict())
        self.bypass_pillar = kwargs.get('bypass_pillar', False)
        self.destroyed_osds_map = kwargs.get('destroyed_osds', {})
        self.dry_run = kwargs.get('dry_run', False)
        self.dgo = DriveGroup(self.filter_args, cephdisks_mode)
        self.ret: dict = dict(
            data_devices={},
            wal_devices={},
            db_devices={},
            journal_devices={},
            errors={})
        self.data_device_props = self.dgo.data_device_properties
        self.db_device_props = self.dgo.db_device_properties
        self.wal_device_props = self.dgo.wal_device_properties
        self.journal_device_props = self.dgo.journal_device_properties

        self._pre_check()

    def _pre_check(self):
        """ Check if filter_args and policies are valid"""
        if not self.filter_args:
            raise Exception("No filter_args provided")

        return self._apply_policies()

    def _apply_policies(self) -> bool:
        """ Apply known policies """

        if not self.data_device_props.devices:
            error_message = """
You didn't specify data_devices. No actions will be taken.
            """
            log.error(error_message)
            self.ret.get('errors', {}).update(
                dict(no_data_devices=error_message))
            return False

        if self.wal_device_props.devices and not self.db_device_props.devices:
            error_message = """
You specified only wal_devices. If your intention was to
have dedicated WALs/DBs please specify it with the db_devices
filter. WALs will be colocated alongside the DBs.
Read more about this here <link>.
            """
            log.error(error_message)
            self.ret.get('errors', {}).update(dict(wal_devices=error_message))
            return False

        if len(self.db_device_props.devices) > len(
                self.data_device_props.devices):
            error_message = """
You specified more db_devices than data_devices.
This will result in an uneven configuration.
Read more about this here <link>.
"""
            log.error(error_message)
            self.ret.get('errors', {}).update(dict(uneven=error_message))
            return False

        if self.wal_device_props.devices and self.db_device_props.devices:
            if len(self.wal_device_props.devices) < len(
                    self.db_device_props.devices):
                error_message = """
We can't guarantee proper wal/db distribution in this configuration.
Please make sure to have more/equal wal_devices than db_devices"""
                log.error(error_message)
                self.ret.get('errors', {}).update(
                    dict(wal_db_distribution=error_message))
                return False

        return True

    @staticmethod
    def _guide(osd_ids: list, can_have_osds: bool = False, error='') -> dict:
        """ Return dict with meaningful message for a specific category """
        if error:
            return dict(message=error)

        if osd_ids and can_have_osds:
            return dict(osds=osd_ids)
        if osd_ids and not can_have_osds:
            return dict(
                conflict=
                f"Detected OSD(s) {' '.join(osd_ids)} in a non-admissible category."
            )

        if can_have_osds:
            return dict(
                message=
                "No OSD detected (Will be created in the next deployment run)")

        # also detect if db/wal-device is _actually_ a wal/db device of a already deployed OSD
        return dict(message="No issues found.")

    def annotate_return(self, devices: list, can_have_osds=False) -> dict:
        """ Annotate a return based on the output of `guide` """
        ret = {}
        for device in devices:
            dev_path: str = device.get('path', '')
            if not dev_path:
                continue
            disk = Disk(dev_path).get_handler()
            ret.update({
                dev_path:
                self._guide(
                    disk.osd_ids,
                    can_have_osds=can_have_osds,
                    error=disk.error)
            })
        return ret

    def _find_conflicts(self) -> bool:
        """ Find conflicts in a output dict """

        def find(key, value):
            """ Search recursively through dict """
            for k, v__ in (
                    value.items() if isinstance(value, dict) else
                    enumerate(value) if isinstance(value, list) else []):
                if k == key:
                    yield v__
                elif isinstance(v__, (dict, list)):
                    for result in find(key, v__):
                        yield result

        conflicts = list(find('conflict', self.ret))
        if conflicts:
            self.ret.get('errors').update(dict(conflicts=conflicts))
            return True
        if self.ret.get('errors', {}):
            return True
        return False

    def generate_annotated_report(self) -> dict:
        """ Generate a annotated report based on group properties """
        for prop in [
                self.data_device_props, self.db_device_props,
                self.wal_device_props, self.journal_device_props
        ]:
            self.ret.get(prop.ident).update(
                self.annotate_return(prop.devices, prop.can_have_osds))

        self._find_conflicts()
        return self.ret

    @property
    def destroyed_osds(self) -> list:
        """ Property that lists 'destroyed' osds """
        return self.destroyed_osds_map.get(__grains__.get('host', ''), list())

    def generate_c_v_commands(self):
        """ Generate ceph-volume commands based on the DriveGroup filters """
        data_devices = [x.get('path') for x in self.data_device_props.devices]
        db_devices = [x.get('path') for x in self.db_device_props.devices]
        wal_devices = [x.get('path') for x in self.wal_device_props.devices]
        journal_devices = [
            x.get('path') for x in self.journal_device_props.devices
        ]

        appendix = ""
        if self.destroyed_osds:
            appendix = " --osd-ids {}".format(" ".join(
                ([str(x) for x in self.destroyed_osds])))

        if self._find_conflicts():
            return self.ret.get('errors')

        def chunks(seq, size):
            """ Splits a sequence in evenly sized chunks"""
            return (seq[i::size] for i in range(size))

        if self.dgo.format == 'filestore':
            cmd = "ceph-volume lvm batch"

            cmd += " {}".format(" ".join(data_devices))

            if self.dgo.journal_size:
                cmd += " --journal-size {}".format(self.dgo.journal_size)

            if journal_devices:
                cmd += " --journal-devices {}".format(
                    ' '.join(journal_devices))

            cmd += " --filestore"

            if self.dry_run:
                cmd += " --report"
            else:
                cmd += " --yes"

            if appendix:
                cmd += appendix

            if self.dgo.encryption:
                cmd += " --dmcrypt"

            if self.dgo.osds_per_device:
                cmd += " --osds-per-device {}".format(self.dgo.osds_per_device)

            return [cmd]

        if self.dgo.format == 'bluestore':

            chunks_wal_devices = list(chunks(wal_devices, len(db_devices)))
            chunks_db_devices = list(chunks(db_devices, len(db_devices)))
            chunks_data_devices = list(chunks(data_devices, len(db_devices)))

            commands = []

            for i in range(0, len(db_devices)):
                cmd = "ceph-volume lvm batch --no-auto"
                cmd += " {}".format(" ".join(chunks_data_devices[i]))
                cmd += " --db-devices {}".format(" ".join(
                    chunks_db_devices[i]))
                if chunks_wal_devices[i]:
                    cmd += " --wal-devices {}".format(" ".join(
                        chunks_wal_devices[i]))
                commands.append(cmd)

            if not db_devices:
                cmd = "ceph-volume lvm batch --no-auto {}".format(
                    " ".join(data_devices))
                commands.append(cmd)

            # pylint: disable=consider-using-enumerate
            for i in range(0, len(commands)):
                if self.dry_run:
                    commands[i] += " --report"
                else:
                    commands[i] += " --yes"
                # how is that working now? That might get
                # passed multiple times.. How is c-v reacting
                if appendix:
                    commands[i] += appendix

                if self.dgo.encryption:
                    commands[i] += " --dmcrypt"

                if self.dgo.block_wal_size:
                    commands[i] += " --block-wal-size {}".format(
                        self.dgo.block_wal_size)

                if self.dgo.block_db_size:
                    commands[i] += " --block-db-size {}".format(
                        self.dgo.block_db_size)

                if self.dgo.osds_per_device:
                    commands[i] += " --osds-per-device {}".format(
                        self.dgo.osds_per_device)

            return commands

    def _check_for_old_profiles(self):
        """ Check if old profiles are present. Do not deploy if present """
        if not self.bypass_pillar and ('storage' in __pillar__.get('ceph',
                                                                   {})):
            return ("You seem to have configured old-style profiles."
                    "Will not deploy using Drive-Groups."
                    "Please consult the official documentation for guidance"
                    "on how to migrate to Drive-Groups")
        return ""

    def deploy(self):
        """ Execute the generated ceph-volume commands """
        # do not run this when there is still ceph:storage in the pillar
        # this indicates that we are in a post-upgrade scenario and
        # the drive assignment was not ported to drive-groups yet.
        error_message = self._check_for_old_profiles()
        if error_message:
            return error_message

        c_v_command_list = self.generate_c_v_commands()

        if isinstance(c_v_command_list, dict):
            # In this case we have an error dict
            return c_v_command_list

        rets = []
        for cmd in c_v_command_list:
            if not cmd.startswith("ceph-volume"):
                if cmd:
                    log.error(cmd)
                continue
            log.debug("Running command: {}".format(cmd))
            rets.append(__salt__['helper.run'](cmd))
        log.debug("Returns for dg.deploy: {}".format(rets))
        return rets


def report(**kwargs):
    """ User facing report(list) call """
    return Output(**kwargs, cephdisks_mode='all').generate_annotated_report()


def list_(**kwargs):
    """
    Salt's __func_alias__ doens't support more than one alias
    for a function.
    """
    return report(**kwargs)


def c_v_commands(**kwargs):
    """ User facing ceph-volume command call """
    return Output(**kwargs, cephdisks_mode='unused').generate_c_v_commands()


def deploy(**kwargs):
    """ User facing deploy call """
    return Output(**kwargs, cephdisks_mode='unused').deploy()


def _help():
    """ Help/Usage class
    """
    print(USAGE)


__func_alias__ = {'help_': 'help', 'list_': 'list'}
