import pytest
from mock import patch, call, Mock, PropertyMock
from srv.salt._modules import dg


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
        def make_sample_data(empty=empty, limit=0, disk_format='bluestore'):
            raw_sample_bluestore = {
                'target': 'data*',
                'format': 'bluestore',
                'data_devices': {
                    'size': '10G:29G',
                    'model': 'foo',
                    'vendor': '1x',
                    'limit': limit
                },
                'wal_devices': {
                    'model': 'fast'
                },
                'db_devices': {
                    'size': ':10G'
                },
                'db_slots': 5,
                'wal_slots': 5,
                'encryption': True,
            }
            raw_sample_filestore = {
                'target': 'data*',
                'format': 'filestore',
                'data_devices': {
                    'size': '10G:29G',
                    'model': 'foo',
                    'vendor': '1x',
                    'limit': limit
                },
                'journal_devices': {
                    'size': ':90G'
                },
                'journal_size': '500M',
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

    def test_db_slots_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.db_slots is False

    def test_wal_slots_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.wal_slots is 5

    def test_wal_slots_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.wal_slots is False

    def test_data_devices_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.data_device_attrs == {
            'model': 'foo',
            'size': '10G:29G',
            'vendor': '1x',
            'limit': 0
        }

    def test_data_devices_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.data_device_attrs == {}

    def test_db_devices_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.db_device_attrs == {
            'size': ':10G',
        }

    def test_db_devices_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.db_device_attrs == {}

    def test_wal_device_prop(self, test_fix):
        test_fix = test_fix()
        assert test_fix.wal_device_attrs == {
            'model': 'fast',
        }

    def test_journal_device_prop(self, test_fix):
        test_fix = test_fix(disk_format='filestore')
        assert test_fix.journal_device_attrs == {
            'size': ':90G',
        }

    def test_wal_device_prop_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.wal_device_attrs == {}

    @patch(
        'srv.salt._modules.dg.DriveGroup._filter_devices', new_callable=Mock)
    def test_db_devices(self, filter_mock, test_fix):
        test_fix = test_fix()
        test_fix.data_devices
        filter_mock.assert_called_once_with({
            'size': '10G:29G',
            'model': 'foo',
            'vendor': '1x'
        })

    @patch(
        'srv.salt._modules.dg.DriveGroup._filter_devices', new_callable=Mock)
    def test_wal_devices(self, filter_mock, test_fix):
        test_fix = test_fix()
        test_fix.wal_devices
        filter_mock.assert_called_once_with({'model': 'fast'})

    @patch(
        'srv.salt._modules.dg.DriveGroup._filter_devices', new_callable=Mock)
    def test_db_devices(self, filter_mock, test_fix):
        test_fix = test_fix()
        test_fix.db_devices
        filter_mock.assert_called_once_with({'size': ':10G'})

    @patch(
        'srv.salt._modules.dg.DriveGroup._filter_devices', new_callable=Mock)
    def test_journal_devices(self, filter_mock, test_fix):
        test_fix = test_fix(disk_format='filestore')
        test_fix.journal_devices
        filter_mock.assert_called_once_with({'size': ':90G'})

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
        assert test_fix.journal_size == '500M'

    def test_journal_size_empty(self, test_fix):
        test_fix = test_fix(empty=True)
        assert test_fix.journal_size == 0

    @pytest.fixture
    def inventory(self, available=True):
        def make_sample_data(available=available):
            inventory_sample = [
                {
                    'available': available,
                    'lvs': [],
                    'path': '/dev/vda',
                    'rejected_reasons': ['locked'],
                    'sys_api': {
                        'human_readable_size': '10.00 GB',
                        'locked': 1,
                        'model': 'modelA',
                        'nr_requests': '256',
                        'partitions': {
                            'vda1': {
                                'sectors': '41940992',
                                'sectorsize': 512,
                                'size': '10.00 GB',
                                'start': '2048'
                            }
                        },
                        'path': '/dev/vda',
                        'removable': '0',
                        'rev': '',
                        'ro': '0',
                        'rotational': '1',
                        'sas_address': '',
                        'sas_device_handle': '',
                        'scheduler_mode': 'mq-deadline',
                        'sectors': 0,
                        'sectorsize': '512',
                        'size': 10474836480.0,
                        'support_discard': '',
                        'vendor': 'samsung'
                    }
                },
                {
                    'available':
                    available,
                    'lvs': [{
                        'block_uuid':
                        'EbnVK1-chW6-NfEA-0RY4-dWjo-0AeL-b1V9hv',
                        'cluster_fsid':
                        'b9f1174e-fc02-4142-8816-172f20573c13',
                        'cluster_name':
                        'ceph',
                        'name':
                        'osd-block-d8a50e9b-2ea3-43a8-9617-2edccfee0c28',
                        'osd_fsid':
                        'd8a50e9b-2ea3-43a8-9617-2edccfee0c28',
                        'osd_id':
                        '0',
                        'type':
                        'block'
                    }],
                    'path':
                    '/dev/vdb',
                    'rejected_reasons': ['locked'],
                    'sys_api': {
                        'human_readable_size': '20.00 GB',
                        'locked': 1,
                        'model': 'modelB',
                        'nr_requests': '256',
                        'partitions': {
                            'vdb1': {
                                'sectors': '41940959',
                                'sectorsize': 512,
                                'size': '20.00 GB',
                                'start': '2048'
                            }
                        },
                        'path': '/dev/vdb',
                        'removable': '0',
                        'rev': '',
                        'ro': '0',
                        'rotational': '0',
                        'sas_address': '',
                        'sas_device_handle': '',
                        'scheduler_mode': 'mq-deadline',
                        'sectors': 0,
                        'sectorsize': '512',
                        'size': 21474836480.0,
                        'support_discard': '',
                        'vendor': 'intel'
                    }
                },
                {
                    'available':
                    available,
                    'lvs': [{
                        'block_uuid':
                        'ArrVrZ-5wIc-sDbu-gTkW-OFcc-uMy1-WuRbUZ',
                        'cluster_fsid':
                        'b9f1174e-fc02-4142-8816-172f20573c13',
                        'cluster_name':
                        'ceph',
                        'name':
                        'osd-block-ec36354c-110d-4273-8e47-f1fe78195860',
                        'osd_fsid':
                        'ec36354c-110d-4273-8e47-f1fe78195860',
                        'osd_id':
                        '4',
                        'type':
                        'block'
                    }],
                    'path':
                    '/dev/vdc',
                    'rejected_reasons': ['locked'],
                    'sys_api': {
                        'human_readable_size': '30.00 GB',
                        'locked': 1,
                        'model': 'modelC',
                        'nr_requests': '256',
                        'partitions': {
                            'vdc1': {
                                'sectors': '41940959',
                                'sectorsize': 512,
                                'size': '30.00 GB',
                                'start': '2048'
                            }
                        },
                        'path': '/dev/vdc',
                        'removable': '0',
                        'rev': '',
                        'ro': '0',
                        'rotational': '1',
                        'sas_address': '',
                        'sas_device_handle': '',
                        'scheduler_mode': 'mq-deadline',
                        'sectors': 0,
                        'sectorsize': '512',
                        'size': 32474836480.0,
                        'support_discard': '',
                        'vendor': 'micron'
                    }
                }
            ]
            self.raw_property = patch(
                'srv.salt._modules.dg.Inventory.raw',
                new_callable=PropertyMock,
                return_value=[])
            self.dg_property = patch(
                'srv.salt._modules.dg.Inventory.disks',
                new_callable=PropertyMock,
                return_value=inventory_sample)
            self.raw_property.start()
            self.dg_property.start()

            inv = dg.Inventory
            return inv

            self.raw_property.stop()
            self.dg_property.stop()

        return make_sample_data

    def test_filter_devices_2_size_min_max(self, test_fix, inventory):
        """ Test_fix's data_device_attrs is configured to take any disk from
        10G - 29G.  This means that in this test two out of three disks should
        appear in the output
        (Disks are 10G/20G/30G)
        """
        # initialize inventory once (scope is session by default)
        inventory()
        test_fix = test_fix()
        ret = test_fix._filter_devices(test_fix.data_device_attrs)
        assert len(ret) == 2

    def test_filter_devices_1_size_exact(self, test_fix, inventory):
        """
        Configure to only take disks with 10G
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size='10G'))
        assert len(ret) == 1

    def test_filter_devices_3_max(self, test_fix, inventory):
        """
        Configure to only take disks with a max of 30G
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size=':30G'))
        assert len(ret) == 3

    def test_filter_devices_1_max(self, test_fix, inventory):
        """
        Configure to only take disks with a max of 10G
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size=':10G'))
        assert len(ret) == 1

    def test_filter_devices_1_min(self, test_fix, inventory):
        """
        Configure to only take disks with a min of 10G
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size='10G:'))
        assert len(ret) == 3

    def test_filter_devices_2_min(self, test_fix, inventory):
        """
        Configure to only take disks with a min of 20G
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(size='20G:'))
        assert len(ret) == 2

    def test_filter_devices_1_model(self, test_fix, inventory):
        """
        Configure to only take disks with a model of modelA
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(model='modelA'))
        assert len(ret) == 1

    def test_filter_devices_3_model(self, test_fix, inventory):
        """
        Configure to only take disks with a model of model*(wildcard)
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(model='model'))
        assert len(ret) == 3

    def test_filter_devices_1_vendor(self, test_fix, inventory):
        """
        Configure to only take disks with a vendor of samsung
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(vendor='samsung'))
        assert len(ret) == 1

    def test_filter_devices_1_rotational(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 0
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(rotational='0'))
        assert len(ret) == 1

    def test_filter_devices_2_rotational(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        """
        test_fix = test_fix()
        ret = test_fix._filter_devices(dict(rotational='1'))
        assert len(ret) == 2

    def test_filter_devices_limit(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take two disks, but limit=1 is in place
        """
        test_fix = test_fix(limit=1)
        ret = test_fix._filter_devices(dict(rotational='1'))
        assert len(ret) == 1

    def test_filter_devices_empty_list_eq_matcher(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take two disks, but limit=1 is in place
        """
        inventory(available=False)
        test_fix = test_fix(limit=1)
        ret = test_fix._filter_devices(dict(rotational='1'))
        assert len(ret) == 0

    def test_filter_devices_empty_string_matcher(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take two disks, but limit=1 is in place
        """
        inventory(available=False)
        test_fix = test_fix(limit=1)
        ret = test_fix._filter_devices(dict(vendor='samsung'))
        assert len(ret) == 0

    def test_filter_devices_empty_size_matcher(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take two disks, but limit=1 is in place
        """
        inventory(available=False)
        test_fix = test_fix(limit=1)
        ret = test_fix._filter_devices(dict(size='10G:100G'))
        assert len(ret) == 0

    def test_filter_devices_empty_all_matcher(self, test_fix, inventory):
        """
        Configure to only take disks with a rotational flag of 1
        This should take two disks, but limit=1 is in place
        """
        inventory(available=False)
        test_fix = test_fix(limit=1)
        ret = test_fix._filter_devices(dict(all=True))
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
