import pytest
import mock
from srv.modules.runners import disk_led

grains_get_result = {"data1.ceph": ["vdf"]}
udev_links_result = {
    "data1.ceph": [
        "disk/by-id/wwn-0x4003c435a4d43cd8",
        "disk/by-path/pci-0000:00:15.0-ata-3",
        "disk/by-id/ata-SanDisk_X400_M.2_2280_512GB_26453645624767"
    ]
}
pillar_get_result = {
    "data1.ceph": {
        "ident": {
            "on": "xxx '{device_file}'",
            "off": "yyy '{device_file}'"
        },
        "fault": {
            "on": "aaa '{device_file}'",
            "off": "bbb '{device_file}'"
        }
    }
}
invalid_pillar_get_result = {"data1.ceph": ""}


class TestDiskLed:
    @mock.patch('srv.modules.runners.disk_led._process', autospec=True)
    @mock.patch('salt.client.LocalClient', autospec=True)
    def test_device_by_device_name(self, mock_localclient, mock_process):
        mock_localclient.return_value.cmd.side_effect = [
            grains_get_result, udev_links_result
        ]

        disk_led.device('data1.ceph', 'vdf', 'ident', 'on')
        mock_process.assert_called_once_with('data1.ceph', 'vdf', 'ident',
                                             'on')

    @mock.patch('srv.modules.runners.disk_led._process', autospec=True)
    @mock.patch('salt.client.LocalClient', autospec=True)
    def test_device_by_device_id(self, mock_localclient, mock_process):
        mock_localclient.return_value.cmd.side_effect = [
            grains_get_result, udev_links_result
        ]

        disk_led.device('data1.ceph',
                        'SanDisk_X400_M.2_2280_512GB_26453645624767', 'fault',
                        'off')
        mock_process.assert_called_once_with('data1.ceph', 'vdf', 'fault',
                                             'off')

    @mock.patch('srv.modules.runners.disk_led._process', autospec=True)
    @mock.patch('salt.client.LocalClient', autospec=True)
    def test_device_failure(self, mock_localclient, mock_process):
        mock_localclient.return_value.cmd.return_value = {}

        result = disk_led.device('data2.ceph', 'sdg', 'ident', 'off')
        assert not mock_process.called
        assert result == 'Could not find device "sdg" on host "data2.ceph"'

    @mock.patch('salt.client.LocalClient', autospec=True)
    def test_process_get_pillar_failed(self, mock_localclient):
        mock_localclient.return_value.cmd.return_value = []

        with pytest.raises(RuntimeError):
            disk_led._process('data1.ceph', 'vdf', 'ident', 'on')

    @mock.patch('salt.client.LocalClient', autospec=True)
    def test_process_invalid_config(self, mock_localclient):
        mock_localclient.return_value.cmd.return_value = invalid_pillar_get_result

        with pytest.raises(RuntimeError):
            disk_led._process('data1.ceph', 'vdf', 'ident', 'on')

    @mock.patch('srv.modules.runners.disk_led._cmd_run')
    @mock.patch('salt.client.LocalClient', autospec=True)
    def test_process(self, mock_localclient, mock_cmd_run):
        mock_localclient.return_value.cmd.return_value = pillar_get_result

        disk_led._process('data1.ceph', 'vdf', 'ident', 'on')
        mock_cmd_run.assert_called_once_with('data1.ceph', 'xxx \'/dev/vdf\'')

    def test_process_invalid_arg_1(self):
        with pytest.raises(AssertionError):
            disk_led._process('data1.ceph', '/dev/vdf', 'ident', 'on')

    def test_process_invalid_arg_1(self):
        with pytest.raises(AssertionError):
            disk_led._process('data1.ceph', 'sdb', 'foo', 'on')

    @mock.patch('salt.client.LocalClient', autospec=True)
    def test_cmd_run_failure(self, mock_localclient):
        mock_localclient.return_value.cmd.return_value = {
            'data1.ceph': {
                'ret': 'Command failed',
                'retcode': 1
            }
        }

        with pytest.raises(RuntimeError):
            disk_led._cmd_run('data1.ceph', 'foo bar')
