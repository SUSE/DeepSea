import pytest
from mock import patch, call, Mock, PropertyMock
from srv.salt._modules import dg
from tests.unit.helper.fixtures import helper_specs


class InventoryFactory(object):
    def __init__(self):
        self.taken_paths = []

    def _make_path(self, ident='b'):
        return "/dev/{}{}".format(self.prefix, ident)

    def _find_new_path(self):
        cnt = 0
        if len(self.taken_paths) >= 25:
            raise Exception(
                "Double-character disks are not implemetend. Maximum amount"
                "of disks reached.")

        while self.path in self.taken_paths:
            ident = chr(ord('b') + cnt)
            self.path = "/dev/{}{}".format(self.prefix, ident)
            cnt += 1

    def assemble(self):
        if self.empty:
            return {}
        self._find_new_path()
        inventory_sample = {
            'available': self.available,
            'lvs': [],
            'path': self.path,
            'rejected_reasons': self.rejected_reason,
            'sys_api': {
                'human_readable_size': self.human_readable_size,
                'locked': 1,
                'model': self.model,
                'nr_requests': '256',
                'partitions':
                {  # partitions are not as relevant for now, todo for later
                    'vda1': {
                        'sectors': '41940992',
                        'sectorsize': 512,
                        'size': self.human_readable_size,
                        'start': '2048'
                    }
                },
                'path': self.path,
                'removable': '0',
                'rev': '',
                'ro': '0',
                'rotational': str(self.rotational),
                'sas_address': '',
                'sas_device_handle': '',
                'scheduler_mode': 'mq-deadline',
                'sectors': 0,
                'sectorsize': '512',
                'size': 123,  # TODO
                'support_discard': '',
                'vendor': self.vendor
            }
        }
        self.taken_paths.append(self.path)
        return inventory_sample

    def _init(self, **kwargs):
        self.prefix = 'vd'
        self.path = kwargs.get('path', self._make_path())
        self.human_readable_size = kwargs.get('human_readable_size',
                                              '50.00 GB')
        self.vendor = kwargs.get('vendor', 'samsung')
        self.model = kwargs.get('model', '42-RGB')
        self.available = kwargs.get('available', True)
        self.rejected_reason = kwargs.get('rejected_reason', [''])
        self.rotational = kwargs.get('rotational', '1')
        if not self.available:
            self.rejected_reason = ['locked']
        self.empty = kwargs.get('empty', False)

    def produce(self, pieces=1, **kwargs):
        if kwargs.get('path') and pieces > 1:
            raise Exception("/path/ and /pieces/ are mutually exclusive")
        # Move to custom init to track _taken_paths.
        # class is invoked once in each context.
        # if disks with different properties are being created
        # we'd have to re-init the class and loose track of the
        # taken_paths
        self._init(**kwargs)
        return [self.assemble() for x in range(0, pieces)]


class TestInventory(object):
    """ Test Inventory container class
    """

    def test_inventory_raw(self):
        """ Check if c-v inv gets called
        """
        dg.__salt__ = {}
        dg.__salt__['helper.run'] = Mock()
        dg.__salt__['helper.run'].return_value = (1, "out", "err")
        dg.Inventory().raw
        call1 = call("ceph-volume inventory --format json")
        assert call1 in dg.__salt__['helper.run'].call_args_list


class TestDirtyJson(object):
    """
    Test dirty json parser
    """

    @pytest.mark.parametrize("test_input,expected", [('sdmkh{"foo":"bar"}', {
        "foo": "bar"
    }), ('{"foo":"bar"}', {
        "foo": "bar"
    }), ('sdmkh[{"foo":"bar"}]', [{
        "foo": "bar"
    }]), ('sdmkh[{"foo":\n"bar"}]', [{
        "foo": "bar"
    }]), ('sdmkh[{"foo":"bar"}]', [{
        "foo": "bar"
    }]), ('sdmkh[{"foo":{"bar":"foobar"}}]', [{
        "foo": {
            "bar": "foobar"
        }
    }])])
    def test_dirty_json(self, test_input, expected):
        assert dg._parse_dirty_json(test_input) == expected


class TestMatcher(object):
    """ Test Matcher base class
    """

    @patch(
        "srv.salt._modules.dg.Matcher._virtual",
        autospec=True,
        return_value=True)
    def test_get_disk_key_1(self, whatthefuck):
        """
        virtual is True
        key is found
        return value of key is expected
        """
        disk_map = dict(path='/dev/vdb', foo='bar')
        ret = dg.Matcher('foo', 'bar')._get_disk_key(disk_map)
        assert ret == disk_map.get('foo')

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_get_disk_key_2(self, virtual_mock):
        """
        virtual is True
        key is not found
        retrun False is expected
        """
        virtual_mock.return_value = True
        disk_map = dict(path='/dev/vdb')
        ret = dg.Matcher('bar', 'foo')._get_disk_key(disk_map)
        assert ret is ''

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_get_disk_key_3(self, virtual_mock):
        """
        virtual is False
        key is found
        retrun value of key is expected
        """
        virtual_mock.return_value = False
        disk_map = dict(path='/dev/vdb', foo='bar')
        ret = dg.Matcher('foo', 'bar')._get_disk_key(disk_map)
        assert ret is disk_map.get('foo')

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_get_disk_key_4(self, virtual_mock):
        """
        virtual is False
        key is not found
        expect raise Exception
        """
        virtual_mock.return_value = False
        disk_map = dict(path='/dev/vdb')
        with pytest.raises(
                Exception, message="No disk_key found for foo or None"):
            dg.Matcher('bar', 'foo')._get_disk_key(disk_map)

    def test_virtual(self):
        """ Test if virtual
        """
        dg.__grains__ = {'virtual': 'kvm'}
        obj = dg.Matcher(None, None)
        obj.virtual is True

    def test_virtual_1(self):
        """ all hosts are physical
        """
        dg.__grains__ = {'virtual': 'pysical'}
        obj = dg.Matcher(None, None)
        obj.virtual is False


class TestSubstringMatcher(object):
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare(self, virtual_mock):
        virtual_mock.return_value = False
        disk_dict = dict(path='/dev/vdb', model='samsung')
        matcher = dg.SubstringMatcher('model', 'samsung')
        ret = matcher.compare(disk_dict)
        assert ret is True

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_false(self, virtual_mock):
        virtual_mock.return_value = False
        disk_dict = dict(path='/dev/vdb', model='nothing_matching')
        matcher = dg.SubstringMatcher('model', 'samsung')
        ret = matcher.compare(disk_dict)
        assert ret is False


class TestEqualityMatcher(object):
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare(self, virtual_mock):
        virtual_mock.return_value = False
        disk_dict = dict(path='/dev/vdb', rotates='1')
        matcher = dg.EqualityMatcher('rotates', '1')
        ret = matcher.compare(disk_dict)
        assert ret is True

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_false(self, virtual_mock):
        virtual_mock.return_value = False
        disk_dict = dict(path='/dev/vdb', rotates='1')
        matcher = dg.EqualityMatcher('rotates', '0')
        ret = matcher.compare(disk_dict)
        assert ret is False


class TestAllMatcher(object):
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare(self, virtual_mock):
        virtual_mock.return_value = False
        disk_dict = dict(path='/dev/vdb')
        matcher = dg.AllMatcher('all', 'True')
        ret = matcher.compare(disk_dict)
        assert ret is True

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_value_not_true(self, virtual_mock):
        virtual_mock.return_value = False
        disk_dict = dict(path='/dev/vdb')
        matcher = dg.AllMatcher('all', 'False')
        ret = matcher.compare(disk_dict)
        assert ret is True


class TestSizeMatcher(object):
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_parse_filter_exact(self, virtual_mock):
        """ Testing exact notation with 20G """
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', '20G')
        assert isinstance(matcher.exact, tuple)
        assert matcher.exact[0] == '20'
        assert matcher.exact[1] == 'GB'

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_parse_filter_exact_GB_G(self, virtual_mock):
        """ Testing exact notation with 20G """
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', '20GB')
        assert isinstance(matcher.exact, tuple)
        assert matcher.exact[0] == '20'
        assert matcher.exact[1] == 'GB'

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_parse_filter_high_low(self, virtual_mock):
        """ Testing high-low notation with 20G:50G """
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', '20G:50G')
        assert isinstance(matcher.exact, tuple)
        assert matcher.low[0] == '20'
        assert matcher.high[0] == '50'
        assert matcher.low[1] == 'GB'
        assert matcher.high[1] == 'GB'

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_parse_filter_max_high(self, virtual_mock):
        """ Testing high notation with :50G """
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', ':50G')
        assert isinstance(matcher.exact, tuple)
        assert matcher.high[0] == '50'
        assert matcher.high[1] == 'GB'

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_parse_filter_min_low(self, virtual_mock):
        """ Testing low notation with 20G: """
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', '50G:')
        assert isinstance(matcher.exact, tuple)
        assert matcher.low[0] == '50'
        assert matcher.low[1] == 'GB'

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_to_byte_GB(self, virtual_mock):
        """ Pretty nonesense test.."""
        virtual_mock.return_value = False
        ret = dg.SizeMatcher('size', '10G').to_byte(('10', 'GB'))
        assert ret == 10 * 1e+9

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_to_byte_MB(self, virtual_mock):
        """ Pretty nonesense test.."""
        virtual_mock.return_value = False
        ret = dg.SizeMatcher('size', '10M').to_byte(('10', 'MB'))
        assert ret == 10 * 1e+6

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_to_byte_TB(self, virtual_mock):
        """ Pretty nonesense test.."""
        virtual_mock.return_value = False
        ret = dg.SizeMatcher('size', '10T').to_byte(('10', 'TB'))
        assert ret == 10 * 1e+12

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_to_byte_PB(self, virtual_mock):
        """ Expect to raise """
        virtual_mock.return_value = False
        with pytest.raises(dg.UnitNotSupported):
            dg.SizeMatcher('size', '10P').to_byte(('10', 'PB'))
        assert 'Unit \'P\' is not supported'

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_exact(self, virtual_mock):
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', '20GB')
        disk_dict = dict(path='/dev/vdb', size='20.00 GB')
        ret = matcher.compare(disk_dict)
        assert ret is True

    @pytest.mark.parametrize("test_input,expected", [
        ("1.00 GB", False),
        ("20.00 GB", True),
        ("50.00 GB", True),
        ("100.00 GB", True),
        ("101.00 GB", False),
        ("1101.00 GB", False),
    ])
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_high_low(self, virtual_mock, test_input, expected):
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', '20GB:100GB')
        disk_dict = dict(path='/dev/vdb', size=test_input)
        ret = matcher.compare(disk_dict)
        assert ret is expected

    @pytest.mark.parametrize("test_input,expected", [
        ("1.00 GB", True),
        ("20.00 GB", True),
        ("50.00 GB", True),
        ("100.00 GB", False),
        ("101.00 GB", False),
        ("1101.00 GB", False),
    ])
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_high(self, virtual_mock, test_input, expected):
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', ':50GB')
        disk_dict = dict(path='/dev/vdb', size=test_input)
        ret = matcher.compare(disk_dict)
        assert ret is expected

    @pytest.mark.parametrize("test_input,expected", [
        ("1.00 GB", False),
        ("20.00 GB", False),
        ("50.00 GB", True),
        ("100.00 GB", True),
        ("101.00 GB", True),
        ("1101.00 GB", True),
    ])
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_low(self, virtual_mock, test_input, expected):
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', '50GB:')
        disk_dict = dict(path='/dev/vdb', size=test_input)
        ret = matcher.compare(disk_dict)
        assert ret is expected

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_raise(self, virtual_mock):
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', 'None')
        disk_dict = dict(path='/dev/vdb', size='20.00 GB')
        with pytest.raises(Exception, message="Couldn't parse size"):
            matcher.compare(disk_dict)

    @pytest.mark.parametrize("test_input,expected", [
        ("10G", ('10', 'GB')),
        ("20GB", ('20', 'GB')),
    ])
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_get_k_v(self, virtual_mock, test_input, expected):
        virtual_mock.return_value = False
        assert dg.SizeMatcher('size', '10G')._get_k_v(test_input) == expected

    @pytest.mark.parametrize("test_input,expected", [
        ("10G", ('GB')),
        ("20GB", ('GB')),
        ("20TB", ('TB')),
        ("20T", ('TB')),
        ("20MB", ('MB')),
        ("20M", ('MB')),
    ])
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_parse_suffix(self, virtual_mock, test_input, expected):
        virtual_mock.return_value = False
        assert dg.SizeMatcher('size',
                              '10G')._parse_suffix(test_input) == expected

    @pytest.mark.parametrize("test_input,expected", [
        ("G", 'GB'),
        ("GB", 'GB'),
        ("TB", 'TB'),
        ("T", 'TB'),
        ("MB", 'MB'),
        ("M", 'MB'),
    ])
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_normalize_suffix(self, virtual_mock, test_input, expected):
        virtual_mock.return_value = False
        assert dg.SizeMatcher('10G',
                              'size')._normalize_suffix(test_input) == expected

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_normalize_suffix_raises(self, virtual_mock):
        virtual_mock.return_value = False
        with pytest.raises(
                dg.UnitNotSupported, message="Unit 'P' not supported"):
            dg.SizeMatcher('10P', 'size')._normalize_suffix("P")


class TestDriveGroup(object):
    @pytest.fixture(scope='class')
    def test_fix(self, empty=None):
        def make_sample_data(empty=empty,
                             data_limit=0,
                             wal_limit=0,
                             db_limit=0,
                             disk_format='bluestore'):
            raw_sample_bluestore = {
                'target': 'data*',
                'format': 'bluestore',
                'data_devices': {
                    'size': '30G:50G',
                    'model': '42-RGB',
                    'vendor': 'samsung',
                    'limit': data_limit
                },
                'wal_devices': {
                    'model': 'fast',
                    'limit': wal_limit
                },
                'db_devices': {
                    'size': ':20G',
                    'limit': db_limit
                },
                'db_slots': 5,
                'wal_slots': 5,
                'block_wal_size': 500,
                'block_db_size': 500,
                'objectstore': 'bluestore',
                'encryption': True,
            }
            raw_sample_filestore = {
                'target': 'data*',
                'format': 'filestore',
                'data_devices': {
                    'size': '30G:50G',
                    'model': 'foo',
                    'vendor': '1x',
                    'limit': data_limit
                },
                'journal_devices': {
                    'size': ':20G'
                },
                'journal_size': '500',
                'encryption': True,
            }
            if disk_format == 'filestore':
                raw_sample = raw_sample_filestore
            else:
                raw_sample = raw_sample_bluestore

            if empty:
                raw_sample = {}

            self.check_filter_support = patch(
                'srv.salt._modules.dg.DriveGroup._check_filter_support',
                new_callable=Mock,
                return_value=True)

            self.check_filter_support.start()

            dgo = dg.DriveGroup(raw_sample)
            return dgo

            self.check_filter_support.stop()

        return make_sample_data

    def test_encryption_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.encryption is True

    def test_encryption_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.encryption is False

    def test_db_slots_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.db_slots is 5

    def test_db_slots_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.db_slots is 5

    def test_db_slots_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.db_slots is False

    def test_wal_slots_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.wal_slots is 5

    def test_wal_slots_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.wal_slots is False

    def test_block_wal_size_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.block_wal_size == 500

    def test_block_wal_size_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.block_wal_size == 0

    def test_block_db_size_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.block_db_size == 500

    def test_block_db_size_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.block_db_size == 0

    def test_data_devices_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.data_device_attrs == {
            'model': '42-RGB',
            'size': '30G:50G',
            'vendor': 'samsung',
            'limit': 0
        }

    def test_data_devices_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.data_device_attrs == {}

    def test_db_devices_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.db_device_attrs == {
            'size': ':20G',
            'limit': 0,
        }

    def test_db_devices_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.db_device_attrs == {}

    def test_wal_device_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.wal_device_attrs == {
            'model': 'fast',
            'limit': 0,
        }

    def test_journal_device_prop(self, test_fix):
        test_fix = test_fix(disk_format='filestore')
        assert test_fix.journal_device_attrs == {
            'size': ':20G',
        }

    def test_wal_device_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.wal_device_attrs == {}

    @patch(
        'srv.salt._modules.dg.DriveGroup._filter_devices', new_callable=Mock)
    def test_data_devices(self, filter_mock, test_fix):
        test_fix = test_fix()
        test_fix.data_devices
        filter_mock.assert_called_once_with({
            'size': '30G:50G',
            'model': '42-RGB',
            'vendor': 'samsung',
            'limit': 0
        })

    @patch(
        'srv.salt._modules.dg.DriveGroup._filter_devices', new_callable=Mock)
    def test_wal_devices(self, filter_mock, test_fix):
        test_fix = test_fix()
        test_fix.wal_devices
        filter_mock.assert_called_once_with({'model': 'fast', 'limit': 0})

    @patch(
        'srv.salt._modules.dg.DriveGroup._filter_devices', new_callable=Mock)
    def test_db_devices(self, filter_mock, test_fix):
        test_fix = test_fix()
        test_fix.db_devices
        filter_mock.assert_called_once_with({'size': ':20G', 'limit': 0})

    @patch(
        'srv.salt._modules.dg.DriveGroup._filter_devices', new_callable=Mock)
    def test_journal_devices(self, filter_mock, test_fix):
        test_fix = test_fix(disk_format='filestore')
        test_fix.journal_devices
        filter_mock.assert_called_once_with({'size': ':20G'})

    def test_filestore_format_prop(self, test_fix):
        test_fix = test_fix(disk_format='filestore')
        assert test_fix.format == 'filestore'

    def test_bluestore_format_prop(self, test_fix):
        test_fix = test_fix(disk_format='bluestore')
        assert test_fix.format == 'bluestore'

    def test_default_format_prop(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.format == 'bluestore'

    def test_journal_size(self, test_fix):
        test_fix = test_fix(disk_format='filestore')
        assert test_fix.journal_size == '500'

    def test_journal_size_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.journal_size == 0

    @pytest.fixture
    def inventory(self, available=True):
        def make_sample_data(available=available,
                             data_devices=10,
                             wal_devices=0,
                             db_devices=2):
            factory = InventoryFactory()
            inventory_sample = []
            data_disks = factory.produce(
                pieces=data_devices, available=available)
            wal_disks = factory.produce(
                pieces=wal_devices,
                human_readable_size='20.00 GB',
                rotational='0',
                model='ssd_type_model',
                available=available)
            db_disks = factory.produce(
                pieces=db_devices,
                human_readable_size='20.00 GB',
                rotational='0',
                model='ssd_type_model',
                available=available)
            inventory_sample.extend(data_disks)
            inventory_sample.extend(wal_disks)
            inventory_sample.extend(db_disks)

            self.disks_mock = patch(
                'srv.salt._modules.dg.Inventory.disks',
                new_callable=PropertyMock,
                return_value=inventory_sample)
            self.disks_mock.start()

            inv = dg.Inventory()
            return inv.disks

            self.disks_mock.stop()

        return make_sample_data

    def test_filter_devices_10_size_min_max(self, test_fix, inventory):
        """ Test_fix's data_device_attrs is configured to take any disk from
        30G - 50G or with vendor samsung or with model 42-RGB
        The default inventory setup is configured to have 10 data devices(50G)
        and 2 wal devices(20G).
        The expected match is 12
        """
        # initialize inventory once (scope is session by default)
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(test_fix.data_device_attrs)
        assert len(ret) == 12

    def test_filter_devices_size_exact(self, test_fix, inventory):
        """
        Configure to only take disks with 20G (exact)
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size='20G'))
        assert len(ret) == 2

    def test_filter_devices_2_max(self, test_fix, inventory):
        """
        Configure to only take disks with a max of 30G
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size=':30G'))
        assert len(ret) == 2

    def test_filter_devices_0_max(self, test_fix, inventory):
        """
        Configure to only take disks with a max of 10G
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size=':10G'))
        assert len(ret) == 0

    def test_filter_devices_12_min(self, test_fix, inventory):
        """
        Configure to only take disks with a min of 10G
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size='10G:'))
        assert len(ret) == 12

    def test_filter_devices_12_min(self, test_fix, inventory):
        """
        Configure to only take disks with a min of 20G
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size='20G:'))
        assert len(ret) == 12

    def test_filter_devices_0_model(self, test_fix, inventory):
        """
        Configure to only take disks with a model of modelA
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(model='unknown'))
        assert len(ret) == 0

    def test_filter_devices_2_model(self, test_fix, inventory):
        """
        Configure to only take disks with a model of model*(wildcard)
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(model='ssd_type_model'))
        assert len(ret) == 2

    def test_filter_devices_12_vendor(self, test_fix, inventory):
        """
        Configure to only take disks with a vendor of samsung
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(vendor='samsung'))
        assert len(ret) == 12

    def test_filter_devices_2_rotational(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 0
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(rotational='0'))
        assert len(ret) == 2

    def test_filter_devices_10_rotational(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(rotational='1'))
        assert len(ret) == 10

    def test_filter_devices_limit(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take two disks, but limit=1 is in place
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(rotational='1', limit=1))
        assert len(ret) == 1

    def test_filter_devices_all_limit_2(self, test_fix, inventory):
        """
        Configure to take all disks
        limiting to two
        """
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(all=True, limit=2))
        assert len(ret) == 2

    def test_filter_devices_empty_list_eq_matcher(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take 10 disks, but limit=1 is in place
        Available is set to False. No disks are assigned
        """
        inventory(available=False)
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(rotational='1', limit=1))
        assert len(ret) == 0

    def test_filter_devices_empty_string_matcher(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take two disks, but limit=1 is in place
        Available is set to False. No disks are assigned
        """
        inventory(available=False)
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(vendor='samsung', limit=1))
        assert len(ret) == 0

    def test_filter_devices_empty_size_matcher(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take two disks, but limit=1 is in place
        Available is set to False. No disks are assigned
        """
        inventory(available=False)
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size='10G:100G', limit=1))
        assert len(ret) == 0

    def test_filter_devices_empty_all_matcher(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take two disks, but limit=1 is in place
        Available is set to False. No disks are assigned
        """
        inventory(available=False)
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(all=True, limit=1))
        assert len(ret) == 0

    @patch('srv.salt._modules.dg.DriveGroup._check_filter')
    def test_check_filter_support(self, check_filter_mock, test_fix):
        test_fix = test_fix()
        test_fix._check_filter_support()
        check_filter_mock.assert_called

    def test_check_filter(self, test_fix):
        test_fix = test_fix()
        ret = test_fix._check_filter(dict(model='foo'))
        assert ret is None

    def test_check_filter_raise(self, test_fix):
        test_fix = test_fix()
        with pytest.raises(
                dg.FilterNotSupported,
                message="Filter unknown is not supported"):
            test_fix._check_filter(dict(unknown='foo'))

    def test_list_devices(self):
        pass

    def test_c_v_commands(self, test_fix, inventory):
        inventory()
        test_fix = test_fix()
        ret = dg.c_v_commands(filter_args=test_fix.filter_args)
        assert ret == [
            'ceph-volume lvm batch --no-auto /dev/vdb /dev/vdc /dev/vdd /dev/vde /dev/vdf /dev/vdg /dev/vdh /dev/vdi /dev/vdj /dev/vdk /dev/vdl /dev/vdm --yes --dmcrypt --block-wal-size 500 --block-db-size 500'
        ]

    def test_c_v_commands_filestore(self, test_fix, inventory):
        inventory()
        test_fix = test_fix(disk_format='filestore')
        ret = dg.c_v_commands(filter_args=test_fix.filter_args)
        assert ret == [
            'ceph-volume lvm batch /dev/vdb /dev/vdc /dev/vdd /dev/vde /dev/vdf /dev/vdg /dev/vdh /dev/vdi /dev/vdj /dev/vdk --journal-size 500 --journal-devices /dev/vdl /dev/vdm --filestore --yes --dmcrypt'
        ]

    def test_c_v_commands_external_db(self, test_fix, inventory):
        inventory()
        ret = dg.c_v_commands(filter_args={
            'data_devices': {
                'rotational': '1'
            },
            'db_devices': {
                'rotational': '0'
            }
        })
        assert ret == [
            'ceph-volume lvm batch --no-auto /dev/vdb /dev/vdd /dev/vdf /dev/vdh /dev/vdj --db-devices /dev/vdl --yes',
            'ceph-volume lvm batch --no-auto /dev/vdc /dev/vde /dev/vdg /dev/vdi /dev/vdk --db-devices /dev/vdm --yes'
        ]

    def test_c_v_commands_external_wal_only(self, test_fix, inventory):
        inventory(wal_devices=2, db_devices=0)
        with pytest.raises(dg.ConfigError):
            dg.c_v_commands(
                filter_args={
                    'data_devices': {
                        'rotational': '1'
                    },
                    'wal_devices': {
                        'rotational': '0'
                    }
                })

    def test_c_v_commands_external_2_dbs_and_2_wals(self, test_fix, inventory):
        inventory(db_devices=2, wal_devices=2)
        ret = dg.c_v_commands(
            filter_args={
                'data_devices': {
                    'rotational': '1'
                },
                'db_devices': {
                    'rotational': '0',
                    'limit': 2
                },
                'wal_devices': {
                    'rotational': '0',
                    'limit': 2
                }
            })
        assert ret == [
            'ceph-volume lvm batch --no-auto /dev/vdb /dev/vdd /dev/vdf /dev/vdh /dev/vdj --db-devices /dev/vdn --wal-devices /dev/vdl --yes',
            'ceph-volume lvm batch --no-auto /dev/vdc /dev/vde /dev/vdg /dev/vdi /dev/vdk --db-devices /dev/vdo --wal-devices /dev/vdm --yes'
        ]

    def test_c_v_commands_external_2_dbs_and_3_wals(self, test_fix, inventory):
        inventory(db_devices=2, wal_devices=3)
        ret = dg.c_v_commands(
            filter_args={
                'data_devices': {
                    'rotational': '1'
                },
                'db_devices': {
                    'rotational': '0',
                    'limit': 2
                },
                'wal_devices': {
                    'rotational': '0',
                    'limit': 3
                }
            })
        assert [
            'ceph-volume lvm batch --no-auto /dev/vdb /dev/vdd /dev/vdf /dev/vdh /dev/vdj --db-devices /dev/vdo --wal-devices /dev/vdl /dev/vdn --yes',
            'ceph-volume lvm batch --no-auto /dev/vdc /dev/vde /dev/vdg /dev/vdi /dev/vdk --db-devices /dev/vdp --wal-devices /dev/vdm --yes'
        ] == ret

    def test_c_v_commands_11_data_external_3_dbs_and_1_wals(
            self, test_fix, inventory):
        inventory(data_devices=11, db_devices=3, wal_devices=1)
        with pytest.raises(dg.ConfigError):
            dg.c_v_commands(
                filter_args={
                    'data_devices': {
                        'rotational': '1'
                    },
                    'db_devices': {
                        'rotational': '0',
                        'limit': 3
                    },
                    'wal_devices': {
                        'rotational': '0',
                        'limit': 1
                    }
                })

    @patch("srv.salt._modules.dg.c_v_commands", autospec=True)
    def test_deploy(self, c_v_commands):
        """
        No ceph-volume commands
        No errors
        No old profiles in the pillar
        """
        c_v_commands.return_value = []
        dg.__pillar__ = {}
        dg.__salt__ = {}
        dg.__salt__['helper.run'] = Mock()
        ret = dg.deploy()
        dg.__salt__['helper.run'].assert_not_called
        assert ret == []

    @patch("srv.salt._modules.dg.c_v_commands", autospec=True)
    def test_deploy_1(self, c_v_commands):
        """
        No ceph-volume commands
        No errors
        Old profiles in the pillar
        """
        c_v_commands.return_value = []
        dg.__pillar__ = {'ceph': {'storage': {'something'}}}
        dg.__salt__ = {}
        dg.__salt__['helper.run'] = Mock()
        ret = dg.deploy()
        dg.__salt__['helper.run'].assert_not_called()
        assert "You seem to have configured" in ret

    @patch("srv.salt._modules.dg.c_v_commands", autospec=True)
    def test_deploy_2(self, c_v_commands):
        """
        ceph-volume commands
        No errors
        No old profiles in the pillar
        """
        c_v_commands.return_value = ['ceph-volume foo bar baz']
        dg.__pillar__ = {}
        dg.__salt__ = {}
        dg.__salt__['helper.run'] = Mock()
        ret = dg.deploy()
        dg.__salt__['helper.run'].assert_called_once_with(
            'ceph-volume foo bar baz')
        assert len(ret) == len(c_v_commands.return_value)

    @patch("srv.salt._modules.dg.c_v_commands", autospec=True)
    def test_deploy_3(self, c_v_commands):
        """
        No ceph-volume commands
        One error
        No old profiles in the pillar
        """
        c_v_commands.return_value = ['An error message']
        dg.__pillar__ = {}
        dg.__salt__ = {}
        dg.__salt__['helper.run'] = Mock()
        ret = dg.deploy()
        dg.__salt__['helper.run'].assert_not_called()
        assert len(ret) == 0

    @patch("srv.salt._modules.dg.c_v_commands", autospec=True)
    def test_deploy_4(self, c_v_commands):
        """
        No ceph-volume commands
        One error
        No old profiles in the pillar
        """
        c_v_commands.return_value = ['']
        dg.__pillar__ = {}
        dg.__salt__ = {}
        dg.__salt__['helper.run'] = Mock()
        ret = dg.deploy()
        dg.__salt__['helper.run'].assert_not_called()
        assert len(ret) == 0


class TestFilter(object):
    def test_is_matchable(self):
        ret = dg.Filter()
        assert ret.is_matchable is False

    def test_assign_matchers_all(self):
        ret = dg.Filter(name='all', value='True')
        assert isinstance(ret.matcher, dg.AllMatcher)
        assert ret.is_matchable is True

    def test_assign_matchers_all_2(self):
        """ Should match regardless of value"""
        ret = dg.Filter(name='all', value='False')
        assert isinstance(ret.matcher, dg.AllMatcher)
        assert ret.is_matchable is True

    def test_assign_matchers_size(self):
        ret = dg.Filter(name='size', value='10G')
        assert isinstance(ret.matcher, dg.SizeMatcher)
        assert ret.is_matchable is True

    def test_assign_matchers_model(self):
        ret = dg.Filter(name='model', value='abc123')
        assert isinstance(ret.matcher, dg.SubstringMatcher)
        assert ret.is_matchable is True

    def test_assign_matchers_vendor(self):
        ret = dg.Filter(name='vendor', value='samsung')
        assert isinstance(ret.matcher, dg.SubstringMatcher)
        assert ret.is_matchable is True

    def test_assign_matchers_rotational(self):
        ret = dg.Filter(name='rotational', value='0')
        assert isinstance(ret.matcher, dg.EqualityMatcher)
        assert ret.is_matchable is True
