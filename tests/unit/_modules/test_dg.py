import pytest
from mock import patch, call, Mock, PropertyMock
from srv.salt._modules import dg
from tests.unit.helper.fixtures import helper_specs
from tests.unit.helper.factories import InventoryFactory


class TestMatcher(object):
    """ Test Matcher base class
    """

    @patch(
        "srv.salt._modules.dg.Matcher._virtual",
        autospec=True,
        return_value=True)
    def test_get_disk_key_1(self, virtual):
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
        with pytest.raises(Exception):
            dg.Matcher('bar', 'foo')._get_disk_key(disk_map)
            pytest.fail("No disk_key found for foo or None")

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

    @pytest.mark.parametrize("test_input,expected", [
        ("1.00 GB", False),
        ("20.00 GB", False),
        ("50.00 GB", False),
        ("100.00 GB", False),
        ("101.00 GB", False),
        ("1101.00 GB", True),
        ("9.10 TB", True),
    ])
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_at_least_1TB(self, virtual_mock, test_input, expected):
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', '1TB:')
        disk_dict = dict(path='/dev/sdz', size=test_input)
        ret = matcher.compare(disk_dict)
        assert ret is expected

    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_compare_raise(self, virtual_mock):
        virtual_mock.return_value = False
        matcher = dg.SizeMatcher('size', 'None')
        disk_dict = dict(path='/dev/vdb', size='20.00 GB')
        with pytest.raises(Exception):
            matcher.compare(disk_dict)
            pytest.fail("Couldn't parse size")

    @pytest.mark.parametrize("test_input,expected", [
        ("10G", ('10', 'GB')),
        ("20GB", ('20', 'GB')),
        ("10g", ('10', 'GB')),
        ("20gb", ('20', 'GB')),
    ])
    @patch("srv.salt._modules.dg.Matcher._virtual", autospec=True)
    def test_get_k_v(self, virtual_mock, test_input, expected):
        virtual_mock.return_value = False
        assert dg.SizeMatcher('size', '10G')._get_k_v(test_input) == expected

    @pytest.mark.parametrize("test_input,expected", [
        ("10G", ('GB')),
        ("10g", ('GB')),
        ("20GB", ('GB')),
        ("20gb", ('GB')),
        ("20TB", ('TB')),
        ("20tb", ('TB')),
        ("20T", ('TB')),
        ("20t", ('TB')),
        ("20MB", ('MB')),
        ("20mb", ('MB')),
        ("20M", ('MB')),
        ("20m", ('MB')),
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
        with pytest.raises(dg.UnitNotSupported):
            dg.SizeMatcher('10P', 'size')._normalize_suffix("P")
            pytest.fail("Unit 'P' not supported")


class TestDriveGroup(object):
    @pytest.fixture(scope='class')
    def test_fix(self, empty=None):
        def make_sample_data(empty=empty,
                             data_limit=0,
                             wal_limit=0,
                             db_limit=0,
                             osds_per_device='',
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
                'objectstore': disk_format,
                'osds_per_device': osds_per_device,
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
                'osds_per_device': osds_per_device,
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

            dg.__salt__ = dict()
            dg.__salt__['cephdisks.all'] = lambda : []
            dg.__salt__['cephdisks.unused'] = lambda : []
            dg.__salt__['cephdisks.used'] = lambda : []

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

    def test_osds_per_device(self, test_fix):
        test_fix = test_fix(osds_per_device='3')
        assert test_fix.osds_per_device == '3'

    def test_osds_per_device_default(self, test_fix):
        test_fix = test_fix()
        assert test_fix.osds_per_device == ''

    def test_journal_size_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.journal_size == 0

    @pytest.fixture
    def inventory(self, available=True):
        def make_sample_data(available=available,
                             data_devices=10,
                             wal_devices=0,
                             db_devices=2,
                             human_readable_size_data='50.00 GB',
                             human_readable_size_wal='20.00 GB',
                             size=5368709121,
                             human_readable_size_db='20.00 GB'):
            factory = InventoryFactory()
            inventory_sample = []
            data_disks = factory.produce(
                pieces=data_devices,
                available=available,
                size=size,
                human_readable_size=human_readable_size_data)
            wal_disks = factory.produce(
                pieces=wal_devices,
                human_readable_size=human_readable_size_wal,
                rotational='0',
                model='ssd_type_model',
                size=size,
                available=available)
            db_disks = factory.produce(
                pieces=db_devices,
                human_readable_size=human_readable_size_db,
                rotational='0',
                size=size,
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
        with pytest.raises(dg.FilterNotSupported):
            test_fix._check_filter(dict(unknown='foo'))
            pytest.fail("Filter unknown is not supported")

    def test_list_devices(self):
        pass

    def test_c_v_commands(self, test_fix, inventory):
        inventory(available=True)
        test_fix = test_fix()

        ret = dg.c_v_commands(filter_args=test_fix.filter_args)
        assert ret == [
            'ceph-volume lvm batch --no-auto /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf /dev/sdg /dev/sdh /dev/sdi /dev/sdj /dev/sdk /dev/sdl /dev/sdm --yes --dmcrypt --block-wal-size 500 --block-db-size 500'
        ]

    def test_c_v_commands_bluestore_osds_per_device(self, test_fix, inventory):
        inventory()
        test_fix = test_fix(osds_per_device=3)
        ret = dg.c_v_commands(filter_args=test_fix.filter_args)
        assert ret == [
            'ceph-volume lvm batch --no-auto /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf /dev/sdg /dev/sdh /dev/sdi /dev/sdj /dev/sdk /dev/sdl /dev/sdm --yes --dmcrypt --block-wal-size 500 --block-db-size 500 --osds-per-device 3'
        ]

    def test_c_v_commands_filestore_osds_per_device(self, test_fix, inventory):
        inventory()
        test_fix = test_fix(disk_format='filestore', osds_per_device='3')
        ret = dg.c_v_commands(filter_args=test_fix.filter_args)
        assert ret == [
            'ceph-volume lvm batch /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf /dev/sdg /dev/sdh /dev/sdi /dev/sdj /dev/sdk --journal-size 500 --journal-devices /dev/sdl /dev/sdm --filestore --yes --dmcrypt --osds-per-device 3'
        ]

    def test_c_v_commands_filestore(self, test_fix, inventory):
        inventory()
        test_fix = test_fix(disk_format='filestore')
        ret = dg.c_v_commands(filter_args=test_fix.filter_args)
        assert ret == [
            'ceph-volume lvm batch /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf /dev/sdg /dev/sdh /dev/sdi /dev/sdj /dev/sdk --journal-size 500 --journal-devices /dev/sdl /dev/sdm --filestore --yes --dmcrypt'
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
            'ceph-volume lvm batch --no-auto /dev/sdb /dev/sdd /dev/sdf /dev/sdh /dev/sdj --db-devices /dev/sdl --yes',
            'ceph-volume lvm batch --no-auto /dev/sdc /dev/sde /dev/sdg /dev/sdi /dev/sdk --db-devices /dev/sdm --yes'
        ]

    def test_c_v_commands_external_wal_only(self, test_fix, inventory):
        inventory(wal_devices=2, db_devices=0)
        ret = dg.c_v_commands(
            filter_args={
                'data_devices': {
                    'rotational': '1'
                },
                'wal_devices': {
                    'rotational': '0'
                }
            })
        assert ret == {
            'wal_devices':
            '\nYou specified only wal_devices. If your intention was to\nhave dedicated WALs/DBs please specify it with the db_devices\nfilter. WALs will be colocated alongside the DBs.\nRead more about this here <link>.\n            '
        }

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
            'ceph-volume lvm batch --no-auto /dev/sdb /dev/sdd /dev/sdf /dev/sdh /dev/sdj --db-devices /dev/sdl --wal-devices /dev/sdn --yes',
            'ceph-volume lvm batch --no-auto /dev/sdc /dev/sde /dev/sdg /dev/sdi /dev/sdk --db-devices /dev/sdm --wal-devices /dev/sdo --yes'
        ]

    def test_c_v_commands_external_2_dbs_and_2_wals_osds_per_device(
            self, test_fix, inventory):
        """ Check if osds_per_device shows up in multi commands runs """
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
                },
                'osds_per_device': '3',
            })
        assert ret == [
            'ceph-volume lvm batch --no-auto /dev/sdb /dev/sdd /dev/sdf /dev/sdh /dev/sdj --db-devices /dev/sdl --wal-devices /dev/sdn --yes --osds-per-device 3',
            'ceph-volume lvm batch --no-auto /dev/sdc /dev/sde /dev/sdg /dev/sdi /dev/sdk --db-devices /dev/sdm --wal-devices /dev/sdo --yes --osds-per-device 3'
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
            'ceph-volume lvm batch --no-auto /dev/sdb /dev/sdd /dev/sdf /dev/sdh /dev/sdj --db-devices /dev/sdl --wal-devices /dev/sdn /dev/sdp --yes',
            'ceph-volume lvm batch --no-auto /dev/sdc /dev/sde /dev/sdg /dev/sdi /dev/sdk --db-devices /dev/sdm --wal-devices /dev/sdo --yes'
        ] == ret

    def test_c_v_commands_1TB_size_match(self, test_fix, inventory):
        inventory(
            data_devices=3,
            human_readable_size_data='9.10 TB',
            wal_devices=0,
            db_devices=0)
        ret = dg.c_v_commands(filter_args={
            'data_devices': {
                'size': '1TB:'
            },
            'encryption': 'true'
        })
        assert [
            'ceph-volume lvm batch --no-auto /dev/sdb /dev/sdc /dev/sdd --yes --dmcrypt',
        ] == ret

    def test_c_v_commands_11_data_external_3_dbs_and_1_wals(
            self, test_fix, inventory):
        inventory(data_devices=11, db_devices=3, wal_devices=1)
        ret = dg.c_v_commands(
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
        assert ret == {
            'wal_db_distribution':
            "\nWe can't guarantee proper wal/db distribution in this configuration.\nPlease make sure to have more/equal wal_devices than db_devices"
        }

    @patch(
        "srv.salt._modules.dg.Output.generate_c_v_commands",
        autospec=True,
        return_value=['ceph-volume foo'])
    @patch(
        "srv.salt._modules.dg.Output._check_for_old_profiles",
        autospec=True,
        return_value='error_message')
    def test_deploy_1(self, error_message, c_v_command, test_fix, inventory):
        """ old_profiles detected, expect to return error_message"""
        test_fix = test_fix()
        inventory()
        ret = dg.Output(filter_args=test_fix.filter_args).deploy()
        assert ret == error_message.return_value

    @patch(
        "srv.salt._modules.dg.Output.generate_c_v_commands",
        autospec=True,
        return_value={'error': 'error_message'})
    @patch(
        "srv.salt._modules.dg.Output._check_for_old_profiles",
        autospec=True,
        return_value='')
    def test_deploy_2(self, error_message, c_v_command, test_fix, inventory):
        """ c_v_commands contain a error dict """
        test_fix = test_fix()
        inventory()
        ret = dg.Output(filter_args=test_fix.filter_args).deploy()
        assert ret == c_v_command.return_value

    @patch(
        "srv.salt._modules.dg.Output.generate_c_v_commands",
        autospec=True,
        return_value=['foo, bar, baz'])
    @patch(
        "srv.salt._modules.dg.Output._check_for_old_profiles",
        autospec=True,
        return_value='')
    @patch("srv.salt._modules.dg.log")
    def test_deploy_3(self, log, error_message, c_v_command, test_fix,
                      inventory):
        """ c_v_commands contains list of non-ceph-volume commands"""
        test_fix = test_fix()
        inventory()
        ret = dg.Output(filter_args=test_fix.filter_args).deploy()
        log.error.assert_called_with(c_v_command.return_value[0])
        assert ret == []

    @patch(
        "srv.salt._modules.dg.Output.generate_c_v_commands",
        autospec=True,
        return_value=['foo', 'ceph-volume lvm foo'])
    @patch(
        "srv.salt._modules.dg.Output._check_for_old_profiles",
        autospec=True,
        return_value='')
    @patch("srv.salt._modules.dg.log")
    def test_deploy_4(self, log, error_message, c_v_command, test_fix,
                      inventory):
        """ c_v_commands contains list of mixed-ceph-volume commands"""
        test_fix = test_fix()
        inventory()
        dg.__salt__ = dict()
        dg.__salt__['helper.run'] = Mock()
        ret = dg.Output(filter_args=test_fix.filter_args).deploy()
        log.error.assert_called_with(c_v_command.return_value[0])
        dg.__salt__['helper.run'].assert_called_with('ceph-volume lvm foo')

    def test_check_for_old_profiles(self, test_fix, inventory):
        """ No pillar no bypass"""
        test_fix = test_fix()
        inventory()
        dg.__pillar__ = dict()
        ret = dg.Output(
            filter_args=test_fix.filter_args)._check_for_old_profiles()
        assert ret == ""

    def test_check_for_old_profiles_1(self, test_fix, inventory):
        """ pillar no bypass"""
        test_fix = test_fix()
        inventory()
        dg.__pillar__ = dict(ceph=dict(storage='foo'))
        ret = dg.Output(
            filter_args=test_fix.filter_args)._check_for_old_profiles()
        assert "You seem to have " in ret

    def test_check_for_old_profiles_2(self, test_fix, inventory):
        """ pillar and bypass """
        test_fix = test_fix()
        inventory()
        dg.__pillar__ = dict(ceph=dict(storage='foo'))
        outp = dg.Output(filter_args=test_fix.filter_args, bypass_pillar=True)
        ret = outp._check_for_old_profiles()
        assert ret == ''


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


class TestPublicMethods(object):
    @patch("srv.salt._modules.dg.Output", autospec=True)
    def test_report(self, output_mock):
        dg.report()
        output_mock.assert_called_once()

    @patch("srv.salt._modules.dg.Output", autospec=True)
    def test_c_v_commands(self, output_mock):
        dg.c_v_commands()
        output_mock.assert_called_once()

    @patch("srv.salt._modules.dg.Output", autospec=True)
    def test_deploy(self, output_mock):
        dg.deploy()
        output_mock.assert_called_once()

    @patch("srv.salt._modules.dg.report", autospec=True)
    def test_list(self, report_mock):
        dg.list_()
        report_mock.assert_called_once()
