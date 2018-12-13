from pyfakefs import fake_filesystem as fake_fs
from pyfakefs import fake_filesystem_glob as fake_glob
import pytest
import sys
sys.path.insert(0, 'srv/salt/_modules')
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

    @pytest.mark.skip(reason="Low priority: skipped")
    def test_readlink(self):
        pass


@pytest.mark.skip(reason="Low priority: skipped")
class TetstOSDState():
    pass

class TestOSDWeight():
    """
    Initial checks for the wait method.  Override the __init__ funciton to
    avoid the rados logic.  Set osd_id and settings directly.
    """

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


class TestOSDConfig():
    @pytest.fixture(scope='class')
    def osd_o(self):
        with patch.object(osd.OSDConfig, '__init__', lambda self: None):
            print("Constructing the OSDConfig object")
            cnf = osd.OSDConfig()
            cnf.device = '/dev/sdx'
            # monkeypatching the device in the object since __init__
            # is mocked -> skipping the readlink()
            yield cnf
            # everything after the yield is a teardown code
            print("Teardown OSDConfig object")

    @pytest.mark.skip(reason='skip')
    def test__set_tli(self):
        pass

    @pytest.mark.skip(reason='skip')
    def test_convert_tli(self):
        pass

    def test_set_bytes_valid(self, osd_o):
        osd.__grains__ = {'id': 'data1.ceph'}
        cephdisks_out = {'data1.ceph': [{'Device File': '/dev/sdx', 'Bytes': 1000000}]}
        osd.__salt__ = {'mine.get': lambda tgt, fun: cephdisks_out}
        ret = osd_o.set_bytes()
        assert type(ret) is int
        assert ret == 1000000

    def test_set_bytes_invalid(self, osd_o):
        osd.__grains__ = {'id': 'data1.ceph'}
        cephdisks_out = {}
        osd.__salt__ = {'mine.get': lambda tgt, fun: cephdisks_out}
        with pytest.raises(RuntimeError) as excinfo:
            osd_o.set_bytes()
            assert 'Mine on data1.ceph' in str(excinfo.value)

    def test_set_capacity(self, osd_o):
        osd.__grains__ = {'id': 'data1.ceph'}
        cephdisks_out = {'data1.ceph': [{'Device File': '/dev/sdx', 'Capacity': 1000000}]}
        osd.__salt__ = {'mine.get': lambda tgt, fun: cephdisks_out}
        osd.__grains__ = {'id': 'data1.ceph'}
        ret = osd_o.set_capacity()
        assert ret == 1000000

    def test_set_capacity_invalid(self, osd_o):
        osd.__grains__ = {'id': 'data1.ceph'}
        cephdisks_out = {}
        osd.__salt__ = {'mine.get': lambda tgt, fun: cephdisks_out}
        osd.__grains__ = {'id': 'data1.ceph'}
        with pytest.raises(RuntimeError) as excinfo:
            osd_o.set_capacity()
            assert 'Mine on data1.ceph' in str(excinfo.value)

    def test_small_size_false(self, osd_o):
        osd_o.size = 10000000000
        ret = osd_o._set_small()
        assert ret is False

    def test_small_size_true(self, osd_o):
        osd_o.size = 1
        ret = osd_o._set_small()
        assert ret is True

    def test_config_version_old(self, osd_o):
        osd.__pillar__ = {'storage': {'osds': '1'}}
        ret = osd_o._config_version()
        assert ret == 'v1'

    def test_config_version_new(self, osd_o):
        osd.__pillar__ = {'ceph': {'storage': '1'}}
        ret = osd_o._config_version()
        assert ret == 'v2'

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    def test_set_format_filestore(self, conf_mock, osd_o):
        conf_mock.return_value = 'v1'
        ret = osd_o.set_format()
        assert ret is 'filestore'

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    def test_set_format_bluestore_custom(self, conf_mock, osd_o):
        conf_mock.return_value = 'v2'
        osd_o.tli = {'/dev/sdx': {'format': 'custom_store'}}
        ret = osd_o.set_format()
        assert ret is 'custom_store'

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    def test_set_format_bluestore_default(self, conf_mock, osd_o):
        osd_o.tli = {'/dev/sdx': {}}
        conf_mock.return_value = 'v2'
        ret = osd_o.set_format()
        assert ret is 'bluestore'

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    def test_set_format_raise(self, conf_mock, osd_o):
        conf_mock.return_value = 'v3'
        with pytest.raises(BaseException) as excinfo:
            osd_o.set_format()
            assert 'Mine on data1.ceph' in str(excinfo.value)

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._convert_data_journals')
    def test_set_journal_default(self, convert_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v1'
        osd.__pillar__ = {'storage':{'data+journals':[]}}
        convert_mock.return_value = {}
        ret = osd_o.set_journal()
        assert ret is False

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._convert_data_journals')
    def test_set_journal_v1_no_journal(self, convert_mock, conf_mock, osd_o):
        """
        Given you only have OSDs without separate journals
        """
        conf_mock.return_value = 'v1'
        convert_mock.return_value = {}
        osd.__pillar__ = {'storage':{'data+journals':[]}}
        ret = osd_o.set_journal()
        assert ret is False

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._convert_data_journals')
    def test_set_journal_v1_journal(self, convert_mock, conf_mock, osd_o):
        """
        Given you have OSDs separate journals
        """
        conf_mock.return_value = 'v1'
        convert_mock.return_value = {'/dev/sdx': '/dev/journal'}
        osd.__pillar__ = {'storage':{'data+journals':[]}}
        ret = osd_o.set_journal()
        assert ret is '/dev/journal'

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._convert_data_journals')
    def test_set_journal_v1_journal_no_dev_found(self, convert_mock, conf_mock, osd_o):
        """
        Given you have OSDs separate journals but the device doesn't match
        """
        conf_mock.return_value = 'v1'
        convert_mock.return_value  = {'DOESNOTMATCH': '/dev/journal'}
        osd.__pillar__ = {'storage':{'data+journals':[]}}
        ret = osd_o.set_journal()
        assert ret is False

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    def test_set_journal_v2_tli_journal(self, conf_mock, osd_o):
        """
        Given you have a journal entry in the TLI
        """
        conf_mock.return_value = 'v2'
        osd_o.tli = {'/dev/sdx': {'journal': '/dev/journal'}}
        ret = osd_o.set_journal()
        assert ret is '/dev/journal'

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    def test_set_journal_v2_tli_no_journal(self, conf_mock, osd_o):
        """
        Given you don't have a journal entry in the TLI
        """
        conf_mock.return_value = 'v2'
        osd_o.tli = {'/dev/sdx': {}}
        ret = osd_o.set_journal()
        assert ret is False

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    def test_set_journal_v2_no_tli_no_journal(self, conf_mock, osd_o):
        """
        Given you don't have a journal entry and no TLI
        """
        conf_mock.return_value = 'v2'
        osd_o.tli = {'NOTFOUND': {}}
        ret = osd_o.set_journal()
        assert ret is False

    @mock.patch('srv.salt._modules.osd.readlink')
    def test_convert_data_journals(self, readlink, osd_o):
        #                       why reverse?
        readlink.side_effect = ['/dev/journal', '/dev/sdx']
        data = [{'/dev/sdx': '/dev/journal'}]
        ret = osd_o._convert_data_journals(data)
        assert ret == {'/dev/sdx': '/dev/journal'}

    @mock.patch('srv.salt._modules.osd.readlink')
    def test_convert_data_journals_empty(self, readlink, osd_o):
        #                       why reverse?
        readlink.side_effect = ['/dev/journal', '/dev/sdx']
        data = []
        ret = osd_o._convert_data_journals(data)
        assert ret == {}

    def test_check_existence(self, osd_o):
        device = '/dev/sdx'
        ident = {'/dev/sdx': {'key': 'value'}}
        key = 'key'
        ret = osd_o._check_existence(key, ident, device)
        assert ret == 'value'

    def test_check_existence_default(self, osd_o):
        device = '/dev/sdx'
        ident = {'/dev/sdx': {'key': 'value'}}
        key = 'DOES NOT MATCH'
        ret = osd_o._check_existence(key, ident, device)
        assert ret == None

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._journal_default')
    def test_journal_size_v1(self, journal_default, config_version, osd_o):
        config_version.return_value = 'v1'
        journal_default.return_value = '5242880K'
        ret = osd_o.set_journal_size()
        assert ret == '5242880K'

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._journal_default')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_journal_size_v2(self, check_ex, journal_default, config_version, osd_o):
        check_ex.return_value = '100000'
        config_version.return_value = 'v2'
        journal_default.return_value = '5242880K'
        ret = osd_o.set_journal_size()
        assert ret == '100000'

    def test_journal_default_journal_disks_smaller_10(self, osd_o):
        """
        Given you have a journal
        And it's not a colocated journal
        And you have disks
        And you have disks['Device File'] == journal
        And the disk is smaller than 10G
        Expect the return to be (disksize*0.0001) -> in K
        """
        osd_o.journal = '/dev/sdx'
        osd.__grains__ = {'id': 'data1.ceph'}
        cephdisks_out = {'data1.ceph': [{'Device File': '/dev/sdx', 'Bytes': 1000000}]}
        osd.__salt__ = {'mine.get': lambda tgt, fun: cephdisks_out}
        ret = osd_o._journal_default()
        assert ret == '100K'

    def test_journal_default_journal_disks_bigger_10(self, osd_o):
        """
        Given you have a journal
        And it's not a colocated journal
        And you have disks
        And you have disks['Device File'] == journal
        And the disk is _not_ smaller than 10G
        Expect the return to be the default of 5242880K
        """
        osd_o.journal = '/dev/sdx'
        osd.__grains__ = {'id': 'data1.ceph'}
        cephdisks_out = {'data1.ceph': [{'Device File': '/dev/sdx', 'Bytes': 1000000000000}]}
        osd.__salt__ = {'mine.get': lambda tgt, fun: cephdisks_out}
        ret = osd_o._journal_default()
        assert ret == "5242880K"

    def test_journal_default_journal_mismatch(self, osd_o):
        """
        Given you have a journal
        And it's not in the cephdisks.list return
        Expect to log and return None
        """
        osd_o.journal = '/dev/NOT_THE_DEVICE'
        osd.__grains__ = {'id': 'data1.ceph'}
        cephdisks_out = {'data1.ceph': [{'Device File': '/dev/sdx', 'Bytes': 1000000000000}]}
        osd.__salt__ = {'mine.get': lambda tgt, fun: cephdisks_out}
        ret = osd_o._journal_default()
        assert ret == None

    def test_journal_default_no_journal_small_size(self, osd_o):
        """
        Given you _don't_ have a journal
        And it's a colocated journal
        self.small is set
        self.size is set
        Expect the return to be (disksize*0.0001) -> in K
        """
        osd_o.journal = None
        osd_o.small = True
        osd_o.size = 10000000
        ret = osd_o._journal_default()
        assert ret == "1000K"

    def test_journal_default_no_journal_no_small_size(self, osd_o):
        """
        Given you _don't_ have a journal
        And it's a colocated journal
        self.small is _not_ set
        self.size is set
        Expect the return to be 5242880K
        """
        osd_o.journal = None
        osd_o.small = False
        ret = osd_o._journal_default()
        assert ret == "5242880K"

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_wal_size_v2(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v2'
        check_mock.return_value = True
        ret = osd_o.set_wal_size()
        check_mock.assert_called_once()
        assert ret is True

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_wal_size_v1(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v1'
        check_mock.return_value = True
        ret = osd_o.set_wal_size()
        assert ret is None

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_wal_v1(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v1'
        check_mock.return_value = True
        ret = osd_o.set_wal()
        assert ret is None

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_wal_v2(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v2'
        check_mock.return_value = True
        ret = osd_o.set_wal()
        check_mock.assert_called_once()
        assert ret is True

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_db_size_v1(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v1'
        check_mock.return_value = True
        ret = osd_o.set_db_size()
        assert ret is None

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_db_size_v2(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v2'
        check_mock.return_value = True
        ret = osd_o.set_db_size()
        check_mock.assert_called_once()
        assert ret is True

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_db_v1(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v1'
        check_mock.return_value = True
        ret = osd_o.set_db_size()
        assert ret is None

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_db_v2(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v2'
        check_mock.return_value = True
        ret = osd_o.set_db_size()
        check_mock.assert_called_once()
        assert ret is True

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_encryption_v2(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v2'
        check_mock.return_value = True
        ret = osd_o.set_db_size()
        check_mock.assert_called_once()
        assert ret is True

    @mock.patch('srv.salt._modules.osd.OSDConfig._config_version')
    @mock.patch('srv.salt._modules.osd.OSDConfig._check_existence')
    def test_set_encryption_v1(self, check_mock, conf_mock, osd_o):
        conf_mock.return_value = 'v1'
        check_mock.return_value = True
        ret = osd_o.set_db_size()
        assert ret is None

    def test_set_types(self, osd_o):
        ret = osd_o.set_types()
        assert type(ret) is dict

class OSDConfig(object):

    def __init__(self, **kwargs):
        self.device = kwargs.get('device', '/dev/sdx')
        self.disk_format = kwargs.get('format', 'filestore')
        self.journal = kwargs.get('journal', None)
        self.small = kwargs.get('small', False)
        self.capacity = kwargs.get('capacity', '10000000000K')
        self.size = kwargs.get('size', '10000000000K')
        self.journal_size = kwargs.get('journal_size', '52428000K')
        self.wal_size = kwargs.get('wal_size', None)
        self.wal = kwargs.get('wal', False)
        self.db = kwargs.get('db', False)
        self.db_size = kwargs.get('db_size', None)
        self.encryption = kwargs.get('encryption', None)
        self.types = {'osd': '4FBD7E29-9D25-41B8-AFD0-062C0CEFF05D',
                      'journal': '45B0969E-9B03-4F30-B4C6-B4B80CEFF106',
                      'wal': '5CE17FCE-4087-4169-B7FF-056CC58473F9',
                      'db': '30CD0809-C2B2-499C-8879-2D6B78529876',
                      'lockbox': 'FB3AABF9-D25F-47CC-BF5E-721D1816496B'}

class TestOSDPartitions():

    def test_clean_skips(self):
        kwargs = {'format': 'none'}
        osd_config = OSDConfig(**kwargs)

        osdp = osd.OSDPartitions(osd_config)
        osdp._find_paths = mock.Mock()
        osdp.clean()
        assert osdp._find_paths.call_count == 0

    @mock.patch('srv.salt._modules.osd._find_paths')
    def test_clean_no_paths(self, mock_fp):
        osd_config = OSDConfig()

        osdp = osd.OSDPartitions(osd_config)
        mock_fp.return_value = 0
        osdp.clean()
        assert mock_fp.call_count == 1

    @mock.patch('srv.salt._modules.osd._find_paths')
    def test_clean(self, mock_fp):
        osd_config = OSDConfig()

        osdp = osd.OSDPartitions(osd_config)
        mock_fp.return_value = ['/dev/sda1']
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (0, "out", "err")
        osdp.clean()
        assert mock_fp.call_count == 1
        assert osd.__salt__['helper.run'].call_count == 1

    @mock.patch('srv.salt._modules.osd._find_paths')
    def test_clean_raises_exception(self, mock_fp):
        osd_config = OSDConfig()

        osdp = osd.OSDPartitions(osd_config)
        mock_fp.return_value = ['/dev/sda1']
        osd.__salt__['helper.run'] = mock.Mock()
        osd.__salt__['helper.run'].return_value = (1, "out", "err")
        with pytest.raises(RuntimeError) as excinfo:
            osdp.clean()

    @mock.patch('srv.salt._modules.osd.OSDPartitions._xfs_partitions')
    def test_partition_filestore(self, xfs_part_mock, helper_specs):
        kwargs = {'format': 'filestore'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj.partition()
        xfs_part_mock.assert_called_with(obj.osd.device, obj.osd.size)

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_colocated(self, create_mock, helper_specs):
        """
        Given I have a journal
        And I have set the journal_size
        And the journal equals the device
        Expect a create() invocation with params:
            `journal, list(set(journal_size, journal_size), set(osd, None))`
        """
        kwargs = {'format': 'filestore', 'journal': '/dev/sdx', 'journal_size': 1000000}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_called_with(obj.osd.journal, [('journal', obj.osd.journal_size), ('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_not_colocated(self, create_mock, helper_specs):
        """
        Given I have a journal
        And I have set the journal_size
        And the journal doesn't equal the device
        Expect a create() invocations with params:
            `journal, list(set(journal_size, journal_size)`
            `set(osd, None))`
        """
        kwargs = {'format': 'filestore', 'journal': '/dev/sdz', 'journal_size': 1000000}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_any_call(obj.osd.journal, [('journal', obj.osd.journal_size)])
        create_mock.assert_any_call(obj.osd.device, [('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_colocated_no_journal_size(self, create_mock, helper_specs):
        """
        Given I have a journal
        And I _haven't_ set the journal_size
        And the journal does equal the device
        Expect a create() invocations with params:
            `journal, list(set(journal_size, journal_size)`
            `set(osd, None))`
        """
        kwargs = {'format': 'filestore'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_called_with(obj.osd.device, [('journal', obj.osd.journal_size), ('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_not_colocated_no_journal_size(self, create_mock, helper_specs):
        """
        Given I have a journal
        And I haven't set the journal_size
        And the journal doesn't equal the device
        Expect a create() invocations with params:
            `journal, list(set(journal_size, journal_size)`
            `set(osd, None))`
        """
        kwargs = {'format': 'filestore',
                  'journal': '/dev/journal'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_any_call(obj.osd.journal, [('journal', obj.osd.journal_size)])
        create_mock.assert_any_call(obj.osd.device, [('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_no_journal(self, create_mock, helper_specs):
        """
        Given I don't have a journal
        And I have set the journal_size
        Expect a create() invocation with params:
            `device, list(set(journal_size, journal_size), set(osd, None))`
        """
        kwargs = {'format': 'filestore'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_called_with(obj.osd.device, [('journal', obj.osd.journal_size), ('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_no_journal_small(self, create_mock, helper_specs):
        """
        Given I don't have a journal
        And I have set the journal_size
        And small is set
        Expect a create() invocation with params:
            `device, list(set(journal_size, journal_size), set(osd, None))`
        """
        kwargs = {'format': 'filestore'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_called_with(obj.osd.device, [('journal', obj.osd.journal_size), ('osd', None)])

    @pytest.mark.skip(reason='low priority: skip for now')
    def test_double(self):
        pass

    @pytest.mark.skip(reason='low priority: skip for now')
    def test_halve(self):
        pass

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_log(self, mock_log, helper_specs):
        """
        Given I defined a wal and a db
        And I have a wal_size
        And wal is equivalent to the device
        Expect to call log() ( and leave the partition creation to ceph-disk )
        """
        kwargs = {'format':
                  'bluestore',
                  'wal': '/dev/sdx',
                  'db': '/dev/sdx',
                  'wal_size': '1000'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_called_with('No size specified for db /dev/sdx. Using default sizes')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_log_db_size(self, mock_log, helper_specs):
        """
        Given I defined a wal and a db
        And I have a wal_size
        And I have a db_size
        And wal is equivalent to the device
        Expect to call log() ( and leave the partition creation to ceph-disk )
        Expect to call log() ( and leave the partition creation to ceph-disk )
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sdx',
                  'db': '/dev/sdx',
                  'wal_size': '1000',
                  'db_size': 10000}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_any_call('WAL size is unsupported for same device of /dev/sdx')
        mock_log.warning.assert_any_call('DB size is unsupported for same device of /dev/sdx')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_encrypted_log(self, mock_log, helper_specs):
        """
        Given I defined a wal and a db
        And I encrypt with dmcrypt
        Expect to call log() ( and leave the partition creation to ceph-disk )
        Expect to call log() ( and leave the partition creation to ceph-disk )
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sddb',
                  'encryption': 'dmcrypt',
                  'db': '/dev/sdwal',
                  'wal_size': '1000',
                  'db_size': 10000}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_any_call('You deploy encrypted WAL and/or DB on a dedicated device. Specifying sizes is now handled via your ceph.conf')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_encrypted_log(self, mock_log, helper_specs):
        """
        Given I defined a wal
        And I encrypt with dmcrypt
        Expect to call log() ( and leave the partition creation to ceph-disk )
        Expect to call log() ( and leave the partition creation to ceph-disk )
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sddb',
                  'encryption': 'dmcrypt',
                  'wal_size': '1000',
                  'db_size': 10000}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_any_call('You deploy encrypted WAL and/or DB on a dedicated device. Specifying sizes is now handled via your ceph.conf')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_db_encrypted_log(self, mock_log, helper_specs):
        """
        Given I defined a db
        And I encrypt with dmcrypt
        Expect to call log() ( and leave the partition creation to ceph-disk )
        Expect to call log() ( and leave the partition creation to ceph-disk )
        """
        kwargs = {'format': 'bluestore',
                  'encryption': 'dmcrypt',
                  'db': '/dev/sdwal',
                  'wal_size': '1000',
                  'db_size': 10000}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_any_call('You deploy encrypted WAL and/or DB on a dedicated device. Specifying sizes is now handled via your ceph.conf')

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_bluestore_partitions_wal_and_db_all_size_no_eq(self, create_mock, helper_specs):
        """
        Given I defined a wal and a db
        And I have a wal_size
        And I have a db_size
        And wal is not equivalent to the device
        Expect to call create('/dev/sddb', [('db', db_size)])
        Expect to call create('/dev/sdwal', [('wal', wal_size)])
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sdwal',
                  'db': '/dev/sddb',
                  'wal_size': 'walsize',
                  'db_size': 'dbsize'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        create_mock.assert_any_call('/dev/sdwal', [('wal', 'walsize')])
        create_mock.assert_any_call('/dev/sddb', [('db', 'dbsize')])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_db_size_no_eq(self, mock_log, create_mock, helper_specs):
        """
        Given I defined a wal and a db
        And I do not have a wal_size
        And I have a db_size
        And wal is not equivalent to the device
        Expect to call create('/dev/sdx', [('wal', wal_size)])
        Expect to call log()
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sdwal',
                  'db': '/dev/sddb',
                  'wal_size': None,
                  'db_size': 'dbsize'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_called_with('No size specified for wal /dev/sdwal. Using default sizes.')
        create_mock.assert_any_call('/dev/sddb', [('db', 'dbsize')])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_wal_size_no_eq(self, mock_log, create_mock, helper_specs):
        """
        Given I defined a wal and a db
        And I have a wal_size
        And I do not have a db_size
        And wal is not equivalent to the device
        Expect to call create('/dev/sdx', [('wal', wal_size)])
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sdwal',
                  'db': '/dev/sddb',
                  'wal_size': 'walsize',
                  'db_size': None}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        create_mock.assert_any_call('/dev/sdwal', [('wal', 'walsize')])

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_no_sizes_no_eq(self, mock_log, helper_specs):
        """
        Given I defined a wal and a db
        And I do not have a wal_size
        And I do not have a db_size
        And wal is not equivalent to the device
        Expect to call log()
        Expect to call log()
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sdwal',
                  'db': '/dev/sddb',
                  'wal_size': None,
                  'db_size': None}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_called()

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_wal_and_size(self, mock_log, helper_specs):
        """
        Given I defined only wal
        And I have a wal_size
        And wal is equivalent to the device
        Expect to call log()
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sdx',
                  'db': None,
                  'wal_size': 'walsize',
                  'db_size': None}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_any_call('WAL size is unsupported for same device of /dev/sdx')

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_wal_and_size_no_eq(self, mock_log, create_mock, helper_specs):
        """
        Given I defined only wal
        And I have a wal_size
        And wal is not equivalent to the device
        Expect to call create()
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sdwal',
                  'db': None,
                  'wal_size': 100000,
                  'db_size': None}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        create_mock.assert_called_with('/dev/sdwal', [('wal', 100000)])

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_wal_and_no_size(self, mock_log, helper_specs):
        """
        Given I haven't defined wal and no db
        And I have a wal_size
        Expect to call log()
        """
        kwargs = {'format': 'bluestore',
                  'wal': None,
                  'db': None,
                  'wal_size': 'walsize',
                  'db_size': None}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_called_with('WAL size is unsupported for same device of /dev/sdx')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_db_and_size_eq_log(self, mock_log, helper_specs):
        """
        Given I haven't defined wal but a db
        And I have a db_size
        And wal is the same
        Expect to call log()
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sdx', # temp fix until #340 is merged
                  'db': '/dev/sddb',
                  'wal_size': None,
                  'db_size': 'dbsize'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_called_with('DB size is unsupported for same device of /dev/sdx')

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_db_and_size_no_eq_create(self, mock_log, create_mock, helper_specs):
        """
        Given I have defined a db
        And I have a db_size
        Expect to call create()
        """
        kwargs = {'format': 'bluestore',
                  'wal': None,
                  'db': '/dev/sddb',
                  'wal_size': None,
                  'db_size': 100000}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        create_mock.assert_called_with('/dev/sddb', [('db', 100000)])

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_no_db_log(self, mock_log, helper_specs):
        """
        Given I haven't defined wal or db
        And I have a db_size
        Expect to call log()
        """
        kwargs = {'format': 'bluestore',
                  'wal': None,
                  'db': None,
                  'wal_size': None,
                  'db_size': 'dbsize'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        obj._bluestore_partitions()
        mock_log.warning.assert_called_with("DB size is unsupported for same device of /dev/sdx")

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create(self, ex_mock, pp_mock, lp_mock, helper_specs):
        """
        Given the device is a NVME
        And has a size
        And the RC is 0
        And the os.path.exists is True
        Expect to execute:
        sgdisk
        dd
        _part_probe 1x
        """
        kwargs = {'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)

        lp_mock.return_value = 1
        ex_mock.return_value = True

        obj.create(osd_config.device,[('wal', 1000)])

        lp_mock.assert_called_with(osd_config.device)
        pp_mock.assert_called_with(osd_config.device)
        test_module.__salt__['helper.run'].assert_any_call('/usr/sbin/sgdisk -n 2:0:+1000 -t 2:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/nvme0n1')
        test_module.__salt__['helper.run'].assert_any_call('dd if=/dev/zero of=/dev/nvme0n1p2 bs=4096 count=1 oflag=direct')

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create_1(self, ex_mock, pp_mock, lp_mock, helper_specs):
        """
        Given the device is a NVME
        And has a size
        And the RC is 0
        And the os.path.exists is False
        Expect to execute:
        sgdisk
        _part_probe 1x
        """
        kwargs = {'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)


        lp_mock.return_value = 1
        ex_mock.return_value = False

        obj.create(osd_config.device,[('wal', 1000)])

        lp_mock.assert_called_with(osd_config.device)
        pp_mock.assert_called_with(osd_config.device)
        test_module.__salt__['helper.run'].assert_called_with('/usr/sbin/sgdisk -n 2:0:+1000 -t 2:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/nvme0n1')

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create_2(self, ex_mock, pp_mock, lp_mock, helper_specs):
        """
        Given the device is a NVME
        And has a size
        And the RC is 1
        Expect to execute:
        sgdisk
        """
        kwargs = {'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)

        lp_mock.return_value = 1
        ex_mock.return_value = False

        with pytest.raises(BaseException) as excinfo:
            obj.create(osd_config.device, [('wal', 1000)])
            lp_mock.assert_called_with(osd_config.device)
            assert '/usr/sbin/sgdisk -n 2:0:+1000 -t 2:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/nvme0n1 failed' in str(excinfo.value)

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create_3(self, ex_mock, pp_mock, lp_mock, helper_specs):
        """
        Given the device is not a NVME
        And has a no size
        And the RC is 0
        And the os.path.exists is False
        Expect to execute:
        run 1x
        sgdisk
        _part_probe 1x
        """
        kwargs = {'device': '/dev/sdx'}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)

        lp_mock.return_value = 1
        ex_mock.return_value = False

        obj.create(osd_config.device,[('wal', None)])

        lp_mock.assert_called_with(osd_config.device)
        pp_mock.assert_called_with(osd_config.device)
        test_module.__salt__['helper.run'].assert_called_with('/usr/sbin/sgdisk -N 2 -t 2:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/sdx')

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create_4_last_part(self, ex_mock, pp_mock, lp_mock, helper_specs):
        """
        Given the device is not a NVME
        And has a no size
        And the RC is 0
        And the os.path.exists is False
        Expect to execute:
        run 1x
        sgdisk
        _part_probe 1x
        Partition Param to 4
        """
        kwargs = {}
        osd_config = OSDConfig(**kwargs)
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)

        lp_mock.return_value = 4
        ex_mock.return_value = False
        obj.create(osd_config.device,[('wal', 1000)])

        pp_mock.assert_called
        lp_mock.assert_called_with(osd_config.device)
        test_module.__salt__['helper.run'].assert_any_call('/usr/sbin/sgdisk -n 5:0:+1000 -t 5:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/sdx')

    @mock.patch('srv.salt._modules.osd.glob')
    def test__last_partition(self, glob_mock, helper_specs):
        glob_mock.glob.return_value = ['/dev/sdx1']
        osd_config = OSDConfig()
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        ret = obj._last_partition(osd_config.device)
        glob_mock.glob.assert_called_with('/dev/sdx[0-9]*')
        assert type(ret) is int

    @mock.patch('srv.salt._modules.osd.glob')
    def test__last_partition_digits(self, glob_mock, helper_specs):
        glob_mock.glob.return_value = ['/dev/sdx11']
        osd_config = OSDConfig()
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        ret = obj._last_partition(osd_config.device)
        glob_mock.glob.assert_called_with('/dev/sdx[0-9]*')
        assert ret == 11

    @mock.patch('srv.salt._modules.osd.glob')
    def test__last_partition_no_pathnames(self, glob_mock, helper_specs):
        glob_mock.glob.return_value = []
        osd_config = OSDConfig()
        test_module = helper_specs(module=DEFAULT_MODULE)
        obj = test_module.OSDPartitions(osd_config)
        ret = obj._last_partition(osd_config.device)
        glob_mock.glob.assert_called_with('/dev/sdx[0-9]*')
        assert ret == 0

    @pytest.mark.skip(reason='postponed')
    def test__last_partition_no_pathnames(self):
        """
        Should sorted() and re.sub() be tested aswell?
        """
        pass

class TestOSDCommands():

    @pytest.fixture(scope='class')
    def osdc_o(self):
        # Only return the non-instantiated class to allow
        # custom OSDConfig feeding.
        cnf = osd.OSDCommands
        yield cnf

    def test_osd_partition_1(self, osdc_o):
        """
        Given it's filestore osd+journal, not colocated
        """
        kwargs = {'format': 'filestore',
                  'journal': '/dev/journal'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.osd_partition()
        assert ret == 1

    def test_osd_partition_2(self, osdc_o):
        """
        Given it's filestore osd+journal, colocated
        """
        kwargs = {'format': 'filestore',
                  'journal': '/dev/sdx'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.osd_partition()
        assert ret == 2

    def test_osd_partition_3(self, osdc_o):
        """
        Given it's filestore osd+journal, no journal
        """
        kwargs = {'format': 'filestore'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.osd_partition()
        assert ret == 2

    def test_osd_partition_4(self, osdc_o):
        """
        Given it's bluestore
        """
        kwargs = {'format': 'bluestore'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.osd_partition()
        assert ret == 1

    @mock.patch('srv.salt._modules.osd.OSDCommands.highest_partition')
    def test_osd_partition_5(self, hp_mock, osdc_o):
        """
        Given there is no disk_format
        """
        kwargs = {'format': None}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.osd_partition()
        hp_mock.assert_called_with('/dev/sdx', 'osd')

    def test_is_partition(self, osdc_o, helper_specs):
        helper_specs(osd)
        osd_config = OSDConfig()
        obj = osdc_o(osd_config)
        ret = obj.is_partition('osd', osd_config.device, 1)

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And the device has partitions
        And is_partition() returns True
        And the device is a nvme
        Expect to return p1
        """
        kwargs = {'device': '/dev/nvme1n1'}
        glob_mock.glob.return_value = ['/dev/nvme1n1p1', '/dev/nvme1n1p2']
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd')
        assert ret == 'p2'

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_encrypted(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And it's encrypted
        And the device has partitions & a lockbox
        And is_partition() returns True
        Expect to return 5 (lockboxes are always on 5)
        """
        kwargs = {'device': '/dev/vdb'}
        glob_mock.glob.return_value = ['/dev/vdb1', '/dev/vdb2', '/dev/vdb5']
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'lockbox')
        assert ret == '5'

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_encrypted_nvme(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And it's encrypted
        And the device has partitions & a lockbox
        And is_partition() returns True
        And it's a nvme
        Expect to return 5 (lockboxes are always on 5)
        """
        kwargs = {'device': '/dev/nvme1n1'}
        glob_mock.glob.return_value = ['/dev/nvme1n1p1', '/dev/nvme1n1p2', '/dev/nvme1n1p5']
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'lockbox')
        assert ret == 'p5'

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_no_nvme(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And the device has partitions
        And is_partition() returns True
        And the device is not a nvme
        Expect to return 2
        """
        kwargs = {'device': '/dev/sda'}
        glob_mock.glob.return_value = ['/dev/sda1', '/dev/sda2']
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd')
        assert ret == '2'

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_nvme_partition(self, glob_mock, part_mock, osdc_o):
        """
        Given there is an NVMe device
        And the device has partitions
        And is_partition() returns True
        Expect to return p2
        """
        kwargs = {'device': '/dev/nvme0n1'}
        glob_mock.glob.return_value = ['/dev/nvme0n1p1', '/dev/nvme0n1p2']
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd')
        assert ret == 'p2'

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_no_nvme_partition(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a NVMe device
        And the device has partitions
        And is_partition() returns True
        Expect to return 2
        """
        kwargs = {'device': '/dev/nvme0n1'}
        glob_mock.glob.return_value = ['/dev/nvme0n1p1', '/dev/nvme0n1p2']
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd', nvme_partition=False)
        assert ret == '2'

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_27th(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And the device has partitions
        And is_partition() returns True
        And the device is not a nvme
        And the device is the 27th so will be /dev/sdaa
        Expect to return 2
        """
        kwargs = {'device': '/dev/sdaa'}
        glob_mock.glob.return_value = ['/dev/sdaa1', '/dev/sdaa2']
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd')
        assert ret == '2'

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_27th_twodigit(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And the device has partitions
        And the device has #partitions > 10
        And is_partition() returns True
        And the device is not a nvme
        And the device is the 27th so will be /dev/sdaa
        Expect to return 2
        """
        kwargs = {'device': '/dev/sdaa'}
        glob_mock.glob.return_value = ['/dev/sdaa10', '/dev/sdaa11']
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd')
        assert ret == '11'

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_twodigit(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And the device has partitions
        And the device has #partitions > 10
        And is_partition() returns True
        And the device is not a nvme
        Expect to return 2
        """
        kwargs = {'device': '/dev/sda'}
        glob_mock.glob.return_value = ['/dev/sda10', '/dev/sda11']
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd')
        assert ret == '11'

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_27th_no_partitions(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And the device has partitions
        And is_partition() returns True
        And the device is not a nvme
        And the device is the 27th so will be /dev/sdaa
        Expect to return 2
        """
        kwargs = {'device': '/dev/sdaa'}
        glob_mock.glob.return_value = []
        part_mock.return_value = True
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd')
        assert ret == 0

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    def test_highest_partition_1(self, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And the device has no partitions
        Expect to return 0
        """
        glob_mock.glob.return_value = []
        osd_config = OSDConfig()
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd')
        assert ret == 0

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partition')
    @mock.patch('srv.salt._modules.osd.glob')
    @mock.patch('srv.salt._modules.osd.log')
    def test_highest_partition_2(self, log_mock, glob_mock, part_mock, osdc_o):
        """
        Given there is a device
        And the device has partitions
        And is_partition() returns False
        Expect to return 0
        """
        glob_mock.glob.return_value = ['/dev/sdx1', '/dev/sdx2']
        part_mock.return_value = False
        osd_config = OSDConfig()
        obj = osdc_o(osd_config)
        ret = obj.highest_partition(osd_config.device, 'osd')
        assert ret == 0
        log_mock.error.assert_called_with("Partition type osd not found on /dev/sdx")

    @pytest.mark.skip(reason="Postponed to later")
    def test__cluster_name(self):
        pass

    @pytest.mark.skip(reason="Postponed to later")
    def test__fsid(self):
        pass

    @mock.patch('srv.salt._modules.osd.glob')
    def test_is_partitioned(self, glob_mock, osdc_o):
        glob_mock.glob.return_value = ['/dev/sdx1', '/dev/sdx2']
        osd_config = OSDConfig()
        obj = osdc_o(osd_config)
        ret = obj.is_partitioned(osd_config.device)
        glob_mock.glob.assert_called_with('/dev/sdx[0-9]*')
        assert ret is True

    @mock.patch('srv.salt._modules.osd.glob')
    def test_is_partitioned_false(self, glob_mock, osdc_o):
        glob_mock.glob.return_value = []
        osd_config = OSDConfig()
        obj = osdc_o(osd_config)
        ret = obj.is_partitioned(osd_config.device)
        glob_mock.glob.assert_called_with('/dev/sdx[0-9]*')
        assert ret is False

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    @mock.patch('srv.salt._modules.osd.OSDCommands.highest_partition')
    def test_filestore_args(self, hp_mock, ip_mock, osdc_o):
        """
        Given the disk is partitioned ('/dev/sdx{1,2}')
        And there is a journal ('/dev/journal', with 2 partitions 1&2)
        Expect to return:
        "/dev/sdx2, /dev/journal2
        """
        kwargs = {'journal': '/dev/journal'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.return_value = True
        hp_mock.side_effect = [2,2]
        ret = obj._filestore_args()
        assert ret == "/dev/sdx2 /dev/journal2"

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    @mock.patch('srv.salt._modules.osd.OSDCommands.highest_partition')
    def test_filestore_args_1(self, hp_mock, ip_mock, osdc_o):
        """
        Given the disk is partitioned ('/dev/sdx{1,2}')
        And there is no journal
        Expect to return:
        "/dev/sdx2, /dev/sdx3
        """
        kwargs = {'journal': None}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.return_value = True
        hp_mock.side_effect = [2,3]
        ret = obj._filestore_args()
        assert ret == "/dev/sdx2 /dev/sdx3"

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_filestore_args_2(self, ip_mock, osdc_o):
        """
        Given the disk not is partitioned ('/dev/sdx')
        And there is a journal
        Expect to return:
        "/dev/sdx, /dev/journal
        """
        kwargs = {'journal': '/dev/journal'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.return_value = False
        ret = obj._filestore_args()
        assert ret == "/dev/sdx /dev/journal"

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_filestore_args_3(self, ip_mock, osdc_o):
        """
        Given the disk not is partitioned ('/dev/sdx')
        And there is no journal
        Expect to return:
        "/dev/sdx
        """
        kwargs = {'journal': None}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.return_value = False
        ret = obj._filestore_args()
        assert ret == "/dev/sdx"

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args(self, ip_mock, osdc_o):
        """
        Given there is a wal and db defined
        And there is no wal_size or db_size defined
        Encryption is not set.

        And the device is partitioned
        And and the device is a NVME
        Expect args to be:

        --block.wal /dev/sdwal --block.db /dev/sddb /dev/nvme0n1p1

        """
        kwargs = {'wal': '/dev/sdwal',
                  'db': '/dev/sddb',
                  'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        ret = obj._bluestore_args()
        assert ret == "--block.wal /dev/sdwal --block.db /dev/sddb /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.highest_partition')
    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args_1(self, ip_mock, hp_mock, osdc_o):
        """
        Given there is a wal and db defined
        And there IS wal_size and db_size defined
        And there are partitions (1,1)
        Encryption is not set.

        And the device is partitioned
        And and the device is a NVME
        Expect args to be:

        --block.wal /dev/sdwal1 --block.db /dev/sddb1 /dev/nvme0n1p1

        """
        kwargs = {'wal': '/dev/sdwal',
                  'wal_size': '2G',
                  'db': '/dev/sddb',
                  'db_size': '1G',
                  'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        hp_mock.side_effect = [1, 1]
        ret = obj._bluestore_args()
        assert ret == "--block.wal /dev/sdwal1 --block.db /dev/sddb1 /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.highest_partition')
    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args_2(self, ip_mock, hp_mock, osdc_o):
        """
        Given there is NO wal but a db defined
        And there IS NO wal_size but a db_size defined
        And there are partitions (1)
        Encryption is not set.

        And the device is partitioned
        And and the device is a NVME
        Expect args to be:

        --block.db /dev/sddb1 /dev/nvme0n1p1

        """
        kwargs = {'db': '/dev/sddb',
                  'db_size': '1G',
                  'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        hp_mock.side_effect = [1]
        ret = obj._bluestore_args()
        assert ret == "--block.db /dev/sddb1 /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.highest_partition')
    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args_2_1(self, ip_mock, hp_mock, osdc_o):
        """
        Given there is NO wal but a db defined
        And there is wal_size and a db_size defined
        And there are partitions (1)
        Encryption is not set.

        And the device is partitioned
        And and the device is a NVME
        Expect args to be:

        --block.db /dev/sddb1 /dev/nvme0n1p1

        """
        kwargs = {'db': '/dev/sddb',
                  'db_size': '1G',
                  'wal_size': '2G',
                  'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        hp_mock.side_effect = [1]
        ret = obj._bluestore_args()
        assert ret == "--block.db /dev/sddb1 /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args_3(self, ip_mock, osdc_o):
        """
        Given there is only a wal definded
        And there is no wal_size or db_size defined

        And the device is partitioned
        And and the device is a NVME
        Expect args to be:

        --block.wal /dev/sdwal /dev/nvme0n1p1

        """
        kwargs = {'wal': '/dev/sdwal',
                  'db': None,
                  'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        ret = obj._bluestore_args()
        assert ret == "--block.wal /dev/sdwal /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.highest_partition')
    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args_4(self, ip_mock, hp_mock, osdc_o):
        """
        Given there is NO db but a wal defined
        And there IS NO db_size but a wal_size defined
        And there are partitions (1)
        Encryption is not set.

        And the device is partitioned
        And and the device is a NVME
        Expect args to be:

        --block.db /dev/sdwal1 /dev/nvme0n1p1

        """
        kwargs = {'wal': '/dev/sdwal',
                  'wal_size': '1G',
                  'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        hp_mock.side_effect = [1]
        ret = obj._bluestore_args()
        assert ret == "--block.wal /dev/sdwal1 /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.highest_partition')
    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args_5(self, ip_mock, hp_mock, osdc_o):
        """
        Given there is a db and a wal defined
        And there is db_size and wal_size defined
        Encryption is set.

        And the device is partitioned
        And and the device is a NVME
        Expect args to be:

        --block.db /dev/sddb --block.wal /dev/sdwal /dev/nvme0n1p1

        """
        kwargs = {'wal': '/dev/sdwal',
                  'wal_size': '1G',
                  'db_size': '1G',
                  'db': '/dev/sddb',
                  'encryption': 'dmcrypt',
                  'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        hp_mock.side_effect = [1]
        ret = obj._bluestore_args()
        assert ret == "--block.db /dev/sddb --block.wal /dev/sdwal /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args_6(self, ip_mock, osdc_o):
        """
        Given there is only a db definded
        And there is no wal_size or db_size defined
        And Encryption is set

        And the device is partitioned
        And and the device is a NVME
        Expect args to be:

        --block.db /dev/sddb /dev/nvme0n1p1

        """
        kwargs = {'wal': None,
                  'db': '/dev/sddb',
                  'encryption': 'dmcrypt',
                  'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        ret = obj._bluestore_args()
        assert ret == "--block.db /dev/sddb /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args_7(self, ip_mock, osdc_o):
        """
        Given there is only a wal definded
        And there is no wal_size or db_size defined
        And Encryption is set

        And the device is partitioned
        And and the device is a NVME
        Expect args to be:

        --block.db /dev/sddb /dev/nvme0n1p1

        """
        kwargs = {'wal': '/dev/sdwal',
                  'db': None,
                  'encryption': 'dmcrypt',
                  'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        ret = obj._bluestore_args()
        assert ret == "--block.wal /dev/sdwal /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.is_partitioned')
    def test_bluestore_args_8(self, ip_mock, osdc_o):
        """
        Given there is only a wal definded
        And there is wal_size defined
        And Encryption is set

        And the device is partitioned
        And and the device is a standard disk
        Expect args to be:
        --block.wal /dev/sdwal --block.db /dev/sddb /dev/sdx

        """
        kwargs = {'wal': '/dev/sdwal',
                  'db': '/dev/sddb',
                  'encryption': 'dmcrypt',
                  'device': '/dev/sdx'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ip_mock.side_effect = [True]
        ret = obj._bluestore_args()
        assert ret == "--block.db /dev/sddb --block.wal /dev/sdwal /dev/sdx1"

    def test_bluestore_args_9(self, osdc_o):
        """
        Given there is a not wal and no db defined
        And Encryption is set

        And the device is not partitioned
        And and the device is not a NVME
        Expect args to be:

        /dev/sdx

        """
        kwargs = {'encryption': 'dmcrypt',
                  'device': '/dev/sdx'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj._bluestore_args()
        assert ret == "/dev/sdx"

    def test_bluestore_args_10(self, osdc_o):
        """
        Given there is a not wal and no db defined
        And Encryption is not set

        And the device is not partitioned
        And and the device is not a NVME
        Expect args to be:

        /dev/sdx

        """
        kwargs = {'encryption': None,
                  'device': '/dev/sdx'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj._bluestore_args()
        assert ret == "/dev/sdx"

    @mock.patch('srv.salt._modules.osd.OSDCommands._fsid')
    @mock.patch('srv.salt._modules.osd.OSDCommands._cluster_name')
    @mock.patch('srv.salt._modules.osd.OSDCommands._filestore_args')
    def test_prepare(self, fs_mock, cn_mock, fsid_mock, osdc_o):
        """
        Given there is a device defined
        And it's encrypted
        And it's filestore
        And args are populated
        Expect --fs-type xfs and --dmcrypt to be part of cmd
        """
        kwargs = {'encryption': 'dmcrypt',
                  'format': 'filestore'}
        fs_mock.return_value = 'filestore_args'
        cn_mock.return_value = 'ceph'
        fsid_mock.return_value = '0000-0000-0000-0000-0000'
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.prepare()
        assert "--fs-type xfs" in ret
        assert "--dmcrypt" in ret

    @mock.patch('srv.salt._modules.osd.OSDCommands._fsid')
    @mock.patch('srv.salt._modules.osd.OSDCommands._cluster_name')
    @mock.patch('srv.salt._modules.osd.OSDCommands._filestore_args')
    def test_prepare_reuse_id(self, fs_mock, cn_mock, fsid_mock, osdc_o):
        """
        Given there is a device defined
        And it's filestore
        And args are populated
        Expect --osd-id to be part of cmd
        """
        kwargs = {'format': 'filestore'}
        fs_mock.return_value = 'filestore_args'
        cn_mock.return_value = 'ceph'
        fsid_mock.return_value = '0000-0000-0000-0000-0000'
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.prepare(osd_id=1)
        assert "--osd-id" in ret

    @mock.patch('srv.salt._modules.osd.OSDCommands._fsid')
    @mock.patch('srv.salt._modules.osd.OSDCommands._cluster_name')
    @mock.patch('srv.salt._modules.osd.OSDCommands._filestore_args')
    def test_prepare_1(self, fs_mock, cn_mock, fsid_mock, osdc_o):
        """
        Given there is a device defined
        And it's not encrypted
        And it's filestore
        And args are populated
        Expect dmrypt not to be part of cmd
        """
        kwargs = {'encryption': 'noencryption',
                  'format': 'filestore'}
        fs_mock.return_value = 'filestore_args'
        cn_mock.return_value = 'ceph'
        fsid_mock.return_value = '0000-0000-0000-0000-0000'
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.prepare()
        assert "--fs-type xfs" in ret
        assert "--dmcrypt" not in ret

    @mock.patch('srv.salt._modules.osd.OSDCommands._fsid')
    @mock.patch('srv.salt._modules.osd.OSDCommands._cluster_name')
    @mock.patch('srv.salt._modules.osd.OSDCommands._bluestore_args')
    def test_prepare_2(self, bs_mock, cn_mock, fsid_mock, osdc_o):
        """
        Given there is a device defined
        And it's encrypted
        And it's bluestore
        And args are populated
        Expect dmrypt to be part of cmd
        """
        kwargs = {'encryption': 'dmcrypt',
                  'format': 'bluestore'}
        bs_mock.return_value = 'bluestore_args'
        cn_mock.return_value = 'ceph'
        fsid_mock.return_value = '0000-0000-0000-0000-0000'
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.prepare()
        assert "--bluestore" in ret
        assert "--dmcrypt" in ret

    @mock.patch('srv.salt._modules.osd.OSDCommands._fsid')
    @mock.patch('srv.salt._modules.osd.OSDCommands._cluster_name')
    @mock.patch('srv.salt._modules.osd.OSDCommands._bluestore_args')
    def test_prepare_3(self, bs_mock, cn_mock, fsid_mock, osdc_o):
        """
        Given there is a device defined
        And it's not encrypted
        And it's bluestore
        And args are populated
        Expect dmrypt to be part of cmd
        """
        kwargs = {'encryption': 'nodmcrypt',
                  'format': 'bluestore'}
        bs_mock.return_value = 'bluestore_args'
        cn_mock.return_value = 'ceph'
        fsid_mock.return_value = '0000-0000-0000-0000-0000'
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.prepare()
        assert "--bluestore" in ret
        assert "--dmcrypt" not in ret

    @mock.patch('srv.salt._modules.osd.OSDCommands._fsid')
    @mock.patch('srv.salt._modules.osd.OSDCommands._cluster_name')
    @mock.patch('srv.salt._modules.osd.OSDCommands._bluestore_args')
    @mock.patch('srv.salt._modules.osd.log')
    def test_prepare_4(self, log_mock, bs_mock, cn_mock, fsid_mock, osdc_o):
        """
        Given there is a device defined
        And it's not encrypted
        And it's bluestore
        And args are NOT populated <-
        Expect log.error to be invoked
        """
        kwargs = {'encryption': 'nodmcrypt',
                  'format': 'bluestore'}
        bs_mock.return_value = ''
        cn_mock.return_value = 'ceph'
        fsid_mock.return_value = '0000-0000-0000-0000-0000'
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.prepare()
        log_mock.error.assert_called_once
        assert "--bluestore" in ret
        assert "--dmcrypt" not in ret

    @mock.patch('srv.salt._modules.osd.log')
    def test_prepare_5(self, log_mock, osdc_o):
        """
        Given there is a no device defined
        Expect log.info to be invoked
        And cmd = ""
        """
        kwargs = {'device': None}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.prepare()
        log_mock.info.assert_called_with("prepare: ")
        assert ret == ""

    def test_activate_0(self, osdc_o):
        """
        Given there is a device defined
        And encryption is enabled
        Expect cmd to be:

        /bin/true activated during prepare
        """
        kwargs = {'encryption': 'dmcrypt'}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.activate()
        assert ret == "/bin/true activated during prepare"

    @mock.patch('srv.salt._modules.osd.OSDCommands.osd_partition')
    def test_activate_1(self, osdp_mock, osdc_o):
        """
        Given there is a device defined
        And encryption is disabled
        And the device is a nvme
        Expect cmd to be:

        ceph-disk -v activate --mark-init systemd --mount /dev/nvme0n1p<osd_partition>
        """
        kwargs = {'device': '/dev/nvme0n1'}
        osdp_mock.return_value = 1
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.activate()
        assert ret == "PYTHONWARNINGS=ignore ceph-disk -v activate --mark-init systemd --mount /dev/nvme0n1p1"

    @mock.patch('srv.salt._modules.osd.OSDCommands.osd_partition')
    def test_activate_2(self, osdp_mock, osdc_o):
        """
        Given there is a device defined
        And encryption is disabled
        And the device is not a nvme
        Expect cmd to be:

        ceph-disk -v activate --mark-init systemd --mount /dev/sdx<osd_partition>
        """
        kwargs = {'device': '/dev/sdx'}
        osdp_mock.return_value = 1
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.activate()
        assert ret == "PYTHONWARNINGS=ignore ceph-disk -v activate --mark-init systemd --mount /dev/sdx1"

    def test_activate_3(self, osdc_o):
        """
        Given there is not device defined
        Expect cmd to be:
        ""
        """
        kwargs = {'device': None}
        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)
        ret = obj.activate()
        assert ret == ""

    @pytest.mark.skip(reason="Low priority, postponed")
    def test_detect(self):
        pass

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
        mock_weight.reweight.return_value = (0, "out", "err")
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
        mock_weight.reweight.return_value = (1, "out", "err")
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


class Test_is_incorrect():
    '''
    Create the six possible OSDs in a FakeFilesystem.  Overwrite the
    /proc/mounts file in each test to use one of the six OSDs.

    these tests are focused on is_incorrect.
    '''

    fs = fake_fs.FakeFilesystem()
    proc_mount = fs.CreateFile('/proc/mounts')

    fs.CreateFile('/var/lib/ceph/osd/ceph-1/type',
                  contents='''bluestore\n''')

    fs.CreateFile('/var/lib/ceph/osd/ceph-2/type',
                  contents='''bluestore\n''')
    fs.CreateFile('/var/lib/ceph/osd/ceph-2/block.wal')

    fs.CreateFile('/var/lib/ceph/osd/ceph-3/type',
                  contents='''bluestore\n''')
    fs.CreateFile('/var/lib/ceph/osd/ceph-3/block.db')

    fs.CreateFile('/var/lib/ceph/osd/ceph-4/type',
                  contents='''bluestore\n''')
    fs.CreateFile('/var/lib/ceph/osd/ceph-4/block.wal')
    fs.CreateFile('/var/lib/ceph/osd/ceph-4/block.db')

    fs.CreateFile('/var/lib/ceph/osd/ceph-5/type',
                  contents='''filestore\n''')

    fs.CreateFile('/var/lib/ceph/osd/ceph-6/type',
                  contents='''filestore\n''')
    fs.CreateFile('/var/lib/ceph/osd/ceph-6/journal')

    f_glob = fake_glob.FakeGlobModule(fs)
    f_os = fake_fs.FakeOsModule(fs)
    f_open = fake_fs.FakeFileOpen(fs)

    @pytest.fixture(scope='class')
    def osdc_o(self):
        # Only return the non-instantiated class to allow
        # custom OSDConfig feeding.
        yield osd

    @patch('os.path.exists', new=f_os.path.exists)
    def test_is_incorrect_bluestore(self, osdc_o):
        """
        Check independent bluestore OSD
        """

        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)


        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-1 rest\n''')
        ret = obj.is_incorrect()
        assert ret is False

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    def test_is_incorrect_bluestore_mismatch_format(self, osdc_o):
        """
        Check independent bluestore OSD with filestore format
        """
        kwargs = { 'device': '/dev/sdb',
                   'format': 'filestore' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-1 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    def test_is_incorrect_bluestore_no_wal_config(self, osdc_o):
        """
        Check bluestore OSD with existing wal, but no wal config
        """
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-2 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    def test_is_incorrect_bluestore_no_db_config(self, osdc_o):
        """
        Check bluestore OSD with existing db, but no db config
        """
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-3 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_bluestore_wal(self, readlink, osdc_o):
        """
        Check bluestore OSD with a wal
        """
        readlink.return_value = "/dev/sdc"
        #run.return_value = ( 0, '104857600', '')
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore',
                   'wal': '/dev/sdc',
                   'wal_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-2 rest\n''')
        ret = obj.is_incorrect()
        assert ret == False

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_bluestore_wal_no_device(self, readlink, osdc_o):
        """
        Check bluestore OSD with a configured wal, but no separate wal device
        """
        readlink.return_value = ""
        #run.return_value = ( 0, '104857600', '')
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore',
                   'wal': '/dev/sdc',
                   'wal_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-1 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_bluestore_wal_wrong_device(self, readlink, osdc_o):
        """
        Check bluestore OSD with a wal, but wal is a different device
        """
        readlink.return_value = "/dev/sdx"
        #run.return_value = ( 0, '104857600', '')
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore',
                   'wal': '/dev/sdc',
                   'wal_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-2 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_bluestore_wal_wrong_size(self, readlink, osdc_o):
        """
        Check bluestore OSD with a wal, but wal is the wrong size
        """
        readlink.return_value = "/dev/sdc"
        #run.return_value = ( 0, '104857600', '')
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore',
                   'wal': '/dev/sdc',
                   'wal_size': '200M' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-2 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_bluestore_db(self, readlink, osdc_o):
        """
        Check bluestore OSD with a db
        """
        readlink.return_value = "/dev/sdc"
        #run.return_value = ( 0, '104857600', '')
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore',
                   'db': '/dev/sdc',
                   'db_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-3 rest\n''')
        ret = obj.is_incorrect()
        assert ret == False

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_bluestore_db_no_device(self, readlink, osdc_o):
        """
        Check bluestore OSD with a configured db, but no db device
        """
        readlink.return_value = ""
        #run.return_value = ( 0, '104857600', '')
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore',
                   'db': '/dev/sdc',
                   'db_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-1 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_bluestore_db_wrong_device(self, readlink, osdc_o):
        """
        Check bluestore OSD with a db, but with a different db device
        """
        readlink.return_value = "/dev/sdx"
        #run.return_value = ( 0, '104857600', '')
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore',
                   'db': '/dev/sdc',
                   'db_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-3 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_bluestore_db_wrong_size(self, readlink, osdc_o):
        """
        Check bluestore OSD with a db, but with wrong size
        """
        readlink.return_value = "/dev/sdc"
        #run.return_value = ( 0, '104857600', '')
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore',
                   'db': '/dev/sdc',
                   'db_size': '200M' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-3 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @pytest.mark.skip(reason="disabled until found out why pyfakefs is failing")
    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_bluestore_wal_db(self, readlink, osdc_o):
        """
        Check bluestore OSD with a wal and db
        """
        readlink.return_value = "/dev/sdc"
        #run.return_value = ( 0, '104857600', '')
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore',
                   'db': '/dev/sdc',
                   'db_size': '100M',
                   'wal': '/dev/sdc',
                   'wal_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-4 rest\n''')
        ret = obj.is_incorrect()
        assert ret == False

    @patch('os.path.exists', new=f_os.path.exists)
    def test_is_incorrect_filestore(self, osdc_o):
        """
        Check independent filestore OSD
        """
        kwargs = { 'device': '/dev/sdb'}

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-5 rest\n''')
        ret = obj.is_incorrect()
        assert ret == False

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    def test_is_incorrect_filestore_mismatch_format(self, osdc_o):
        """
        Check independent filestore OSD with bluestore format
        """
        kwargs = { 'device': '/dev/sdb',
                   'format': 'bluestore' }

        osd_config = OSDConfig(**kwargs)
        osdc_o = osd.OSDCommands
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-5 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_filestore_journal(self, readlink, osdc_o, helper_specs):
        """
        Check filestore OSD with a journal
        """
        readlink.return_value = "/dev/sdc"
        osd = helper_specs(osdc_o, ret_val=(0,'104857600', ''))
        osdc_o = osd.OSDCommands
        kwargs = { 'device': '/dev/sdb',
                   'journal': '/dev/sdc',
                   'journal_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-6 rest\n''')
        ret = obj.is_incorrect()
        assert ret == False

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_filestore_journal_no_device(self, readlink, osdc_o, helper_specs):
        """
        Check filestore OSD with a journal
        """
        readlink.return_value = ""
        osd = helper_specs(osdc_o, ret_val=(0,'104857600', ''))
        osdc_o = osd.OSDCommands
        kwargs = { 'device': '/dev/sdb',
                   'journal': '/dev/sdc',
                   'journal_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-5 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_filestore_journal_wrong_device(self, readlink, osdc_o, helper_specs):
        """
        Check filestore OSD with a journal
        """
        readlink.return_value = "/dev/sdx"
        osd = helper_specs(module=osdc_o, ret_val=(0,'104857600', ''))
        osdc_o = osd.OSDCommands
        kwargs = { 'device': '/dev/sdb',
                   'journal': '/dev/sdc',
                   'journal_size': '100M' }

        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-6 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    @patch('srv.salt._modules.osd.readlink')
    def test_is_incorrect_filestore_journal_wrong_size(self, readlink, osdc_o, helper_specs):
        """
        Check filestore OSD with a journal, but with wrong size
        """
        helper_specs(module=osdc_o, ret_val=(0,'104857600', ''))
        osdc_o = osd.OSDCommands
        readlink.return_value = "/dev/sdc"
        kwargs = { 'device': '/dev/sdb',
                   'journal': '/dev/sdc',
                   'journal_size': '200M' }

        osd_config = OSDConfig(**kwargs)
        obj = osdc_o(osd_config)

        Test_is_incorrect.proc_mount.SetContents(
            '''/dev/sdb /var/lib/ceph/osd/ceph-6 rest\n''')
        ret = obj.is_incorrect()
        assert ret == True

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

class Test_report():

    fs = fake_fs.FakeFilesystem()
    f_os = fake_fs.FakeOsModule(fs)

    @patch('srv.salt._modules.osd._report_grains')
    @patch('srv.salt._modules.osd._report_pillar')
    @patch('srv.salt._modules.osd._report_original_pillar')
    def test_report(self, mock_rop, mock_rp, mock_rg):
        mock_rg.return_value = ([], [])
        mock_rp.return_value = ([], [])
        mock_rop.return_value = ([], [])

        result = osd.report()
        assert result == "All configured OSDs are active"

    @patch('srv.salt._modules.osd._report_grains')
    @patch('srv.salt._modules.osd._report_pillar')
    @patch('srv.salt._modules.osd._report_original_pillar')
    def test_report_not_human(self, mock_rop, mock_rp, mock_rg):
        mock_rg.return_value = ([], [])
        mock_rp.return_value = ([], [])
        mock_rop.return_value = ([], [])

        result = osd.report(human=False)
        assert 'unconfigured' in result
        assert 'changed' in result
        assert 'unmounted' in result


    @patch('srv.salt._modules.osd._report_grains')
    @patch('srv.salt._modules.osd._report_pillar')
    @patch('srv.salt._modules.osd._report_original_pillar')
    def test_report_unmounted(self, mock_rop, mock_rp, mock_rg):
        mock_rg.return_value = ([], ['/dev/sda'])
        mock_rp.return_value = ([], [])
        mock_rop.return_value = ([], [])

        result = osd.report()
        assert "No OSD mounted for" in result

    @patch('srv.salt._modules.osd._report_grains')
    @patch('srv.salt._modules.osd._report_pillar')
    @patch('srv.salt._modules.osd._report_original_pillar')
    def test_report_unconfigured(self, mock_rop, mock_rp, mock_rg):
        mock_rg.return_value = ([], [])
        mock_rp.return_value = (['/dev/sda'], [])
        mock_rop.return_value = ([], [])

        result = osd.report()
        assert "No OSD configured for" in result

    @patch('srv.salt._modules.osd._report_grains')
    @patch('srv.salt._modules.osd._report_pillar')
    @patch('srv.salt._modules.osd._report_original_pillar')
    def test_report_unconfigured_original(self, mock_rop, mock_rp, mock_rg):
        mock_rg.return_value = ([], [])
        mock_rp.return_value = ([], [])
        mock_rop.return_value = (['/dev/sda'], [])

        result = osd.report()
        assert "No OSD configured for" in result

    @patch('srv.salt._modules.osd._report_grains')
    @patch('srv.salt._modules.osd._report_pillar')
    @patch('srv.salt._modules.osd._report_original_pillar')
    def test_report_changed(self, mock_rop, mock_rp, mock_rg):
        mock_rg.return_value = ([], [])
        mock_rp.return_value = ([], ['/dev/sda'])
        mock_rop.return_value = ([], [])

        result = osd.report()
        assert "Different configuration for" in result

    @patch('srv.salt._modules.osd._report_grains')
    @patch('srv.salt._modules.osd._report_pillar')
    @patch('srv.salt._modules.osd._report_original_pillar')
    def test_report_changed_original(self, mock_rop, mock_rp, mock_rg):
        mock_rg.return_value = ([], [])
        mock_rp.return_value = ([], [])
        mock_rop.return_value = ([], ['/dev/sda'])

        result = osd.report()
        assert "Different configuration for" in result

    @patch('srv.salt._modules.osd.split_partition')
    @mock.patch('srv.salt._modules.osd.readlink')
    def test_report_grains_unmounted(self, mock_rl, mock_sp):
        osd.__grains__ = {'ceph': {'1': {'partitions': {'osd': '/dev/sda1'}}}}
        osd.__pillar__ = {}

        mock_rl.return_value = "/dev/sda1"
        mock_sp.return_value = ("/dev/sda", "1")
        active, unmounted = osd._report_grains()
        assert unmounted == ["/dev/sda"]
        assert active == ["/dev/sda"]

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.salt._modules.osd.split_partition')
    @mock.patch('srv.salt._modules.osd.readlink')
    def test_report_grains_mounted(self, mock_rl, mock_sp):
        osd.__grains__ = {'ceph': {'1': {'partitions': {'osd': '/dev/sda1'}}}}
        osd.__pillar__ = {}

        filename = "/var/lib/ceph/osd/ceph-1/fsid"
        Test_report.fs.CreateFile(filename)
        mock_rl.return_value = "/dev/sda1"
        mock_sp.return_value = ("/dev/sda", "1")
        active, unmounted = osd._report_grains()
        Test_report.fs.RemoveFile(filename)
        assert unmounted == []
        assert active == ["/dev/sda"]

    # Add lockbox checks

    @patch('srv.salt._modules.osd.is_incorrect')
    @mock.patch('srv.salt._modules.osd.readlink')
    def test_report_pillar_unconfigured(self, mock_rl, mock_ii):
        osd.__pillar__ = {'ceph': {'storage': {'osds': {'/dev/sda': {}}}}}

        mock_rl.return_value = "/dev/sda"
        mock_ii.return_value = False
        unconfigured, changed = osd._report_pillar(["/dev/sdb"])
        assert unconfigured == ["/dev/sda"]
        assert changed == []

    @patch('srv.salt._modules.osd.is_incorrect')
    @mock.patch('srv.salt._modules.osd.readlink')
    def test_report_pillar_configured_and_unchanged(self, mock_rl, mock_ii):
        osd.__pillar__ = {'ceph': {'storage': {'osds': {'/dev/sda': {}}}}}

        mock_rl.return_value = "/dev/sda"
        mock_ii.return_value = False
        unconfigured, changed = osd._report_pillar(["/dev/sda"])
        assert unconfigured == []
        assert changed == []

    @patch('srv.salt._modules.osd.is_incorrect')
    @mock.patch('srv.salt._modules.osd.readlink')
    def test_report_pillar_changed(self, mock_rl, mock_ii):
        osd.__pillar__ = {'ceph': {'storage': {'osds': {'/dev/sda': {}}}}}

        mock_rl.return_value = "/dev/sda"
        mock_ii.return_value = True
        unconfigured, changed = osd._report_pillar(["/dev/sda"])
        assert unconfigured == []
        assert changed == ["/dev/sda"]

    @patch('srv.salt._modules.osd.is_incorrect')
    @mock.patch('srv.salt._modules.osd.readlink')
    def test_report_original_pillar_unconfigured(self, mock_rl, mock_ii):
        osd.__pillar__ = {'storage': {'osds': ['/dev/sda'],
                                      'data+journals': {}}}

        mock_rl.return_value = "/dev/sda"
        mock_ii.return_value = False
        unconfigured, changed = osd._report_original_pillar(["/dev/sdb"])
        assert unconfigured == ["/dev/sda"]
        assert changed == []

    @patch('srv.salt._modules.osd.is_incorrect')
    @mock.patch('srv.salt._modules.osd.readlink')
    def test_report_original_pillar_configured_and_unchanged(self, mock_rl, mock_ii):
        osd.__pillar__ = {'storage': {'osds': ['/dev/sda'],
                                      'data+journals': {}}}

        mock_rl.return_value = "/dev/sda"
        mock_ii.return_value = False
        unconfigured, changed = osd._report_original_pillar(["/dev/sda"])
        assert unconfigured == []
        assert changed == []

    @patch('srv.salt._modules.osd.is_incorrect')
    @mock.patch('srv.salt._modules.osd.readlink')
    def test_report_original_pillar_changed(self, mock_rl, mock_ii):
        osd.__pillar__ = {'storage': {'osds': ['/dev/sda'],
                                      'data+journals': {}}}

        mock_rl.return_value = "/dev/sda"
        mock_ii.return_value = True
        unconfigured, changed = osd._report_original_pillar(["/dev/sda"])
        assert unconfigured == []
        assert changed == ["/dev/sda"]

