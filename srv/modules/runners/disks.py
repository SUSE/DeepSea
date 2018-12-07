import salt.client
import json

class Base(object):
    def __init__(self, **kwargs):
        self.local_client = salt.client.LocalClient()
        self.base_target = kwargs.get('target', '*')


class Inventory(Base):
    def __init__(self, target):
        Base.__init__(self)
        self.target = target if target is not None else self.base_target
        self.raw = self.local_client.cmd(self.target,
                                         'cmd.run',
                                         ['ceph-volume inventory --format json'])


class Matcher(object):

    def __init__(self, attr):
        self.attr = attr
        self.key = ''

    def _compare(self, disk):
        if disk.get(self.key, '') == disk.get(self.key, '!'):
            return True
        return False


class SubstringMatcher(Matcher):

    def __init__(self, attr):
        super().__init__(self)
        self.key = 'model'

    def _compare(self, disk):
        if disk.get(self.key, '') == disk.get(self.key, '!'):
            return True
        return False

class SizeMatcher(Matcher):

    def __init__(self, attr):
        super().__init__(self)
        self.attr = attr
        self.key = 'size'

    def _compare(self, disk):
        __import__('pdb').set_trace()
        if disk.get(self.key, '') == self.attr:
            return True
        return False

class RotatesMatcher(Matcher):

    def __init__(self, attr):
        super().__init__(self)
        self.attr = attr
        self.key = 'rotates'

    def _compare(self, disk):
        __import__('pdb').set_trace()
        if disk.get(self.key, '') == self.attr:
            return True
        return False


class DriveGroup(Base):
    def __init__(self, target) -> None:
        Base.__init__(self)
        self.raw: list = list(self.local_client.cmd(target,
                                                    'pillar.get',
                                                    ['drive_group']).values())[0]
        self.target: str = self.raw.get('target')
        self.data_device_attrs: dict = self.raw.get('data_devices', dict())
        self.shared_device_attrs: dict = self.raw.get('shared_devices', dict())
        self.encryption: bool = self.raw.get('encryption', False)
        self.wal_slots: int = self.raw.get('wal_slots', None)
        self.db_slots: int = self.raw.get('db_slots', None)
        # harden this
        self.matchers = self._assign_matchers()
        self.inventory = json.loads((list(Inventory(target).raw.values()))[0])

    @property
    def data_devices(self) -> list:
        data_devices: list = list()
        for name, val in self.data_device_attrs.items():
            print(name, val)
            for disk in self._reduced_disks:
                if not self.__match(disk):
                    continue
                data_devices.extend(disk)
            # find disks that match name -> val in inventory
            # extend list of disks
        return data_devices

    @property
    def _supported_filters(self):
        return ['size', 'vendor', 'model', 'rotates']

    def _assign_matchers(self):
        matchers = list()
        for k, v in self.data_device_attrs.items():
            if k == 'size':
                matchers.append(SizeMatcher(v))
            elif k == 'model':
                matchers.append(SubstringMatcher(v))
            elif k == 'vendor':
                matchers.append(SubstringMatcher(v))
            elif k == 'rotates':
                matchers.append(RotatesMatcher(v))
        return matchers

    def __match(self, disk):
        for matcher in self.matchers:
            return matcher._compare(disk)


    @property
    def _reduced_disks(self) -> list:
        disks = list()
        for disk in self.inventory:
            reduced_disk = self._reduce_inventory(disk)
            if reduced_disk:
                disks.append(reduced_disk)
        return disks

    def _reduce_inventory(self, disk) -> dict:
        # FIXME: Temp disable this check
        if disk['available'] is False: #True
            reduced_disk = {'path': disk.get('path')}
            reduced_disk['size'] = disk['sys_api'].get('human_readable_size', None)
            reduced_disk['vendor'] = disk['sys_api'].get('vendor', None)
            reduced_disk['bare_size'] = disk['sys_api'].get('size', None)
            reduced_disk['model'] = disk['sys_api'].get('model', None)
            return reduced_disk

def test():
    drive_group = DriveGroup('data1*')
    drive_group.data_devices


