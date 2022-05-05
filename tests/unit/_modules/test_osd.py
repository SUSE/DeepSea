from pyfakefs import fake_filesystem as fake_fs
from pyfakefs import fake_filesystem_glob as fake_glob
import os
import pytest
import logging
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
    def test_list(self, glob):
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
            assert ret == 'osd.0 is safe to destroy'

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

class TestCephPGs():
    """
    This class contains a set of functions that test srv.salt._modules.osd.CephPGs
    """
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def get_ceph_pgs(self):
        cephpgs = osd.CephPGs()
        cephpgs.settings = { 'conf': "/etc/ceph/ceph.conf",
                                'timeout': 0.4,
                                'keyring': '/etc/ceph/ceph.client.admin.keyring',
                                'client': 'client.admin',
                                'delay': 0.2
                            }
        cephpgs.pg_states = mock.Mock()
        return cephpgs

    def test_message_when_scrubbing(self):
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            cephpgs = self.get_ceph_pgs()
            cephpgs.pg_states.return_value = [ { "name":"active+clean+scrubbing+deep","num":128 } ]
            result = cephpgs.quiescent()
            assert isinstance(result, dict)
            assert 'result' in result
            assert 'message' in result
            assert result['result'] is False
            assert result['message'] == ("Timeout expired waiting on active+clean: "
                                         "PGs are scrubbing, "
                                         "disable scrubbing and retry.")

            scrubbing_messages = [x for x in self.caplog.records if 'PGs are scrubbing' in x.message]
            # timeout is 0.4 and delay is 0.2. That means 2 iterations should be executed
            assert len(scrubbing_messages) == 2
            for message in scrubbing_messages:
                assert message.levelno == logging.WARNING

    def test_message_when_active_clean(self):
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            cephpgs = self.get_ceph_pgs()
            cephpgs.pg_states.return_value = [ { "name":"active+clean","num":128 } ]
            result = cephpgs.quiescent()
            assert isinstance(result, dict)
            assert 'result' in result
            assert 'message' in result
            assert result['result'] is True
            assert result['message'] == ("PGs are active+clean")

    def test_message_when_unexpected_message(self):
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            cephpgs = self.get_ceph_pgs()
            cephpgs.pg_states.return_value = [ { "name":"This is not expected","num":128 } ]
            result = cephpgs.quiescent()
            assert isinstance(result, dict)
            assert 'result' in result
            assert 'message' in result
            assert result['result'] is False
            assert result['message'] == ("Timeout expired waiting on active+clean: "
                                         "PGs states: [{'name': 'This is not expected', 'num': 128}]")

    def test_message_when_no_pgs(self):
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            cephpgs = self.get_ceph_pgs()
            cephpgs.pg_states.return_value = None
            result = cephpgs.quiescent()
            assert isinstance(result, dict)
            assert 'result' in result
            assert 'message' in result
            assert result['result'] is True
            assert result['message'] == ("PGs are not present")

    def test_message_first_scrubbing_then_error(self):
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            cephpgs = self.get_ceph_pgs()
            class PGStates(object):
                def __init__(self, *fns):
                    self.fs = iter(fns)
                def __call__(self, *args, **kwargs):
                    f = next(self.fs)
                    return f(*args, **kwargs)
            def scrubbing():
                return [ { "name":"active+clean+scrubbing+deep","num":128 } ]
            def other_error():
                return [ { "name":"something_else","num":128 } ]
            cephpgs.pg_states.side_effect = PGStates(scrubbing, other_error)
            result = cephpgs.quiescent()
            assert isinstance(result, dict)
            assert 'result' in result
            assert 'message' in result
            assert result['result'] is False
            assert result['message'] == ("Timeout expired waiting on active+clean: "
                                         "PGs states: [{'name': 'something_else', 'num': 128}]")
            log_messages = [rec for rec in self.caplog.records if 'PGs are scrubbing' in rec.message]
            assert len(log_messages) == 1

    def test_message_when_more_than_1_line_scrubbing(self):
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            cephpgs = self.get_ceph_pgs()
            cephpgs.pg_states.return_value = [ { "name":"active+clean+scrubbing+deep","num":28 },
                                               { "name":"active+clean","num":50 },
                                               { "name":"active+clean+scrubbing","num":50 }]
            result = cephpgs.quiescent()
            assert isinstance(result, dict)
            assert 'result' in result
            assert 'message' in result
            assert result['result'] is False
            assert result['message'] == ("Timeout expired waiting on active+clean: "
                                         "PGs are scrubbing, "
                                         "disable scrubbing and retry.")
            scrubbing_messages = [x for x in self.caplog.records if 'PGs are scrubbing' in x.message]
            # timeout is 0.4 and delay is 0.2.
            # That means 2 iterations should be executed.
            assert len(scrubbing_messages) == 2
            for message in scrubbing_messages:
                assert message.levelno == logging.WARNING

    def test_message_more_than_1_line_no_scrubbing(self):
        with patch.object(osd.CephPGs, "__init__", lambda self: None):
            cephpgs = self.get_ceph_pgs()
            cephpgs.pg_states.return_value = [ { "name":"not-expected-1","num":28 },
                                               { "name":"active+clean","num":50 },
                                               { "name":"not-expected-2","num":50 }]
            result = cephpgs.quiescent()
            assert isinstance(result, dict)
            assert 'result' in result
            assert 'message' in result
            assert result['result'] is False
            assert result['message'] == ("Timeout expired waiting on active+clean: "
                                         "PGs states: [{'name': 'not-expected-1', 'num': 28}, {'name': 'active+clean', 'num': 50}, {'name': 'not-expected-2', 'num': 50}]")

            scrubbing_messages = [x for x in self.caplog.records if 'PGs are scrubbing' in x.message]
            assert len(scrubbing_messages) == 0
