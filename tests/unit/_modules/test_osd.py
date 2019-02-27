from pyfakefs import fake_filesystem as fake_fs
from pyfakefs import fake_filesystem_glob as fake_glob
import os
import pytest
import sys
sys.path.insert(0, 'srv/salt/_modules')
import tempfile
from srv.salt._modules import osd
from tests.unit.helper.fixtures import helper_specs
from mock import MagicMock, patch, mock, create_autospec

# workaround to 'referenced before assignment'
DEFAULT_MODULE = osd


class TestOSDInstanceMethods():
    '''
    This class contains a set of functions that test srv.salt._modules.osd
    '''
    fs = fake_fs.FakeFilesystem()
    dev_dir = '/dev'
    devices = ['sda', 'sdaa', 'sda1', 'sda10', 'sdaa1', 'sdaa10',
               'sdax', 'sdax10',
               'nvme0n1', 'nvme1n1', 'nvme100n1', 'nvme0n1p1',
               'nvme0n1p100', 'nvme0n100', 'nvme1n1p1', 'nvme100n1p1']
    for dev in devices:
        fs.CreateFile('{}/{}'.format(dev_dir, dev))

    f_glob = fake_glob.FakeGlobModule(fs)
    f_os = fake_fs.FakeOsModule(fs)
    f_open = fake_fs.FakeFileOpen(fs)

    @mock.patch('srv.salt._modules.osd.glob')
    def test_paths(self, glob):
        glob.return_value.glob = []
        ret = osd.paths()
        glob.glob.assert_called_once()
        glob.glob.assert_called_with('/var/lib/ceph/osd/*')
        assert type(ret) is list

    @mock.patch('srv.salt._modules.osd.glob')
    def test_devices(self, glob):
        glob.return_value.glob = []
        ret = osd.devices()
        glob.glob.assert_called_once()
        glob.glob.assert_called_with('/var/lib/ceph/osd/*')
        assert type(ret) is list

    @mock.patch('srv.salt._modules.osd.glob')
    def test_pairs(self, glob):
        glob.return_value.glob = []
        ret = osd.pairs()
        glob.glob.assert_called_once()
        glob.glob.assert_called_with('/var/lib/ceph/osd/*')
        assert type(ret) is list

    @pytest.mark.skip(reason="Postponed to later")
    def test_filter_devices(self):
        pass

    @pytest.mark.skip(reason="about to be refactored")
    def test_configured(self):
        pass

    @mock.patch('srv.salt._modules.osd.glob')
    def test_list_(self, glob):
        glob.return_value.glob = []
        osd.__grains__ = {'ceph': {'foo': 'mocked_grain'}}
        ret = osd.list_()
        glob.glob.assert_called_once()
        glob.glob.assert_called_with('/var/lib/ceph/osd/*/fsid')
        assert 'foo' in ret
        assert type(ret) is list
        osd.__grains__ = {}

    @mock.patch('srv.salt._modules.osd.glob')
    def test_list_no_grains(self, glob):
        glob.return_value.glob = []
        ret = osd.list_()
        glob.glob.assert_called_once()
        glob.glob.assert_called_with('/var/lib/ceph/osd/*/fsid')
        assert type(ret) is list

    @mock.patch('glob.glob', new=f_glob.glob)
    def test__find_paths_default(self):
        ret = osd._find_paths('/dev/sda')
        assert sorted(ret) == sorted(['/dev/sda10', '/dev/sda1'])

    @mock.patch('glob.glob', new=f_glob.glob)
    def test__find_paths_none(self):
        ret = osd._find_paths('/dev/sdx')
        assert ret == []

    @mock.patch('glob.glob', new=f_glob.glob)
    def test__find_paths_long(self):
        ret = osd._find_paths('/dev/sdaa')
        assert sorted(ret) == sorted(['/dev/sdaa10', '/dev/sdaa1'])

    @mock.patch('glob.glob', new=f_glob.glob)
    def test__find_paths_one_high(self):
        ret = osd._find_paths('/dev/sdax')
        assert sorted(ret) == sorted(['/dev/sdax10'])

    @mock.patch('glob.glob', new=f_glob.glob)
    def test__find_paths_nvme_1(self):
        ret = osd._find_paths('/dev/nvme0n1')
        assert sorted(ret) == sorted(['/dev/nvme0n1p1', '/dev/nvme0n1p100'])

    @mock.patch('glob.glob', new=f_glob.glob)
    def test__find_paths_nvme_2(self):
        ret = osd._find_paths('/dev/nvme0n1')
        assert sorted(ret) == sorted(['/dev/nvme0n1p1', '/dev/nvme0n1p100'])

    @mock.patch('glob.glob', new=f_glob.glob)
    def test__find_paths_nvme_3(self):
        ret = osd._find_paths('/dev/nvme1n1')
        assert ret == ['/dev/nvme1n1p1']

    @mock.patch('glob.glob', new=f_glob.glob)
    def test__find_paths_nvme_4(self):
        ret = osd._find_paths('/dev/nvme100n1')
        assert ret == ['/dev/nvme100n1p1']

    @mock.patch('srv.salt._modules.osd.time')
    def test_readlink_shortname(self, mock_time):
        osd.__salt__ = {}
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = ('', '/dev/vdb', '')
        result = osd.readlink("/dev/vdb")

        assert result == "/dev/vdb"

    @mock.patch('srv.salt._modules.osd.time')
    def test_readlink_longname(self, mock_time):
        osd.__salt__ = {}
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = ('', '/dev/sdb1', '')
        result = osd.readlink("/dev/disk/by-id/wwn-0x12345-part1")

        assert result == "/dev/sdb1"

    @mock.patch('srv.salt._modules.osd.time')
    def test_readlink_samename(self, mock_time):
        osd.__salt__ = {}
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = ('', '/dev/disk/by-id/wwn-0x12345-part1', '')
        result = osd.readlink("/dev/disk/by-id/wwn-0x12345-part1")

        assert result == "/dev/disk/by-id/wwn-0x12345-part1"



@pytest.mark.skip(reason="Low priority: skipped")
class TetstOSDState():
    pass

fs = fake_fs.FakeFilesystem()
f_glob = fake_glob.FakeGlobModule(fs)
f_os = fake_fs.FakeOsModule(fs)
f_open = fake_fs.FakeFileOpen(fs)

class TestOSDWeight():
    """
    Initial checks for the wait method.  Override the __init__ funciton to
    avoid the rados logic.  Set osd_id and settings directly.
    """

    @patch('builtins.open', new=f_open)
    @patch('srv.salt._modules.osd.OSDWeight.osd_df')
    def test_save_defaults(self, osd_df):
        """
        No files created with default values
        """
        osd_df.return_value = {'crush_weight': 0,
                               'reweight': 1.0}
        with patch.object(osd.OSDWeight, "__init__", lambda self, _id: None):
            osdw = osd.OSDWeight(0)
            osdw.osd_id = 0
            osdw.settings = {'filename': '/weight', 'rfilename': '/reweight'}
            osdw.save()
            assert f_os.path.exists('/weight') == False
            assert f_os.path.exists('/reweight') == False

    @patch('builtins.open', new=f_open)
    @patch('srv.salt._modules.osd.OSDWeight.osd_df')
    def test_save_custom_values(self, osd_df):
        """
        Files created with custom values
        """
        osd_df.return_value = {'crush_weight': 0.9,
                               'reweight': 1.1}
        with patch.object(osd.OSDWeight, "__init__", lambda self, _id: None):
            osdw = osd.OSDWeight(0)
            osdw.osd_id = 0
            osdw.settings = {'filename': '/weight', 'rfilename': '/reweight'}
            osdw.save()
            assert f_os.path.exists('/weight')
            assert f_os.path.exists('/reweight')
            with open("/weight") as weight:
                contents = weight.read().rstrip('\n')
                assert contents == "0.9"
            with open("/reweight") as reweight:
                contents = reweight.read().rstrip('\n')
                assert contents == "1.1"

        fs.RemoveFile('/weight')
        fs.RemoveFile('/reweight')

    @patch('builtins.open', new=f_open)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('srv.salt._modules.osd.OSDWeight.update_weight')
    @patch('srv.salt._modules.osd.OSDWeight.update_reweight')
    def test_restore_no_files(self, ur, uw):
        """
        Restore does nothing if files are absent
        """
        with patch.object(osd.OSDWeight, "__init__", lambda self, _id: None):
            osdw = osd.OSDWeight(0)
            osdw.osd_id = 0
            osdw.settings = {'filename': '/weight', 'rfilename': '/reweight'}
            osdw.restore()
            assert uw.call_count == 0
            assert ur.call_count == 0

    @patch('builtins.open', new=f_open)
    @patch('os.path.isfile', new=f_os.path.isfile)
    @patch('srv.salt._modules.osd.OSDWeight.update_weight')
    @patch('srv.salt._modules.osd.OSDWeight.update_reweight')
    def test_restore(self, ur, uw):
        """
        Restore calls routines with custom values
        """
        with open("/weight", 'w') as weight:
            weight.write("0.9")
        with open("/reweight", 'w') as reweight:
            reweight.write("1.1")

        with patch.object(osd.OSDWeight, "__init__", lambda self, _id: None):
            osdw = osd.OSDWeight(0)
            osdw.osd_id = 0
            osdw.settings = {'filename': '/weight', 'rfilename': '/reweight'}
            osdw.restore()
            uw.assert_called_with('0.9')
            ur.assert_called_with('1.1')

        fs.RemoveFile('/weight')
        fs.RemoveFile('/reweight')

    def test_update_weight(self):
        """
        Check that the weight command is built correctly
        """
        osd.__salt__ = {}
        osd.__salt__['helper.run'] = mock.Mock()
        with patch.object(osd.OSDWeight, "__init__", lambda self, _id: None):
            osdw = osd.OSDWeight(0)
            osdw.osd_id = 0
            osdw.settings = {'keyring': 'admin.keyring', 'client': 'client.admin'}
            osdw.update_weight('0.9')
            cmd = "ceph --keyring=admin.keyring --name=client.admin osd crush reweight osd.0 0.9"
            osd.__salt__['helper.run'].assert_called_with(cmd)

    def test_update_reweight(self):
        """
        Check that the reweight command is built correctly
        """
        osd.__salt__ = {}
        osd.__salt__['helper.run'] = mock.Mock()
        with patch.object(osd.OSDWeight, "__init__", lambda self, _id: None):
            osdw = osd.OSDWeight(0)
            osdw.osd_id = 0
            osdw.settings = {'keyring': 'admin.keyring', 'client': 'client.admin'}
            osdw.update_reweight('1.1')
            cmd = "ceph --keyring=admin.keyring --name=client.admin osd reweight osd.0 1.1"
            osd.__salt__['helper.run'].assert_called_with(cmd)

    @patch('srv.salt._modules.osd.OSDWeight.osd_safe_to_destroy')
    def test_wait(self, ostd):
        """
        Check that wait returns successfully
        """
        ostd.return_value = (0, "safe to destroy")
        with patch.object(osd.OSDWeight, "__init__", lambda self, _id: None):
            osdw = osd.OSDWeight(0)
            osdw.osd_id = 0
            osdw.settings = {'timeout': 1, 'delay': 1}
            ret = osdw.wait()
            assert ret == ""

    @patch('time.sleep')
    @patch('srv.salt._modules.osd.OSDWeight.osd_df')
    @patch('srv.salt._modules.osd.OSDWeight.osd_safe_to_destroy')
    def test_wait_timeout(self, ostd, od, sleep):
        """
        Check that wait can timeout
        """
        od = {}
        ostd.return_value = (-16, "Ceph is busy")
        with patch.object(osd.OSDWeight, "__init__", lambda self, _id: None):
            osdw = osd.OSDWeight(0)
            osdw.osd_id = 0
            osdw.settings = {'timeout': 1, 'delay': 1, 'osd_id': 0}
            ret = osdw.wait()
            assert 'Timeout expired' in ret

    @patch('time.sleep')
    @patch('srv.salt._modules.osd.OSDWeight.osd_df')
    @patch('srv.salt._modules.osd.OSDWeight.osd_safe_to_destroy')
    def test_wait_loops(self, ostd, od, sleep):
        """
        Check that wait does loop
        """
        od = {}
        ostd.return_value = (-16, "Ceph is busy")
        with patch.object(osd.OSDWeight, "__init__", lambda self, _id: None):
            osdw = osd.OSDWeight(0)
            osdw.osd_id = 0
            osdw.settings = {'timeout': 2, 'delay': 1, 'osd_id': 0}
            ret = osdw.wait()
            assert ostd.call_count == 2

class TestOSDRemove():

    @patch('osd.OSDRemove.set_partitions')
    def test_keyring_set(self, mock_sp):
        mock_device = mock.Mock()
        keyring = '/etc/ceph/ceph.client.storage.keyring'
        osdr = osd.OSDRemove(1, mock_device, None, None, keyring=keyring)
        assert osdr.keyring == keyring

    @patch('osd.OSDRemove.set_partitions')
    def test_client_set(self, mock_sp):
        # Getting exception complaint from mock class
        mock_device1 = mock.Mock()
        client = 'client.storage'
        osdr = osd.OSDRemove(1, mock_device1, None, None, client=client)
        assert osdr.client == client

    def test_set_partitions_from_osd(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions
        mock_grains = mock.Mock()
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        result = osdr.set_partitions()
        assert result == partitions

    def test_set_partitions_from_grains(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = None
        mock_grains = mock.Mock()

        osd.__grains__ = {'ceph': {'1': {'partitions': partitions}}}
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        result = osdr.set_partitions()
        assert result == partitions

    def test_set_partitions_from_grains_missing_id(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = None
        mock_grains = mock.Mock()

        osd.__grains__ = {'ceph': {'2': {'partitions': partitions}}}
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        result = osdr.set_partitions()
        assert result == None

    def test_remove_missing_id(self):
        partitions = {}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions
        mock_grains = mock.Mock()

        osd.__grains__ = {'ceph': {'1': {'partitions': partitions}},
                          'id': 'data1.ceph'}
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        result = osdr.remove()
        print(result)
        assert "OSD 1 is not present" in result

    def test_remove_when_empty_fails(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_grains = mock.Mock()
        mock_grains.delete.return_value = ""
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        osdr.empty = mock.Mock()
        osdr.empty.return_value = "Reweight failed"
        result = osdr.remove()
        assert result == "Reweight failed"

    @patch('srv.salt._modules.osd.update_destroyed')
    def test_remove_when_terminate_fails(self, mock_ud):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_grains = mock.Mock()
        mock_grains.delete.return_value = ""
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        osdr.empty = mock.Mock()
        osdr.empty.return_value = ""
        osdr.terminate = mock.Mock()
        osdr.terminate.return_value = "Failed to terminate OSD"

        result = osdr.remove()
        assert result == "Failed to terminate OSD"

    def test_remove_when_mark_destroyed_fails(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_grains = mock.Mock()
        mock_grains.delete.return_value = ""
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        osdr.empty = mock.Mock()
        osdr.empty.return_value = ""
        osdr.terminate = mock.Mock()
        osdr.terminate.return_value = ""
        osdr.mark_destroyed = mock.Mock()
        osdr.mark_destroyed.return_value = False

        result = osdr.remove()
        assert "Failed to mark OSD" in result

    @patch('srv.salt._modules.osd.update_destroyed')
    def test_remove_when_update_destroyed_fails(self, mock_ud):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_grains = mock.Mock()
        mock_grains.delete.return_value = ""
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        osdr.empty = mock.Mock()
        osdr.empty.return_value = ""
        osdr.terminate = mock.Mock()
        osdr.terminate.return_value = ""
        osdr.mark_destroyed = mock.Mock()
        osdr.mark_destroyed.return_value = True

        osdr._osd_disk = mock.Mock()
        osdr._osd_disk.return_value = '/dev/sda'

        mock_ud.return_value = "Failed to record OSD"

        result = osdr.remove()
        assert "Failed to record OSD" in result

    @patch('srv.salt._modules.osd.update_destroyed')
    def test_remove_when_unmount_fails(self, mock_ud):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_grains = mock.Mock()
        mock_grains.delete.return_value = ""
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        osdr.empty = mock.Mock()
        osdr.empty.return_value = ""
        osdr.terminate = mock.Mock()
        osdr.terminate.return_value = ""
        osdr.mark_destroyed = mock.Mock()
        osdr.mark_destroyed.return_value = True

        osdr._osd_disk = mock.Mock()
        osdr._osd_disk.return_value = '/dev/sda'

        mock_ud.return_value = ""

        osdr.unmount = mock.Mock()
        osdr.unmount.return_value = "Unmount failed"

        result = osdr.remove()
        assert result == "Unmount failed"

    @patch('srv.salt._modules.osd.update_destroyed')
    def test_remove_when_wipe_fails(self, mock_ud):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_grains = mock.Mock()
        mock_grains.delete.return_value = ""
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        osdr.empty = mock.Mock()
        osdr.empty.return_value = ""
        osdr.terminate = mock.Mock()
        osdr.terminate.return_value = ""
        osdr.mark_destroyed = mock.Mock()
        osdr.mark_destroyed.return_value = True

        osdr._osd_disk = mock.Mock()
        osdr._osd_disk.return_value = '/dev/sda'

        mock_ud.return_value = ""

        osdr.unmount = mock.Mock()
        osdr.unmount.return_value = ""
        osdr.wipe = mock.Mock()
        osdr.wipe.return_value = "Failed to wipe partition"

        result = osdr.remove()
        assert result == "Failed to wipe partition"

    @patch('srv.salt._modules.osd.update_destroyed')
    def test_remove_when_destroy_fails(self, mock_ud):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_grains = mock.Mock()
        mock_grains.delete.return_value = ""
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        osdr.empty = mock.Mock()
        osdr.empty.return_value = ""
        osdr.terminate = mock.Mock()
        osdr.terminate.return_value = ""
        osdr.mark_destroyed = mock.Mock()
        osdr.mark_destroyed.return_value = True

        osdr._osd_disk = mock.Mock()
        osdr._osd_disk.return_value = '/dev/sda'

        mock_ud.return_value = ""

        osdr.unmount = mock.Mock()
        osdr.unmount.return_value = ""
        osdr.wipe = mock.Mock()
        osdr.wipe.return_value = ""
        osdr.destroy = mock.Mock()
        osdr.destroy.return_value = "Failed to destroy OSD"

        result = osdr.remove()
        assert result == "Failed to destroy OSD"

    @patch('srv.salt._modules.osd.update_destroyed')
    def test_remove_works(self, mock_ud):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_grains = mock.Mock()
        mock_grains.delete.return_value = ""
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains)
        osdr.empty = mock.Mock()
        osdr.empty.return_value = ""
        osdr.terminate = mock.Mock()
        osdr.terminate.return_value = ""
        osdr.mark_destroyed = mock.Mock()
        osdr.mark_destroyed.return_value = True

        osdr._osd_disk = mock.Mock()
        osdr._osd_disk.return_value = '/dev/sda'

        mock_ud.return_value = ""

        osdr.unmount = mock.Mock()
        osdr.unmount.return_value = ""

        osdr.wipe = mock.Mock()
        osdr.wipe.return_value = ""
        osdr.destroy = mock.Mock()
        osdr.destroy.return_value = ""
        osdr._grains = mock.Mock()
        osdr._grains.delete.return_value = ""

        result = osdr.remove()
        assert result == ""

    @patch('srv.salt._modules.osd.update_destroyed')
    def test_remove_force_works(self, mock_ud):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_grains = mock.Mock()
        mock_grains.delete.return_value = ""
        osdr = osd.OSDRemove(1, mock_device, None, mock_grains, force=True)
        osdr.empty = mock.Mock()
        osdr.empty.return_value = ""
        osdr.terminate = mock.Mock()
        osdr.terminate.return_value = ""
        osdr.mark_destroyed = mock.Mock()
        osdr.mark_destroyed.return_value = True

        osdr._osd_disk = mock.Mock()
        osdr._osd_disk.return_value = '/dev/sda'

        mock_ud.return_value = ""

        osdr.unmount = mock.Mock()
        osdr.unmount.return_value = ""

        osdr.wipe = mock.Mock()
        osdr.wipe.return_value = ""
        osdr.destroy = mock.Mock()
        osdr.destroy.return_value = ""
        osdr._grains = mock.Mock()
        osdr._grains.delete.return_value = ""

        result = osdr.remove()
        assert result == ""

    def test_empty(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_weight = mock.Mock()
        mock_weight.save.return_value = ""
        mock_weight.update_weight.return_value = (0, "out", "err")
        mock_weight.wait.return_value = ""

        osdr = osd.OSDRemove(1, mock_device, mock_weight, None)
        result = osdr.empty()
        assert result == ""

    def test_empty_fails(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_weight = mock.Mock()
        mock_weight.save.return_value = ""
        mock_weight.update_weight.return_value = (1, "out", "err")
        mock_weight.wait.return_value = "Reweight failed"

        osdr = osd.OSDRemove(1, mock_device, mock_weight, None)
        result = osdr.empty()
        assert result == "Reweight failed"

    @patch('time.sleep')
    def test_terminate(self, mock_sleep):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (1, "out", "err")
        result = osdr.terminate()
        assert result == ""

    @patch('time.sleep')
    def test_terminate_fails(self, mock_sleep):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (0, "out", "err")
        result = osdr.terminate()
        assert "Failed to terminate OSD" in result

    fs = fake_fs.FakeFilesystem()
    f_os = fake_fs.FakeOsModule(fs)
    f_open = fake_fs.FakeFileOpen(fs)

    @patch('os.rmdir')
    @patch('builtins.open', new=f_open)
    def test_unmount(self, mock_rmdir):
        TestOSDRemove.fs.CreateFile('/proc/mounts',
            contents='''/dev/sda1 /var/lib/ceph/osd/ceph-1 rest\n''')

        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osdr._mounted = mock.Mock()
        osdr._mounted.return_value = ['/dev/sda1']

        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (0, "out", "err")

        result = osdr.unmount()

        TestOSDRemove.fs.RemoveFile('/proc/mounts')
        assert result == "" and mock_rmdir.call_count == 1

    @patch('builtins.open', new=f_open)
    def test_unmount_fails(self):
        TestOSDRemove.fs.CreateFile('/proc/mounts',
            contents='''/dev/sda1 /var/lib/ceph/osd/ceph-1 rest\n''')

        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osdr._mounted = mock.Mock()
        osdr._mounted.return_value = ['/dev/sda1']

        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (1, "out", "err")

        result = osdr.unmount()

        TestOSDRemove.fs.RemoveFile('/proc/mounts')
        assert "Unmount failed" in result

    @patch('builtins.open', new=f_open)
    def test_unmount_finds_no_match(self):
        TestOSDRemove.fs.CreateFile('/proc/mounts',
            contents='''/dev/sdb1 /var/lib/ceph/osd/ceph-1 rest\n''')

        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osdr._mounted = mock.Mock()
        osdr._mounted.return_value = []

        result = osdr.unmount()

        TestOSDRemove.fs.RemoveFile('/proc/mounts')
        assert result == ""

    # Need /dev/dm tests once we fix the missing cases

    @patch('srv.salt._modules.osd.readlink')
    def test_mounted_osd(self, mock_rl):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        mock_rl.return_value = '/dev/sda1'
        result = osdr._mounted()
        assert '/dev/sda1' in result

    @patch('srv.salt._modules.osd.readlink')
    def test_mounted_lockbox(self, mock_rl):
        partitions = {'lockbox': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        mock_rl.return_value = '/dev/sda1'
        result = osdr._mounted()
        assert '/dev/sda1' in result

    def test_mounted_none(self):
        partitions = {}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        result = osdr._mounted()
        assert result == []

    def test_wipe_with_no_partitions(self):
        partitions = {}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        result = osdr.wipe()
        assert result == ""


    @patch('os.path.exists', new=f_os.path.exists)
    def test_wipe_with_missing_partitions(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        result = osdr.wipe()
        assert result == ""

    @patch('os.path.exists', new=f_os.path.exists)
    def test_wipe(self):
        TestOSDRemove.fs.CreateFile('/dev/sda1')
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (0, "out", "err")
        result = osdr.wipe()
        TestOSDRemove.fs.RemoveFile('/dev/sda1')
        assert result == ""

    @patch('os.path.exists', new=f_os.path.exists)
    def test_wipe_fails(self):
        TestOSDRemove.fs.CreateFile('/dev/sda1')
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (1, "out", "err")
        result = osdr.wipe()
        TestOSDRemove.fs.RemoveFile('/dev/sda1')
        assert "Failed to wipe partition" in result

    def test_destroy(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osdr._osd_disk = mock.Mock()
        osdr._osd_disk.return_value = '/dev/sda'
        osdr._delete_partitions = mock.Mock()
        osdr._delete_partitions.return_value = ""
        osdr._wipe_gpt_backups = mock.Mock()
        osdr._wipe_gpt_backups.return_value = ""

        osdr._delete_osd = mock.Mock()
        osdr._delete_osd.return_value = ""

        osdr._settle = mock.Mock()
        result = osdr.destroy()
        assert result == ""

    def test_destroy_fails_partition_delete(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osdr._osd_disk = mock.Mock()
        osdr._osd_disk.return_value = '/dev/sda'
        osdr._delete_partitions = mock.Mock()
        osdr._delete_partitions.return_value = "Failed to delete partition"
        result = osdr.destroy()
        assert result == "Failed to delete partition"

    def test_destroy_fails_osd_delete(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)
        osdr._osd_disk = mock.Mock()
        osdr._osd_disk.return_value = '/dev/sda'
        osdr._delete_partitions = mock.Mock()
        osdr._delete_partitions.return_value = ""
        osdr._wipe_gpt_backups = mock.Mock()
        osdr._wipe_gpt_backups.return_value = ""

        osdr._delete_osd = mock.Mock()
        osdr._delete_osd.return_value = "Failed to delete OSD"

        result = osdr.destroy()
        assert result == "Failed to delete OSD"

    @patch('srv.salt._modules.osd.split_partition')
    def test_osd_disk(self, mock_sp):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_sp.return_value = ('/dev/sda', '1')
        osdr = osd.OSDRemove(1, mock_device, None, None)
        result = osdr._osd_disk()
        assert result == "/dev/sda"

    @patch('srv.salt._modules.osd.split_partition')
    def test_osd_disk_with_lockbox(self, mock_sp):
        partitions = {'lockbox': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_sp.return_value = ('/dev/sda', '1')
        osdr = osd.OSDRemove(1, mock_device, None, None)
        result = osdr._osd_disk()
        assert result == "/dev/sda"

    @patch('srv.salt._modules.osd.readlink')
    @patch('os.path.exists', new=f_os.path.exists)
    def test_delete_partitions_with_standalone_osd(self, mock_rl):
        TestOSDRemove.fs.CreateFile('/dev/sda1')
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_rl.return_value = '/dev/sda1'
        osdr = osd.OSDRemove(1, mock_device, None, None)

        osdr.osd_disk = '/dev/sda'

        result = osdr._delete_partitions()
        TestOSDRemove.fs.RemoveFile('/dev/sda1')
        assert result == ""

    @patch('time.sleep')
    @patch('srv.salt._modules.osd.readlink')
    @patch('os.path.exists', new=f_os.path.exists)
    def test_delete_partitions_with_nvme(self, mock_rl, mock_sleep):
        TestOSDRemove.fs.CreateFile('/dev/nvme0n1')
        partitions = {'osd': '/dev/nvme0n1p1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_rl.return_value = '/dev/nvme0n1p1'
        osdr = osd.OSDRemove(1, mock_device, None, None)

        osdr.osd_disk = '/dev/nvme0n1'

        result = osdr._delete_partitions()
        TestOSDRemove.fs.RemoveFile('/dev/nvme0n1')
        assert result == ""

    @patch('srv.salt._modules.osd.split_partition')
    @patch('srv.salt._modules.osd.readlink')
    @patch('os.path.exists', new=f_os.path.exists)
    def test_delete_partitions_working(self, mock_rl, mock_sp):
        TestOSDRemove.fs.CreateFile('/dev/sdb1')
        partitions = {'journal': '/dev/sdb1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_rl.return_value = '/dev/sdb1'
        mock_sp.return_value = ('/dev/sdb', '1')
        osdr = osd.OSDRemove(1, mock_device, None, None)

        osdr.osd_disk = '/dev/sda'
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (0, "out", "err")

        result = osdr._delete_partitions()
        TestOSDRemove.fs.RemoveFile('/dev/sdb1')
        assert result == ""

    @patch('srv.salt._modules.osd.split_partition')
    @patch('srv.salt._modules.osd.readlink')
    @patch('os.path.exists', new=f_os.path.exists)
    def test_delete_partitions_fails(self, mock_rl, mock_sp):
        TestOSDRemove.fs.CreateFile('/dev/sdb1')
        partitions = {'journal': '/dev/sdb1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        mock_rl.return_value = '/dev/sdb1'
        mock_sp.return_value = ('/dev/sdb', '1')
        osdr = osd.OSDRemove(1, mock_device, None, None)

        osdr.osd_disk = '/dev/sda'
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (1, "out", "err")

        result = osdr._delete_partitions()
        TestOSDRemove.fs.RemoveFile('/dev/sdb1')
        assert "Failed to delete partition" in result

    def test_mark_destroyed(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)

        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (0, "out", "err")

        result = osdr.mark_destroyed()
        assert result == True

    def test_mark_destroyed_with_keyring_and_client(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        keyring = '/etc/ceph/ceph.client.storage.keyring'
        client = 'client.storage'
        osdr = osd.OSDRemove(1, mock_device, None, None, keyring=keyring, client=client)

        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (0, "out", "err")

        result = osdr.mark_destroyed()
        assert result == True

    def test_mark_destroyed_fails(self):
        partitions = {'osd': '/dev/sda1'}
        mock_device = mock.Mock()
        mock_device.partitions.return_value = partitions

        osdr = osd.OSDRemove(1, mock_device, None, None)

        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (1, "out", "err")

        result = osdr.mark_destroyed()
        assert result == False

class TestOSDDestroyed():

    fs = fake_fs.FakeFilesystem()
    f_os = fake_fs.FakeOsModule(fs)
    f_open = fake_fs.FakeFileOpen(fs)

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_update(self):
        filename = "/etc/ceph/destroyedOSDs.yml"
        TestOSDDestroyed.f_os.makedirs("/etc/ceph")

        osdd = osd.OSDDestroyed()
        osdd._by_path = mock.Mock()
        osdd._by_path.return_value = '/dev/disk/by-path/virtio-pci-0000:00:04.0'

        result = osdd.update('/dev/sda', 1)
        contents = TestOSDDestroyed.f_open(filename).read()

        TestOSDDestroyed.fs.RemoveFile(filename)
        TestOSDDestroyed.f_os.rmdir("/etc/ceph")
        TestOSDDestroyed.f_os.rmdir("/etc")
        assert result == "" and contents == "/dev/disk/by-path/virtio-pci-0000:00:04.0: 1\n"

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_update_with_no_by_path(self):
        filename = "/etc/ceph/destroyedOSDs.yml"
        TestOSDDestroyed.f_os.makedirs("/etc/ceph")

        osdd = osd.OSDDestroyed()
        osdd._by_path = mock.Mock()
        osdd._by_path.return_value = None

        result = osdd.update('/dev/sda', 1)
        contents = TestOSDDestroyed.f_open(filename).read()

        TestOSDDestroyed.fs.RemoveFile(filename)
        TestOSDDestroyed.f_os.rmdir("/etc/ceph")
        TestOSDDestroyed.f_os.rmdir("/etc")
        assert "Device /dev/sda is missing" in result and contents == "/dev/sda: 1\n"

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_update_entry_exists(self):
        filename = "/etc/ceph/destroyedOSDs.yml"
        TestOSDDestroyed.fs.CreateFile(filename, contents="""/dev/sda1: '1'""")

        osdd = osd.OSDDestroyed()
        result = osdd.update('/dev/sda', 1)

        TestOSDDestroyed.fs.RemoveFile(filename)
        assert result == ""

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_update_force(self):
        filename = "/etc/ceph/destroyedOSDs.yml"

        osdd = osd.OSDDestroyed()
        osdd._by_path = mock.Mock()
        osdd._by_path.return_value = None

        result = osdd.update('/dev/sda', 1, force=True)
        contents = TestOSDDestroyed.f_open(filename).read()

        TestOSDDestroyed.fs.RemoveFile(filename)
        assert result == "" and contents == "/dev/sda: 1\n"

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_get(self):
        filename = "/etc/ceph/destroyedOSDs.yml"
        TestOSDDestroyed.fs.CreateFile(filename, contents="""/dev/disk/by-path/virtio-pci-0000:00:04.0: '1'""")
        osdd = osd.OSDDestroyed()

        osdd._by_path = mock.Mock()
        osdd._by_path.return_value = '/dev/disk/by-path/virtio-pci-0000:00:04.0'

        result = osdd.get('/dev/disk/by-path/virtio-pci-0000:00:04.0')
        TestOSDDestroyed.fs.RemoveFile(filename)
        assert result == '1'

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_get_no_match(self):
        filename = "/etc/ceph/destroyedOSDs.yml"
        TestOSDDestroyed.fs.CreateFile(filename, contents="""/dev/disk/by-path/virtio-pci-0000:00:04.0: '1'""")
        osdd = osd.OSDDestroyed()

        osdd._by_path = mock.Mock()
        osdd._by_path.return_value = '/dev/disk/by-path/virtio-pci-0000:00:10.0'

        result = osdd.get('/dev/disk/by-path/virtio-pci-0000:00:10.0')
        TestOSDDestroyed.fs.RemoveFile(filename)
        assert result is ""

    def test_by_path(self):
        osdd = osd.OSDDestroyed()

        output = """
            /dev/disk/by-path/pci-0000:00:1f.2-scsi-1:0:0:0
            /dev/disk/by-path/pci-0000:00:1f.2-ata-2"""

        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (0, output, "err")

        result = osdd._by_path("/dev/sda")
        assert result == "/dev/disk/by-path/pci-0000:00:1f.2-scsi-1:0:0:0"

    def test_by_path_no_match(self):
        osdd = osd.OSDDestroyed()

        output = ""

        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (0, output, "err")

        result = osdd._by_path("/dev/sda")
        assert result is ""

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_remove(self):
        filename = "/etc/ceph/destroyedOSDs.yml"
        TestOSDDestroyed.fs.CreateFile(filename, contents="""/dev/disk/by-path/virtio-pci-0000:00:04.0: '1'""")

        osdd = osd.OSDDestroyed()
        osdd._by_path = mock.Mock()
        osdd._by_path.return_value = "/dev/disk/by-path/virtio-pci-0000:00:04.0"

        osdd.remove('/dev/sda')

        contents = TestOSDDestroyed.f_open(filename).read()
        TestOSDDestroyed.fs.RemoveFile(filename)
        assert contents == "{}\n"

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_remove_original_device(self):
        filename = "/etc/ceph/destroyedOSDs.yml"
        TestOSDDestroyed.fs.CreateFile(filename, contents="""/dev/sda: '1'""")

        osdd = osd.OSDDestroyed()
        osdd._by_path = mock.Mock()
        osdd._by_path.return_value = "/dev/disk/by-path/virtio-pci-0000:00:04.0"

        osdd.remove('/dev/sda')

        contents = TestOSDDestroyed.f_open(filename).read()
        TestOSDDestroyed.fs.RemoveFile(filename)
        assert contents == "{}\n"

    @patch('os.path.exists', new=f_os.path.exists)
    def test_remove_missing_file(self):
        osdd = osd.OSDDestroyed()
        osdd._by_path = mock.Mock()
        osdd._by_path.return_value = "/dev/disk/by-path/virtio-pci-0000:00:04.0"

        result = osdd.remove('/dev/sda')
        assert result is None

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_dump(self):
        filename = "/etc/ceph/destroyedOSDs.yml"
        contents = "/dev/sda: '1'"
        TestOSDDestroyed.fs.CreateFile(filename, contents=contents)

        osdd = osd.OSDDestroyed()
        results = osdd.dump()
        TestOSDDestroyed.fs.RemoveFile(filename)
        assert results == {'/dev/sda': '1'}

    @patch('os.path.exists', new=f_os.path.exists)
    def test_dump_missing_file(self):
        osdd = osd.OSDDestroyed()
        results = osdd.dump()
        assert results is ""

class TestOSDGrains():

    fs = fake_fs.FakeFilesystem()
    f_os = fake_fs.FakeOsModule(fs)
    f_open = fake_fs.FakeFileOpen(fs)
    f_glob = fake_glob.FakeGlobModule(fs)

    @patch('glob.glob', new=f_glob.glob)
    def test_retain(self):
        mock_device = mock.Mock()
        mock_device.partitions.return_value = {'block': '/dev/vdb2',
                                               'osd': '/dev/vdb1'}
        mock_device.osd_fsid.return_value = '66758302-deb5-4078-b871-988c54f0eb57'
        filename = "/var/lib/ceph/osd/ceph-0/type"
        TestOSDGrains.fs.CreateFile(filename)

        osdg = osd.OSDGrains(mock_device)
        osdg._grains = mock.Mock()
        osdg.retain()
        TestOSDGrains.fs.RemoveFile(filename)
        TestOSDGrains.f_os.rmdir("/var/lib/ceph/osd/ceph-0")
        assert osdg._grains.call_count == 1
        osdg._grains.assert_called_with({'0': {'fsid': '66758302-deb5-4078-b871-988c54f0eb57', 'partitions': {'block': '/dev/vdb2', 'osd': '/dev/vdb1'}}})

    @patch('glob.glob', new=f_glob.glob)
    def test_retain_no_osds(self):
        mock_device = mock.Mock()
        mock_device.partitions.return_value = {'block': '/dev/vdb2',
                                               'osd': '/dev/vdb1'}
        mock_device.osd_fsid.return_value = '66758302-deb5-4078-b871-988c54f0eb57'
        osdg = osd.OSDGrains(mock_device)
        osdg._grains = mock.Mock()
        osdg.retain()
        assert osdg._grains.call_count == 1
        osdg._grains.assert_called_with({})

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_delete_no_file(self):
        mock_device = mock.Mock()
        mock_device.partitions.return_value = {'block': '/dev/vdb2',
                                               'osd': '/dev/vdb1'}
        mock_device.osd_fsid.return_value = '66758302-deb5-4078-b871-988c54f0eb57'
        osdg = osd.OSDGrains(mock_device)
        osdg._update_grains = mock.Mock()
        osdg.delete(1)
        assert osdg._update_grains.call_count == 0

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_delete_empty_file(self):
        filename = "/etc/salt/grains"
        TestOSDGrains.fs.CreateFile(filename)
        mock_device = mock.Mock()
        mock_device.partitions.return_value = {'block': '/dev/vdb2',
                                               'osd': '/dev/vdb1'}
        mock_device.osd_fsid.return_value = '66758302-deb5-4078-b871-988c54f0eb57'
        osdg = osd.OSDGrains(mock_device)
        osdg._update_grains = mock.Mock()
        osdg.delete(1)
        TestOSDGrains.fs.RemoveFile(filename)
        assert osdg._update_grains.call_count == 0

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_delete(self):
        filename = "/etc/salt/grains"
        contents = """
            ceph:
              '10':
                fsid: 751f74ca-dfe2-42af-9457-94b286793abf
                partitions:
                  block: /dev/vdc2
                  osd: /dev/vdc1
              '17':
                fsid: 28e231cd-cd01-40f9-aa47-e332ccf73e35
                partitions:
                  block: /dev/vdd2
                  osd: /dev/vdd1
            """

        TestOSDGrains.fs.CreateFile(filename, contents=contents)
        mock_device = mock.Mock()
        mock_device.partitions.return_value = {'block': '/dev/vdb2',
                                               'osd': '/dev/vdb1'}
        mock_device.osd_fsid.return_value = '66758302-deb5-4078-b871-988c54f0eb57'
        osdg = osd.OSDGrains(mock_device)
        osdg._update_grains = mock.Mock()
        osdg.delete(10)
        TestOSDGrains.fs.RemoveFile(filename)
        assert osdg._update_grains.call_count == 1
        expected = {'ceph':
                       {'17': {'fsid': '28e231cd-cd01-40f9-aa47-e332ccf73e35',
                               'partitions': {'block': '/dev/vdd2',
                                              'osd': '/dev/vdd1'}}}}
        osdg._update_grains.assert_called_with(expected)

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_grains_no_file(self):
        mock_device = mock.Mock()
        mock_device.partitions.return_value = {'block': '/dev/vdb2',
                                               'osd': '/dev/vdb1'}
        mock_device.osd_fsid.return_value = '66758302-deb5-4078-b871-988c54f0eb57'
        osdg = osd.OSDGrains(mock_device)
        osdg._update_grains = mock.Mock()
        osdg._grains("data")
        assert osdg._update_grains.call_count == 1
        expected = {'ceph': 'data'}
        osdg._update_grains.assert_called_with(expected)

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_grains(self):
        filename = "/etc/salt/grains"
        contents = """
            deepsea:
              - default
            """
        TestOSDGrains.fs.CreateFile(filename, contents=contents)
        mock_device = mock.Mock()
        mock_device.partitions.return_value = {'block': '/dev/vdb2',
                                               'osd': '/dev/vdb1'}
        mock_device.osd_fsid.return_value = '66758302-deb5-4078-b871-988c54f0eb57'
        osdg = osd.OSDGrains(mock_device)
        osdg._update_grains = mock.Mock()
        osdg._grains("data")
        TestOSDGrains.fs.RemoveFile(filename)
        assert osdg._update_grains.call_count == 1
        expected = {'ceph': 'data', 'deepsea': ['default']}
        osdg._update_grains.assert_called_with(expected)

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_grains_no_update(self):
        filename = "/etc/salt/grains"
        contents = """
            ceph:
              '17':
                fsid: 28e231cd-cd01-40f9-aa47-e332ccf73e35
                partitions:
                  block: /dev/vdd2
                  osd: /dev/vdd1
            """

        TestOSDGrains.fs.CreateFile(filename, contents=contents)
        mock_device = mock.Mock()
        mock_device.partitions.return_value = {'block': '/dev/vdb2',
                                               'osd': '/dev/vdb1'}
        mock_device.osd_fsid.return_value = '66758302-deb5-4078-b871-988c54f0eb57'
        osdg = osd.OSDGrains(mock_device)
        osdg._update_grains = mock.Mock()
        storage = {'17': {'fsid': '28e231cd-cd01-40f9-aa47-e332ccf73e35',
                               'partitions': {'block': '/dev/vdd2',
                                              'osd': '/dev/vdd1'}}}
        osdg._grains(storage)
        TestOSDGrains.fs.RemoveFile(filename)
        assert osdg._update_grains.call_count == 0

    @patch('builtins.open', new=f_open)
    def test_update_grains(self):
        filename = "/etc/salt/grains"
        mock_device = mock.Mock()
        mock_device.partitions.return_value = {'block': '/dev/vdb2',
                                               'osd': '/dev/vdb1'}
        mock_device.osd_fsid.return_value = '66758302-deb5-4078-b871-988c54f0eb57'
        osdg = osd.OSDGrains(mock_device)
        content = {'deepsea': ['default']}
        osd.__salt__['saltutil.sync_grains'] = mock.Mock()

        osdg._update_grains(content)
        contents = TestOSDGrains.f_open(filename).read()
        expected = "deepsea:\n- default\n"
        assert contents == expected


class TestCephPGS:

    def test_pg_value(self):
        """
        """
        states = [{'name': 'active+clean', 'num': 11}]
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            ceph_pgs = osd.CephPGs()
            ret = ceph_pgs._pg_value(states)
            assert ret == 11

    def test_pg_value_missing(self):
        """
        """
        states = []
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            ceph_pgs = osd.CephPGs()
            ret = ceph_pgs._pg_value(states)
            assert ret == 0

    @patch('srv.salt._modules.osd.CephPGs.pg_states')
    def test_quiescent(self, pg_states):
        """
        """
        pg_states.return_value = [{'name': 'active+clean', 'num': 11}]
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            ceph_pgs = osd.CephPGs()
            ceph_pgs.settings = {'timeout': 1, 'delay': 1}
            ret = ceph_pgs.quiescent()
            assert ret == None

    @patch('srv.salt._modules.osd.CephPGs.pg_states')
    def test_quiescent_on_empty_cluster(self, pg_states):
        """
        """
        pg_states.return_value = []
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            ceph_pgs = osd.CephPGs()
            ceph_pgs.settings = {'timeout': 1, 'delay': 1}
            ret = ceph_pgs.quiescent()
            assert ret == None

    @patch('time.sleep')
    @patch('srv.salt._modules.osd.CephPGs.pg_states')
    def test_quiescent_timeout(self, pg_states, sleep):
        """
        """
        pg_states.return_value = [{}, {}]
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            ceph_pgs = osd.CephPGs()
            ceph_pgs.settings = {'timeout': 1, 'delay': 1}

            with pytest.raises(RuntimeError) as excinfo:
                ret = ceph_pgs.quiescent()
                assert 'Timeout expired' in str(excinfo.value)

    @patch('time.sleep')
    @patch('srv.salt._modules.osd.CephPGs.pg_states')
    def test_quiescent_delay_is_zero(self, pg_states, sleep):
        """
        """
        pg_states.return_value = [{}, {}]
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            ceph_pgs = osd.CephPGs()
            ceph_pgs.settings = {'timeout': 1, 'delay': 0}

            with pytest.raises(ValueError) as excinfo:
                ret = ceph_pgs.quiescent()
                assert 'The delay cannot be 0' in str(excinfo.value)
