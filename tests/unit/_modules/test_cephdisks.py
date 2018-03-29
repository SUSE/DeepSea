import pytest
import sys
sys.path.insert(0, 'srv/salt/_modules')
from srv.salt._modules import cephdisks, helper
from mock import MagicMock, patch, mock_open, mock, create_autospec
from tests.unit.helper.output import OutputHelper


class TestHardwareDetections():
    '''
    This class contains a set of functions that test srv.salt._modules
    '''
    @pytest.fixture(scope='class')
    def hwd(self):
        """
        Patching hw_detection_method in the __init__ function
        of HardwareDetections to allow sudoless test execution
        Patched method are tested separately.

        scope: class
        return: instance of 
                <class srv.salt._modules.cephdisks.HardwareDetections>
        """
        self.hw_detection_method = patch('srv.salt._modules.cephdisks.HardwareDetections._find_detection_tool')
        self.hw_dtctr = self.hw_detection_method.start()
        self.hw_dtctr.return_value = '/a/valid/path'
        def pass_through(*args, **kwargs):
            return args[0]                
        mock_func = create_autospec(lambda x: x, side_effect=pass_through)
        cephdisks.__salt__ = {'helper.convert_out': mock_func}
        yield cephdisks
        self.hw_detection_method.stop()


    @pytest.fixture(scope='module')
    def output_helper(self):
        yield OutputHelper()

    def test_which_success(self, hwd):
        """
        Given we have that tool, return the full path
        """
        assert hwd.HardwareDetections()._which('cat') is not None

    def test_which_failure(self, hwd):
        """
        Given we do not have that tool installed or privileges.
        But tell which to not raise an error.
        """
        assert hwd.HardwareDetections()._which('notthere', failhard=False) is None

    def test_which_failure_explicit_raise(self, hwd):
        """
        Given we do not have that tool installed or privileges. 
        And explicitly tell `which` so.
        """
        with pytest.raises(Exception):
            hwd.HardwareDetections()._which('notthere', failhard=True)

    def test_which_failure_raise(self, hwd):
        """
        Given we do not have that tool installed or privileges.
        And don't explicitly tell `which` so.
        """
        with pytest.raises(Exception):
            hwd.HardwareDetections()._which('notthere')

    def test_which_failure_raise_param_error(self, hwd):
        """
        Given we do not have that tool installed or privileges.
        And tell which the wrong type(argument).
        """
        with pytest.raises(Exception):
            hwd.HardwareDetections()._which('notthere', 'StringTrue')

    def test_is_rotational(self, hwd):
        read_data = "1"
        with patch("srv.salt._modules.cephdisks.open", mock_open(read_data=read_data)) as mock_file:
            expect = read_data
            out = hwd.HardwareDetections()._is_rotational('disk/in/question')
            assert expect == out

    def test_is_rotational_not(self, hwd):
        read_data = "0"
        with patch("srv.salt._modules.cephdisks.open", mock_open(read_data=read_data)) as mock_file:
            expect = read_data
            out = hwd.HardwareDetections()._is_rotational('disk/in/question')
            assert expect == out

    def test_is_removable_not(self, hwd):
        read_data = "0"
        with patch("srv.salt._modules.cephdisks.open", mock_open(read_data=read_data)) as mock_file:
            expect = None
            out = hwd.HardwareDetections()._is_removable('disk/in/question')
            assert expect == out

    def test_is_removable(self, hwd):
        read_data = "1"
        with patch("srv.salt._modules.cephdisks.open", mock_open(read_data=read_data)) as mock_file:
            expect = True
            out = hwd.HardwareDetections()._is_removable('disk/in/question')
            assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test_return_device_bus_id_fail(self, po, wm, hwd, output_helper):
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.lsscsi_with_raid_fail['stdout']
        expect = output_helper.lsscsi_with_raid_fail['expected_return']
        out = hwd.HardwareDetections()._return_device_bus_id(output_helper.lsscsi_with_raid_fail['device'])
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test_return_device_bus_id_success(self, po, wm, hwd, output_helper):
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.lsscsi_with_raid_success['stdout']
        expect = output_helper.lsscsi_with_raid_success['expected_return']
        out = hwd.HardwareDetections()._return_device_bus_id(output_helper.lsscsi_with_raid_success['device'])
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test__osd_no_osd(self, po, wm, hwd, output_helper):
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.sgdisk_invalid['stdout']
        expect = output_helper.sgdisk_invalid['expected_return']
        out = hwd.HardwareDetections()._osd('/dev/sda', ['1', '2', '3', '4'])
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test__osd_is_osd_data(self, po, wm, output_helper, hwd):
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.sgdisk_valid_osd_data['stdout']
        expect = output_helper.sgdisk_valid_osd_data['expected_return']
        out = hwd.HardwareDetections()._osd('/dev/sdb', ['1', '2', '3', '4'])
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test__osd_is_osd_journal(self, po, wm, output_helper, hwd):
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.sgdisk_valid_journal['stdout']
        expect = output_helper.sgdisk_valid_journal['expected_return']
        out = hwd.HardwareDetections()._osd('/dev/sdn', ['1', '2', '3', '4'])
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test__hwinfo(self, po, wm, output_helper, hwd):
        """ 
        No negative test needed here.
        Won't test hwinfo itself here
        """
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.hwinfo['stdout']
        args = output_helper.hwinfo['function_args']
        out = hwd.HardwareDetections()._hwinfo(args)
        expect = output_helper.hwinfo['expected_return']
        assert out != {}
        assert type(out) == dict
        assert expect == out 

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._return_device_bus_id')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test__query_disktype_hdd(self, po, ret_bus_id, wm, hwd, output_helper):
        """ Assume ret_bus_id has some value """
        wm.return_value = '/valid/path'
        ret_bus_id.return_value = True
        po.return_value.returncode = 0
        po.return_value.stdout = output_helper.smartctl_spinner_valid['stdout']
        expect = output_helper.smartctl_spinner_valid['expected_return']
        out = hwd.HardwareDetections()._query_disktype('sda', {'controller_name': 'megaraid'}, 'base')
        assert expect, out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._return_device_bus_id')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test__query_disktype_ssd(self, po, ret_bus_id, wm, output_helper, hwd):
        """ Assume ret_bus_id has some value """
        wm.return_value = '/valid/path'
        ret_bus_id.return_value = True
        po.return_value.returncode = 0
        po.return_value.stdout = output_helper.smartctl_solid_state_valid['stdout']
        expect = output_helper.smartctl_solid_state_valid['expected_return']
        out = hwd.HardwareDetections()._query_disktype('sdn', {'controller_name': 'megaraid'}, 'base')
        assert expect == out 

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._return_device_bus_id')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._is_rotational')
    def test__query_disktype_smartctl_failure(self, ir, po, ret_bus_id, wm, output_helper, hwd):
        """ Assume ret_bus_id returns True """
        wm.return_value = '/valid/path'
        ret_bus_id.return_value = True
        po.return_value.returncode = 1
        po.return_value.stdout = output_helper.smartctl_invalid['stdout']
        out = hwd.HardwareDetections()._query_disktype('sdn', {'controller_name': 'megaraid'}, 'base')
        assert ir.called

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._return_device_bus_id')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._is_rotational')
    def test__query_disktype_invalid(self, ir, po, ret_bus_id, wm, output_helper, hwd):
        """ Assume ret_bus_id returns True """
        wm.return_value = '/valid/path'
        ret_bus_id.return_value = True
        po.return_value.returncode = 0
        po.return_value.stdout = output_helper.smartctl_invalid['stdout']
        out = hwd.HardwareDetections()._query_disktype('sdn', {'controller_name': 'megaraid'}, 'base')
        expect = output_helper.smartctl_invalid['expected_return']
        assert expect == out


    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._return_device_bus_id')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._is_rotational')
    def test__query_disktype_drop_at_bus_id(self, ir, ret_bus_id, wm, hwd):
        """ Assume ret_bus_id False """
        wm.return_value = '/valid/path'
        ret_bus_id.return_value = False
        hwd.HardwareDetections()._query_disktype('sdn', {'controller_name': 'megaraid'}, 'base')
        assert ir.called is True

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._return_device_bus_id')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._is_rotational')
    def test__query_disktype_except_block(self, ir, po, ret_bus_id, wm, hwd):
        """ Assume ret_bus_id returns True"""
        wm.return_value = '/valid/path'
        ret_bus_id.return_value = True
        po.side_effect = StandardError
        hwd.HardwareDetections()._query_disktype('sdn', {'controller_name': 'megaraid'}, 'base')
        assert ir.called is True
    
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._hw_raid_ctrl_detection')
    def test_hw_raid_ctrl_detection_custom_hwraid(self, hw_raid_detection):
        """ No hw_raid_name is set """
        hwd = cephdisks.HardwareDetections(hw_raid=True)
        hwd._detect_raidctrl()
        assert hw_raid_detection.called is True

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._hw_raid_ctrl_detection')
    def test_hw_raid_ctrl_detection_custom_hwraid_controller_name(self, hw_raid_detection):
        """ hw_raid_name is set """
        hwd = cephdisks.HardwareDetections(hw_raid=True, raid_controller_name='3ware')
        out = hwd._detect_raidctrl()
        expect = {'raidtype': 'hardware', 'controller_name': '3ware'}
        assert out == expect

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._hw_raid_ctrl_detection')
    def test_hw_raid_ctrl_detection(self, hw_raid_detection):
        """ No hw_raid_name, no raidtype """
        hwd = cephdisks.HardwareDetections()
        # TRAVIS SAYS THIS IS NOT CALLED
        hwd._detect_raidctrl()
        assert hw_raid_detection.called is True 

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._hw_raid_ctrl_detection')
    def test_hw_raid_ctrl_detection_custom_software(self, hw_raid_detection):
        """ sw_raid is set """
        hwd = cephdisks.HardwareDetections(sw_raid=True)
        expect = {'raidtype': 'software'}
        out = hwd._detect_raidctrl()
        assert out == expect

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test_hw_raid_ctrl_detection_megaraid(self, po, wm, output_helper, hwd): 
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.lspci_out_hwraid_megaraid['stdout']
        expect = {}
        expect['controller_name'] = output_helper.lspci_out_hwraid_megaraid['controller_name']
        expect['raidtype'] = output_helper.lspci_out_hwraid_megaraid['raidtype']
        out = hwd.HardwareDetections()._hw_raid_ctrl_detection()
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test_hw_raid_ctrl_detection_aacraid(self, po, wm, output_helper, hwd): 
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.lspci_out_hwraid_aacraid['stdout']
        expect = {}
        expect['controller_name'] = output_helper.lspci_out_hwraid_aacraid['controller_name']
        expect['raidtype'] = output_helper.lspci_out_hwraid_aacraid['raidtype']
        out = hwd.HardwareDetections()._hw_raid_ctrl_detection()
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test_hw_raid_ctrl_detection_3ware(self, po, wm, output_helper, hwd): 
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.lspci_out_hwraid_3ware['stdout']
        expect = {}
        expect['controller_name'] = output_helper.lspci_out_hwraid_3ware['controller_name']
        expect['raidtype'] = output_helper.lspci_out_hwraid_3ware['raidtype']
        out = hwd.HardwareDetections()._hw_raid_ctrl_detection()
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test_hw_raid_ctrl_detection_areca(self, po, wm, output_helper, hwd):
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.lspci_out_hwraid_areca['stdout']
        expect = {}
        expect['controller_name'] = output_helper.lspci_out_hwraid_areca['controller_name']
        expect['raidtype'] = output_helper.lspci_out_hwraid_areca['raidtype']
        out = hwd.HardwareDetections()._hw_raid_ctrl_detection()
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test_hw_raid_ctrl_detection_cciss(self, po, wm, output_helper, hwd):
        wm.return_value = '/valid/path'
        po.return_value.stdout = output_helper.lspci_out_hwraid_cciss['stdout']
        expect = {}
        expect['controller_name'] = output_helper.lspci_out_hwraid_cciss['controller_name']
        expect['raidtype'] = output_helper.lspci_out_hwraid_cciss['raidtype']
        out = hwd.HardwareDetections()._hw_raid_ctrl_detection()
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test_hw_raid_ctrl_detection_none(self, po, wm, hwd):
        wm.return_value = '/valid/path'
        po.return_value.stdout = ["empty"]
        expect = {}
        expect['controller_name'] = None
        expect['raidtype'] = None
        out = hwd.HardwareDetections()._hw_raid_ctrl_detection()
        assert expect == out

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which')
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._udevadm')
    def test__lshw(self, udev_mock, po, wm, output_helper, hwd):
        wm.return_value = '/valid/path'
        udev_mock.return_value = "mocked_udevadm_out"
        process_mock = mock.Mock()
        attrs = {'communicate.return_value': (output_helper.lshw_out['stdout'], 'error')}
        process_mock.configure_mock(**attrs)
        po.return_value = process_mock 
        out = hwd.HardwareDetections()._lshw()
        expected = output_helper.lshw_out['expected_return']
        assert out == expected
        
    @mock.patch('srv.salt._modules.cephdisks.Popen')
    def test__udevadm(self, po, output_helper, hwd):
        # additional test for virtualized env?
        process_mock = mock.Mock()
        attrs = {'communicate.return_value': (output_helper._udevadm_out['stdout'], 'error')}
        process_mock.configure_mock(**attrs)
        po.return_value = process_mock 
        out = hwd.HardwareDetections()._udevadm('/dev/sda')
        expected = output_helper._udevadm_out['expected_return']
        assert out == expected


class TestHardwareDetections_2():
    """ 
    This class contains a set of functions that test srv.salt._modules
    with a different set of patches that could not be tested in class1
    """
    
    @pytest.fixture(scope='class')
    def hwd(self):
        """
        HardwareDetections calls a method that requires root
        in order to return a correct path. Mocking only once 
        to be able to test the function in question later on.
        """
        self.hw_detection_method = patch('srv.salt._modules.cephdisks.HardwareDetections._which')
        self.hw_dtctr = self.hw_detection_method.start()
        self.hw_dtctr.return_value = '/a/valid/path'
        self.hwd = cephdisks.HardwareDetections()
        yield cephdisks.HardwareDetections()
        self.hw_dtctr = self.hw_detection_method.stop()

    @pytest.fixture(scope='module')
    def output_helper(self):
        yield OutputHelper()

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which', side_effect=[True])
    def test_detection_tool_hwinfo(self, which_mocked, hwd):
        out =  hwd._find_detection_tool()
        assert which_mocked.called is True
        assert out is not None

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which', side_effect=[False, True])
    def test_detection_tool_lshw(self, which_mocked, hwd):
        out = hwd._find_detection_tool()
        assert which_mocked.called is True
        assert callable(out) is True
        assert out is not None

    @mock.patch('srv.salt._modules.cephdisks.HardwareDetections._which', side_effect=[False, False])
    def test_detection_tool_none(self, which_mocked, hwd):
        pytest.raises(Exception, hwd._find_detection_tool)

    def test_detection_tool_overwrite_hwinfo(self):
        hwd = cephdisks.HardwareDetections(detection_method='hwinfo')
        assert callable(hwd.detection_method) is True

    def test_detection_tool_overwrite_lshw(self):
        hwd = cephdisks.HardwareDetections(detection_method='lshw')
        assert callable(hwd.detection_method) is True
