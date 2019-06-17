import pytest
import sys
sys.path.insert(0, 'srv/salt/_modules')
from srv.salt._modules import cephdisks

from mock import patch, mock_open

from collections import namedtuple


class SimpleDevice(object):
    def __init__(self, path):
        self.path = path


@pytest.fixture(scope='class')
def test_fix():
    def make_sample_data(**kwargs):
        with patch.object(cephdisks.Inventory, "__init__",
                          lambda self, **kwargs: None):
            c = cephdisks.Inventory(**kwargs)
            c.kwargs = kwargs
            device = namedtuple('Device', 'path, size')
            dev1 = device('/dev/sdb', 50000000.0)
            c.devices = [dev1]
            c.device = SimpleDevice
            c.root_disk = '/dev/sda'
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

    @patch("srv.salt._modules.cephdisks.open", new_callable=mock_open, read_data=b'/dev/sdaa1 / xfs rw,nosuid,nodev,noexec,relatime 0 0\n')
    def test_find_root_disk(self, open_mock, test_fix):
        ret = test_fix()._find_root_disk()
        assert '/dev/sdaa' == ret

    @patch("srv.salt._modules.cephdisks.open", new_callable=mock_open, read_data=b'/dev/nvme0n1p1 / xfs rw,nosuid,nodev,noexec,relatime 0 0\n')
    def test_find_root_disk_vnme(self, open_mock, test_fix):
        ret = test_fix()._find_root_disk()
        assert '/dev/nvme0n1' == ret

    @patch("srv.salt._modules.cephdisks.open", new_callable=mock_open, read_data=b'/dev/nvme0n1p1 nope xfs rw,nosuid,nodev,noexec,relatime 0 0\n')
    def test_find_root_disk_vnme(self, open_mock, test_fix):
        ret = test_fix()._find_root_disk()
        assert ret is None

    def test_is_cdrom(self, test_fix):
        inv = test_fix()
        assert inv._is_cdrom('/dev/sr0') is True

    def test_is_cdrom(self, test_fix):
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

    def test_is_rbd(self, test_fix):
        inv = test_fix()
        assert inv._is_rbd('/dev/rbd10') is True

    def test_has_sufficient_size_false(self, test_fix):
        inv = test_fix()
        assert inv._has_sufficient_size(1.0) is False

    def test_has_sufficient_size(self, test_fix):
        inv = test_fix()
        assert inv._has_sufficient_size(1000000000000.0) is True
