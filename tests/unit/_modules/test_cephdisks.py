import pytest
import sys
sys.path.insert(0, 'srv/salt/_modules')
from srv.salt._modules import cephdisks
from tests.unit.helper.factories import DeviceFactory, SimpleDevice
from mock import patch, mock_open


@pytest.fixture(scope='class')
def test_fix():
    def make_sample_data(device_conf={}, **kwargs):
        with patch.object(cephdisks.Inventory, "__init__",
                          lambda self, **kwargs: None):
            c = cephdisks.Inventory(**kwargs)
            c.kwargs = kwargs
            if device_conf:
                c.devices = DeviceFactory(device_conf).produce()
            else:
                c.devices = DeviceFactory(dict(pieces=1)).produce()
            c.device = SimpleDevice
            c.root_disk = '/dev/sda'
            c.raid_devices = set([])
            return c

    return make_sample_data


class TestInventory(object):
    def test_inventory_init_defaults(self, test_fix):
        inv = test_fix()
        assert inv.exclude_available is False
        assert inv.exclude_used_by_ceph is False
        assert inv.exclude_root_disk is True

    def test_inventory_init_kwargs(self, test_fix):
        inv = test_fix(
            exclude_available=True,
            exclude_used_by_ceph=True,
            exclude_root_disk=False)
        assert inv.exclude_available is True
        assert inv.exclude_used_by_ceph is True
        assert inv.exclude_root_disk is False
        assert inv._min_osd_size == 5368709120.0

    @pytest.mark.skip(reason='will be offloaded to ceph-volume')
    def test_osd_list(self):
        pass

    @patch(
        "srv.salt._modules.cephdisks.open",
        new_callable=mock_open,
        read_data=b'/dev/sdaa1 / xfs rw,nosuid,nodev,noexec,relatime 0 0\n')
    def test_find_root_disk(self, open_mock, test_fix):
        ret = test_fix()._find_root_disk()
        assert '/dev/sdaa' == ret

    @patch(
        "srv.salt._modules.cephdisks.open",
        new_callable=mock_open,
        read_data=b'/dev/nvme0n1p1 / xfs rw,nosuid,nodev,noexec,relatime 0 0\n'
    )
    def test_find_root_disk_vnme(self, open_mock, test_fix):
        ret = test_fix()._find_root_disk()
        assert '/dev/nvme0n1' == ret

    @patch(
        "srv.salt._modules.cephdisks.open",
        new_callable=mock_open,
        read_data=
        b'/dev/nvme0n1p1 nope xfs rw,nosuid,nodev,noexec,relatime 0 0\n')
    def test_find_root_disk_vnme(self, open_mock, test_fix):
        ret = test_fix()._find_root_disk()
        assert ret is None

    @patch('srv.salt._modules.cephdisks.Popen')
    def test_find_raid_dev(self, po, test_fix):
        po.return_value.communicate.return_value = (b'md126 : active raid1 sdb1[0] sdd1[1]\nmd127 : active raid0 sdb2[0] sdd2[1]\n', '')
        ret = test_fix()._find_raid_devices()
        assert ret == set({'/dev/sdb', '/dev/sdd'})

    @patch('srv.salt._modules.cephdisks.Popen')
    def test_find_raid_dev_empty(self, po, test_fix):
        po.return_value.communicate.return_value = (b'', '')
        ret = test_fix()._find_raid_devices()
        assert ret == set([])

    @patch('srv.salt._modules.cephdisks.Popen')
    def test_find_raid_nvme(self, po, test_fix):
        po.return_value.communicate.return_value = (b'md126 : active raid1 nvme0n1p1[0] nvme0n1p2[1]\nmd127 : active raid0 sdb2[0] sdd2[1]\n', '')
        ret = test_fix()._find_raid_devices()
        assert ret == set({'/dev/sdb', '/dev/nvme0n1', '/dev/sdd'})

    def test_is_cdrom(self, test_fix):
        inv = test_fix()
        assert inv._is_cdrom('/dev/sr0') is True

    def test_is_mdraid(self, test_fix):
        inv = test_fix()
        assert inv._is_mdraid('/dev/md127') is True

    def test_is_cdrom_10(self, test_fix):
        inv = test_fix()
        assert inv._is_cdrom('/dev/sr10') is True

    def test_is_cdrom_false(self, test_fix):
        inv = test_fix()
        assert inv._is_cdrom('/dev/sdb') is False

    def test_is_rbd_false(self, test_fix):
        inv = test_fix()
        assert inv._is_rbd('/dev/sdb') is False

    def test_is_rbd(self, test_fix):
        inv = test_fix()
        assert inv._is_rbd('/dev/rbd') is True

    def test_is_rbd_10(self, test_fix):
        inv = test_fix()
        assert inv._is_rbd('/dev/rbd10') is True

    def test_has_sufficient_size_false(self, test_fix):
        inv = test_fix()
        assert inv._has_sufficient_size(1.0) is False

    def test_has_sufficient_size(self, test_fix):
        inv = test_fix()
        assert inv._has_sufficient_size(1000000000000.0) is True

    def test_filter(self, test_fix):
        """ Base test """
        inv = test_fix()
        ret = inv.filter_()
        assert len(ret) == 1

    def test_filter_available_device(self, test_fix):
        """ /dev/sdb is the available_device """
        conf = dict(
            pieces=1, device_config=dict(path='/dev/sdb', available=True))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 1

    def test_filter_available_device_exclusion(self, test_fix):
        """ /dev/sdb is the available_device but we exclude it """
        conf = dict(
            pieces=1, device_config=dict(path='/dev/sdb', available=True))
        inv = test_fix(conf, exclude_available=True)
        ret = inv.filter_()
        assert len(ret) == 0

    def test_filter_root_device(self, test_fix):
        """ /dev/sda is the root_device """
        conf = dict(pieces=1, device_config=dict(path='/dev/sda'))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 0

    def test_filter_root_device_no_exclusion(self, test_fix):
        """ /dev/sda is the root_device but we don't exclude it """
        conf = dict(pieces=1, device_config=dict(path='/dev/sda'))
        inv = test_fix(conf, exclude_root_disk=False)
        ret = inv.filter_()
        assert len(ret) == 1

    def test_filter_used_by_ceph_device(self, test_fix):
        """ /dev/sdb is the used_by_ceph_device """
        conf = dict(
            pieces=1, device_config=dict(path='/dev/sdb', used_by_ceph=True))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 1

    def test_filter_used_by_ceph_device_exclusion(self, test_fix):
        """ /dev/sdb is the used_by_ceph_device but we don't exclude it """
        conf = dict(
            pieces=1, device_config=dict(path='/dev/sdb', used_by_ceph=True))
        inv = test_fix(conf, exclude_used_by_ceph=True)
        ret = inv.filter_()
        assert len(ret) == 0

    def test_filter_cdrom(self, test_fix):
        conf = dict(pieces=1, device_config=dict(path='/dev/sr0'))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 0

    def test_filter_rbd(self, test_fix):
        conf = dict(pieces=1, device_config=dict(path='/dev/rbd0'))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 0

    def test_filter_too_small(self, test_fix):
        conf = dict(pieces=1, device_config=dict(path='/dev/sdb', size=0))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 0

    def test_filter_mapper_and_encrypted(self, test_fix):
        conf = dict(
            pieces=1,
            device_config=dict(
                path='/dev/sdb', is_mapper=True, is_encrypted=True))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 0

    def test_filter_encrypted(self, test_fix):
        conf = dict(
            pieces=1,
            device_config=dict(
                path='/dev/sdb', is_mapper=False, is_encrypted=True))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 1

    def test_filter_mapper(self, test_fix):
        conf = dict(
            pieces=1,
            device_config=dict(
                path='/dev/sdb', is_mapper=True, is_encrypted=False))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 1

    def test_filter_mdraid(self, test_fix):
        conf = dict(
            pieces=1,
            device_config=dict(
                path='/dev/md127'))
        inv = test_fix(conf)
        ret = inv.filter_()
        assert len(ret) == 0

    @pytest.mark.skip(reason="Offloaded to ceph-volume")
    def test_find_by_osd_id(self):
        pass
