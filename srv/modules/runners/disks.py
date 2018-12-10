import salt.client
import json
import re
import pprint


class FilterNotSupported(Exception):
    pass


class Base(object):
    def __init__(self, **kwargs):
        self.local_client = salt.client.LocalClient()
        self.base_target = kwargs.get("target", "*")


class Inventory(Base):
    def __init__(self, target):
        Base.__init__(self)
        self.target = target if target is not None else self.base_target
        self.raw = self.local_client.cmd(
            self.target, "cmd.run", ["ceph-volume inventory --format json"]
        )


class Matcher(object):
    def __init__(self, attr, key):
        self.attr = attr
        self.key = key
        self.fallback_key = None

    def _get_disk_key(self, disk):
        disk_key = disk.get(self.key)
        if not disk_key and self.fallback_key:
            disk_key = disk.get(self.fallback_key)
        if disk_key:
            return disk_key
        raise Exception("No disk_key found")


class SubstringMatcher(Matcher):
    def __init__(self, attr, key):
        Matcher.__init__(self, attr, key)

    def _compare(self, disk):
        disk_key = self._get_disk_key(disk)
        if str(self.attr) in str(disk_key):
            return True
        return False


class RotatesMatcher(Matcher):
    def __init__(self, attr, key):
        Matcher.__init__(self, attr, key)

    def _compare(self, disk):
        disk_key = self._get_disk_key(disk)
        if int(disk_key) == int(self.attr):
            return True
        return False


class SizeMatcher(Matcher):
    def __init__(self, attr, key):
        Matcher.__init__(self, attr, key)
        self.key = "human_readable_size"
        # Inconsistency in ceph-volume? Sometimes there is no human_readable_size
        self.fallback_key = "size"
        self.high = None
        self.low = None
        self.exact = None
        self.suffix = None
        self._parse_filter()
        self._adjust_suffix()

    def _adjust_suffix(self):
        if self.suffix == "G":
            self.suffix = "GB"
        if self.suffix == "T":
            self.suffix = "TB"
        if self.suffix == "M":
            self.suffix = "MB"

    def _parse_suffix(self, obj):
        # Needs adaption when 1G:10G
        return re.findall("[a-zA-Z]+", obj)[0]

    def set_low_high(self):
        low_high = re.match("\d+[A-Z]:\d+[A-Z]", self.attr)
        if low_high:
            low, high = low_high.group().split(":")
            __import__('pdb').set_trace()



    def _parse_filter(self):
        # This is obviously a bad implementation
        # Alternatives:
        # 1. write 3 regexes that match
        # :int, int:, #int:int, #int
        # 2. endswitch and startwith + extra case int:int
        # 3. something bettter :/
        # TODO!
        sizes = re.findall("\d+", self.attr)
        self.suffix = self._parse_suffix(self.attr)

        self.set_low_high()
        low = re.match("\d+[A-Z]:$", self.attr)
        high = re.match("^:\d+[A-Z]", self.attr)
        exact = re.match("^\d+[A-Z]$", self.attr)




        if len(sizes) == 1:
            # and no delim
            self.exact = float(sizes[0])
        elif len(sizes) == 2:
            # and split with : delim
            self.high = float(sizes[0])
            self.low = float(sizes[1])
        else:
            raise

    def _compare(self, disk):
        """ That entire Matcher sucks and needs to be redesigned
        """
        disk_key = self._get_disk_key(disk)
        disk_size = float(re.findall("\d+\.\d+", disk_key)[0])
        disk_suffix = self._parse_suffix(disk_key)

        if self.high and self.low:
            if (
                disk_size <= self.high
                and disk_size >= self.low
                and disk_suffix == self.suffix
            ):
                return True
            print("Nothing matched in high/low mode")
            return False

        elif self.exact:
            if disk_size == self.exact and disk_suffix == self.suffix:
                return True
            print("Nothing matched in exact")
            return False
        else:
            print("Neither high, low, nor exact was given")
            # TODO
            raise


class DriveGroup(Base):
    def __init__(self, target) -> None:
        Base.__init__(self)
        self.raw: list = list(
            self.local_client.cmd(target,
                                  "pillar.get",
                                  ["drive_group"]).values()
        )[0]
        self.target: str = self.raw.get("target")
        self.data_device_attrs: dict = self.raw.get("data_devices", dict())
        self.shared_device_attrs: dict = self.raw.get("shared_devices", dict())
        self._check_filter_support()
        self.encryption: bool = self.raw.get("encryption", False)
        self.wal_slots: int = self.raw.get("wal_slots", None)
        self.db_slots: int = self.raw.get("db_slots", None)
        self.matchers = self._assign_matchers()
        # harden this
        self.inventory = json.loads((list(Inventory(target).raw.values()))[0])

    @property
    def data_devices(self) -> set:
        return self._filter_devices(self.data_device_attrs)

    @property
    def shared_devices(self) -> set:
        return self._filter_devices(self.shared_device_attrs)

    def _filter_devices(self, device_filter) -> set:
        devices: set = set()
        for name, val in device_filter.items():
            print("scanning for {}:{}".format(name, val))
            for disk in self.inventory:
                if not self.__match(self._reduce_inventory(disk)):
                    continue
                devices.add(disk["path"])
        return devices

    @property
    def _supported_filters(self) -> list:
        return ["size", "vendor", "model", "rotates"]

    def _check_filter_support(self):
        for applied_filter in list(self.data_device_attrs.keys()):
            if applied_filter not in self._supported_filters:
                raise FilterNotSupported(
                    "Filter {} is not supported".format(applied_filter)
                )
        for applied_filter in list(self.shared_device_attrs.keys()):
            if applied_filter not in self._supported_filters:
                raise FilterNotSupported(
                    "Filter {} is not supported".format(applied_filter)
                )

    def _assign_matchers(self):
        matchers = list()
        for k, v in self.data_device_attrs.items():
            if k == "size":
                matchers.append(SizeMatcher(v, k))
            elif k == "model":
                matchers.append(SubstringMatcher(v, k))
            elif k == "vendor":
                matchers.append(SubstringMatcher(v, k))
            elif k == "rotates":
                matchers.append(RotatesMatcher(v, k))
        return matchers

    def __match(self, disk):
        for matcher in self.matchers:
            return matcher._compare(disk)

    def _reduce_inventory(self, disk) -> dict:
        """ Wrapper to check ceph-volume inventory output
        """
        # FIXME: Temp disable this check, only for testing purposes
        if disk["available"] is False:  # True
            reduced_disk = {"path": disk.get("path")}
            reduced_disk["size"] = disk["sys_api"].get("human_readable_size", None)
            reduced_disk["vendor"] = disk["sys_api"].get("vendor", None)
            reduced_disk["bare_size"] = disk["sys_api"].get("size", None)
            reduced_disk["model"] = disk["sys_api"].get("model", None)
            return reduced_disk


def test():
    drive_group = DriveGroup("data1*")
    pprint.pprint(drive_group.data_devices)
    pprint.pprint(drive_group.shared_devices)
