from pyfakefs import fake_filesystem as fake_fs
from pyfakefs import fake_filesystem_glob as fake_glob
import pytest
from srv.salt._modules import osd
from mock import MagicMock, patch, mock

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

@pytest.mark.skip(reason="Low priority: skipped")
class TestOSDWeight():
    pass


class TestOSDConfig():

    # How to properly reset the salt_internals after it was altered..
    # fixtures allow you to teardown the fixture..
    # can you yield multiple things?
    @pytest.fixture(scope='class')
    def salt_internals(self):
        osd.__pillar__ = {}
        osd.__salt__ = {'mine.get': 'asd'}
        osd.__grains__ = {'id': 1}

    @pytest.fixture(scope='class')
    def osd_o(self):
        with patch.object(osd.OSDConfig, '__init__', lambda self: None):
            print "Constructing the OSDConfig object"
            cnf = osd.OSDConfig()
            cnf.device = '/dev/sdx'
            # monkeypatching the device in the object since __init__
            # is mocked -> skipping the readlink()
            yield cnf
            # everything after the yield is a teardown code
            print "Teardown OSDConfig object"

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

    @pytest.fixture(scope='class')
    def osdp_o(self):
        # Only return the non-instantiated class to allow
        # custom OSDConfig feeding.
        cnf = osd.OSDPartitions
        yield cnf

    @mock.patch('srv.salt._modules.osd.OSDPartitions._xfs_partitions')
    def test_partition_filestore(self, xfs_part_mock, osdp_o):
        kwargs = {'format': 'filestore'}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)
        obj.partition()
        xfs_part_mock.assert_called_with(obj.osd.device, obj.osd.size)

    @mock.patch('srv.salt._modules.osd.OSDPartitions._bluestore_partitions')
    def test_partition_bluestore(self, blue_part_mock, osdp_o):
        kwargs = {'format': 'bluestore'}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)
        obj.partition()
        blue_part_mock.assert_called_with(obj.osd.device)

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_colocated(self, create_mock, osdp_o):
        """
        Given I have a journal
        And I have set the journal_size
        And the journal equals the device
        Expect a create() invocation with params:
            `journal, list(set(journal_size, journal_size), set(osd, None))`
        """
        kwargs = {'format': 'filestore', 'journal': '/dev/sdx', 'journal_size': 1000000}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_called_with(obj.osd.journal, [('journal', obj.osd.journal_size), ('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_not_colocated(self, create_mock, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_any_call(obj.osd.journal, [('journal', obj.osd.journal_size)])
        create_mock.assert_any_call(obj.osd.device, [('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_colocated_no_journal_size(self, create_mock, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_called_with(obj.osd.device, [('journal', obj.osd.journal_size), ('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_not_colocated_no_journal_size(self, create_mock, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_any_call(obj.osd.journal, [('journal', obj.osd.journal_size)])
        create_mock.assert_any_call(obj.osd.device, [('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_no_journal(self, create_mock, osdp_o):
        """
        Given I don't have a journal
        And I have set the journal_size
        Expect a create() invocation with params:
            `device, list(set(journal_size, journal_size), set(osd, None))`
        """
        kwargs = {'format': 'filestore'}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_called_with(obj.osd.device, [('journal', obj.osd.journal_size), ('osd', None)])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_xfs_partitions_no_journal_small(self, create_mock, osdp_o):
        """
        Given I don't have a journal
        And I have set the journal_size
        And small is set
        Expect a create() invocation with params:
            `device, list(set(journal_size, journal_size), set(osd, None))`
        """
        kwargs = {'format': 'filestore'}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)
        obj._xfs_partitions(obj.osd.device, obj.osd.size)
        create_mock.assert_called_with(obj.osd.device, [('journal', obj.osd.journal_size), ('osd', None)])

    @pytest.mark.skip(reason='low priority: skip for now')
    def test_double(self):
        pass

    @pytest.mark.skip(reason='low priority: skip for now')
    def test_halve(self):
        pass

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_log(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_called_with('No size specified for db /dev/sdx. Using default sizes')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_log_db_size(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_any_call('WAL size is unsupported for same device of /dev/sdx')
        mock_log.warn.assert_any_call('DB size is unsupported for same device of /dev/sdx')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_encrypted_log(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_any_call('You deploy encrypted WAL and/or DB on a dedicated device. Specifying sizes is now handled via your ceph.conf')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_encrypted_log(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_any_call('You deploy encrypted WAL and/or DB on a dedicated device. Specifying sizes is now handled via your ceph.conf')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_db_encrypted_log(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_any_call('You deploy encrypted WAL and/or DB on a dedicated device. Specifying sizes is now handled via your ceph.conf')

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    def test_bluestore_partitions_wal_and_db_all_size_no_eq(self, create_mock, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        create_mock.assert_any_call('/dev/sdwal', [('wal', 'walsize')])
        create_mock.assert_any_call('/dev/sddb', [('db', 'dbsize')])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_db_size_no_eq(self, mock_log, create_mock, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_called_with('No size specified for wal /dev/sdwal. Using default sizes.')
        create_mock.assert_any_call('/dev/sddb', [('db', 'dbsize')])

    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_wal_size_no_eq(self, mock_log, create_mock, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        create_mock.assert_any_call('/dev/sdwal', [('wal', 'walsize')])

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_wal_and_db_no_sizes_no_eq(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_called()
        mock_log.warn.assert_called()

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_wal_and_size(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_any_call('WAL size is unsupported for same device of /dev/sdx')

    @mock.patch('srv.salt._modules.osd.OSDPartitions._halve')
    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_wal_and_size_no_eq(self, mock_log, create_mock, halve_mock, osdp_o):
        """
        Given I defined only wal
        And I have a wal_size
        And wal is not equivalent to the device
        Expect to call log()
        Expect to call _halve()
        Expect to call create()
        """
        kwargs = {'format': 'bluestore',
                  'wal': '/dev/sdwal',
                  'db': None,
                  'wal_size': 100000,
                  'db_size': None}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_called_with('Setting db to same device /dev/sdwal as wal')
        create_mock.assert_called_with('/dev/sdwal', [('wal', 100000), ('db', halve_mock('100000'))])
        halve_mock.assert_called_with('100000')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_wal_and_no_size(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_called_with('WAL size is unsupported for same device of /dev/sdx')

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_db_and_size_eq_log(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_called_with('DB size is unsupported for same device of /dev/sdx')

    @mock.patch('srv.salt._modules.osd.OSDPartitions._double')
    @mock.patch('srv.salt._modules.osd.OSDPartitions.create')
    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_only_db_and_size_no_eq_create(self, mock_log, create_mock, double_mock, osdp_o):
        """
        Given I haven't defined wal but a db
        And I have a db_size
        And wal isn't the same
        Expect to call log()
        Expect to call create()
        """
        kwargs = {'format': 'bluestore',
                  'wal': None,
                  'db': '/dev/sddb',
                  'wal_size': None,
                  'db_size': 100000}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_called_with('Setting wal to same device /dev/sddb as db')
        create_mock.assert_called_with('/dev/sddb', [('wal', double_mock(100000)), ('db', 100000)])
        double_mock.assert_called_with(100000)

    @mock.patch('srv.salt._modules.osd.log')
    def test_bluestore_partitions_no_waldb_no_db_log(self, mock_log, osdp_o):
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
        obj = osdp_o(osd_config)
        obj._bluestore_partitions(obj.osd.device)
        mock_log.warn.assert_called_with("DB size is unsupported for same device of /dev/sdx")

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd._run')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create(self, ex_mock, run_mock, pp_mock, lp_mock, osdp_o):
        """
        Given the device is a NVME
        And has a size
        And the RC is 0
        And the os.path.exists is True
        Expect to execute:
        _run 2x
        sgdisk
        dd
        _part_probe 1x
        """
        kwargs = {'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)

        lp_mock.return_value = 1
        run_mock.return_value = (0, 'stdout', 'stderr')
        ex_mock.return_value = True

        obj.create(osd_config.device,[('wal', 1000)])

        lp_mock.assert_called_with(osd_config.device)
        pp_mock.assert_called_with('/dev/nvme0n1p2')
        run_mock.assert_any_call('/usr/sbin/sgdisk -n 2:0:+1000 -t 2:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/nvme0n1')
        run_mock.assert_any_call('dd if=/dev/zero of=/dev/nvme0n12 bs=4096 count=1 oflag=direct')
        #                                                       ^^ that's wrong imho

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd._run')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create_1(self, ex_mock, run_mock, pp_mock, lp_mock, osdp_o):
        """
        Given the device is a NVME
        And has a size
        And the RC is 0
        And the os.path.exists is False
        Expect to execute:
        _run 1x
        sgdisk
        _part_probe 1x
        """
        kwargs = {'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)

        lp_mock.return_value = 1
        run_mock.return_value = (0, 'stdout', 'stderr')
        ex_mock.return_value = False

        obj.create(osd_config.device,[('wal', 1000)])

        lp_mock.assert_called_with(osd_config.device)
        pp_mock.assert_called_with('/dev/nvme0n1p2')
        run_mock.assert_any_call('/usr/sbin/sgdisk -n 2:0:+1000 -t 2:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/nvme0n1')

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd._run')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create_2(self, ex_mock, run_mock, pp_mock, lp_mock, osdp_o):
        """
        Given the device is a NVME
        And has a size
        And the RC is 1
        Expect to execute:
        _run 1x
        sgdisk
        """
        kwargs = {'device': '/dev/nvme0n1'}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)

        lp_mock.return_value = 1
        run_mock.return_value = (99, 'stdout', 'stderr')
        ex_mock.return_value = False

        with pytest.raises(BaseException) as excinfo:
            obj.create(osd_config.device,[('wal', 1000)])
            lp_mock.assert_called_with(osd_config.device)
            run_mock.assert_any_call('/usr/sbin/sgdisk -n 2:0:+1000 -t 2:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/nvme0n1')
            assert '/usr/sbin/sgdisk -n 2:0:+1000 -t 2:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/nvme0n1 failed' in str(excinfo.value)

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd._run')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create_3(self, ex_mock, run_mock, pp_mock, lp_mock, osdp_o):
        """
        Given the device is not a NVME
        And has a no size
        And the RC is 0
        And the os.path.exists is False
        Expect to execute:
        _run 1x
        sgdisk
        _part_probe 1x
        """
        kwargs = {'device': '/dev/sdx'}
        osd_config = OSDConfig(**kwargs)
        obj = osdp_o(osd_config)

        lp_mock.return_value = 1
        run_mock.return_value = (0, 'stdout', 'stderr')
        ex_mock.return_value = False

        obj.create(osd_config.device,[('wal', None)])

        lp_mock.assert_called_with(osd_config.device)
        pp_mock.assert_called_with('/dev/sdx2')
        run_mock.assert_any_call('/usr/sbin/sgdisk -N 2 -t 2:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/sdx')

    @mock.patch('srv.salt._modules.osd.OSDPartitions._last_partition')
    @mock.patch('srv.salt._modules.osd._run')
    @mock.patch('srv.salt._modules.osd.OSDPartitions._part_probe')
    @mock.patch('srv.salt._modules.osd.os.path.exists')
    def test_create_4_last_part(self, ex_mock, pp_mock, run_mock, lp_mock, osdp_o):
        """
        Given the device is not a NVME
        And has a no size
        And the RC is 0
        And the os.path.exists is False
        Expect to execute:
        _run 1x
        sgdisk
        _part_probe 1x
        Partition Param to 4
        """
        osd_config = OSDConfig()
        obj = osdp_o(osd_config)

        lp_mock.return_value = 4
        ex_mock.return_value = False
        run_mock.return_value = (0, 'stdout', 'stderr')

        obj.create(osd_config.device,[('wal', 1000)])

        pp_mock.assert_called
        lp_mock.assert_called_with(osd_config.device)
        run_mock.assert_any_call('/usr/sbin/sgdisk -n 5:0:+1000 -t 5:5CE17FCE-4087-4169-B7FF-056CC58473F9 /dev/sdx')

    @mock.patch('srv.salt._modules.osd.glob')
    def test__last_partition(self, glob_mock, osdp_o):
        glob_mock.glob.return_value = ['/dev/sdx1']
        osd_config = OSDConfig()
        obj = osdp_o(osd_config)
        ret = obj._last_partition(osd_config.device)
        glob_mock.glob.assert_called_with('/dev/sdx[0-9]*')
        assert type(ret) is int

    @mock.patch('srv.salt._modules.osd.glob')
    def test__last_partition_no_pathnames(self, glob_mock, osdp_o):
        glob_mock.glob.return_value = []
        osd_config = OSDConfig()
        obj = osdp_o(osd_config)
        ret = obj._last_partition(osd_config.device)
        glob_mock.glob.assert_called_with('/dev/sdx[0-9]*')
        assert ret == 0

    @pytest.mark.skip(reason='postponed')
    def test__last_partition_no_pathnames(self, osdp_o):
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


    @pytest.mark.skip(reason="FIXME: refactor to _run()")
    def test_is_partition(self, osdc_o):
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
        assert ret == "ceph-disk -v activate --mark-init systemd --mount /dev/nvme0n1p1"

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
        assert ret == "ceph-disk -v activate --mark-init systemd --mount /dev/sdx1"

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
