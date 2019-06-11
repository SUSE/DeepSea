import pytest
import salt.client
import os
import sys
sys.path.insert(0, 'srv/salt/_modules')
from pyfakefs import fake_filesystem, fake_filesystem_glob
from mock import patch, MagicMock, mock
from srv.salt._modules import subvolume

fs = fake_filesystem.FakeFilesystem()
f_glob = fake_filesystem_glob.FakeGlobModule(fs)
f_os = fake_filesystem.FakeOsModule(fs)
f_open = fake_filesystem.FakeFileOpen(fs)

class Testsubvolume():

    @patch('srv.salt._modules.subvolume._btrfs')
    def test_check_mounted(self, mockb):
        mockb.return_value = [True, True]
        state, msg = subvolume.check()
        assert state == True
        assert msg == "/var/lib/ceph subvolume mounted"

    @patch('srv.salt._modules.subvolume._btrfs')
    def test_check_not_btrfs(self, mockb):
        mockb.return_value = [False, False]
        state, msg = subvolume.check()
        assert state == True
        assert msg == "/ is not btrfs"

    @patch('srv.salt._modules.subvolume._subvol')
    @patch('srv.salt._modules.subvolume._btrfs')
    def test_check_fails_with_no_mount(self, mockb, mocks):
        mockb.return_value = [True, False]
        mocks.return_value = True
        state, msg = subvolume.check()
        assert state == False
        assert msg == "/var/lib/ceph not mounted"

    @patch('srv.salt._modules.subvolume._subvol')
    @patch('srv.salt._modules.subvolume._btrfs')
    def test_check_fails_missing(self, mockb, mocks):
        mockb.return_value = [True, False]
        mocks.return_value = False
        state, msg = subvolume.check()
        assert state == False
        assert msg == "/var/lib/ceph subvolume missing"

    @patch('builtins.open', new=f_open)
    def test_btrfs_mounted(self):
        fs.CreateFile("/proc/mounts", contents="/dev/sda1 / btrfs rw,relatime\n/dev/sda1 /var/lib/ceph btrfs rw,relatime,space_cache,subvolid=286,subvol=/@/var/lib/ceph\n")
        btrfs, mounted = subvolume._btrfs()
        fs.RemoveFile("/proc/mounts")
        assert btrfs == True
        assert mounted == True

    @patch('builtins.open', new=f_open)
    def test_btrfs_unmounted(self):
        fs.CreateFile("/proc/mounts", contents="/dev/sda1 / btrfs rw,relatime\n")
        btrfs, mounted = subvolume._btrfs()
        fs.RemoveFile("/proc/mounts")
        assert btrfs == True
        assert mounted == False

    @patch('builtins.open', new=f_open)
    def test_btrfs_other_fs(self):
        fs.CreateFile("/proc/mounts", contents="/dev/sda1 / xfs rw,relatime\n")
        btrfs, mounted = subvolume._btrfs()
        fs.RemoveFile("/proc/mounts")
        assert btrfs == False
        assert mounted == False

    def test_subvol(self):
        subvolume.__salt__ = {}
        subvolume.__salt__['helper.run'] = mock.Mock()
        subvolume.__salt__['helper.run'].return_value = (0, ["ID 286 gen 363 top level 265 path @/var/lib/ceph"], "")
        result = subvolume._subvol()
        assert result == True

    def test_subvol_fails(self):
        subvolume.__salt__ = {}
        subvolume.__salt__['helper.run'] = mock.Mock()
        subvolume.__salt__['helper.run'].return_value = (0, ["ID 286 gen 363 top level 265 path @/var"], "")
        result = subvolume._subvol()
        assert result == False

