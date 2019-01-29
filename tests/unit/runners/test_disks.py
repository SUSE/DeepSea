import pytest
from mock import patch, call, Mock, PropertyMock
from srv.modules.runners import disks


class TestDriveGroups_Disks(object):
    def test_target(self):
        dgo = disks.DriveGroup('default', {'target': 'test_target'})
        assert dgo.target() == 'test_target'

    def test_target_not_present(self):
        with pytest.raises(disks.NoTargetFound):
            dgo = disks.DriveGroup('default', {'target': ''})
            dgo.target()

    def test_target_is_not_string(self):
        with pytest.raises(disks.NoTargetFound):
            dgo = disks.DriveGroup('default', {'target': int(9)})
            dgo.target()

    def test_filter_args(self):
        filter_args = {'target': '', 'data_devices': {'size': '50G'}}
        dgo = disks.DriveGroup('default', filter_args)
        assert dgo.filter_args() == filter_args

    def test_filter_args_not_present(self):
        with pytest.raises(disks.NoFilterFound):
            dgo = disks.DriveGroup('default', {})
            dgo.filter_args()

    def test_filter_args_is_not_dict(self):
        with pytest.raises(disks.NoFilterFound):
            dgo = disks.DriveGroup('default', str('raises'))
            dgo.filter_args()


class TestDriveGroup_Disks(object):

    default_spec = {
        'default': {
            'target': 'data*',
            'data_devices': {
                'size': '50G'
            }
        },
        'non_default': {
            'target': 'other*',
            'data_devices': {
                'rotational': 1
            },
            'db_devices': {
                'size': ':50G'
            },
            'wal_devices': {
                'size': ':50G'
            }
        }
    }

    @pytest.fixture(scope='class')
    def drive_groups_fixture(self, **kwargs):
        def make_drive_group_object(**kwargs):
            drive_groups = kwargs.get('drive_groups', self.default_spec)
            self.load_drive_group = patch(
                'srv.modules.runners.disks.DriveGroups._load_drive_group_file',
                return_value=drive_groups)
            self.localclient = patch(
                'srv.modules.runners.disks.salt.client.LocalClient')
            self.ldg_mock = self.load_drive_group.start()
            self.local_client_mock = self.localclient.start()
            return disks.DriveGroups(**kwargs)
            self.ldg_mock = self.get_drive_group.stop()
            self.local_client_mock = self.localclient.stop()

        return make_drive_group_object

    def test_class_defaults(self, drive_groups_fixture):
        dgo = drive_groups_fixture()
        assert dgo.dry_run is False
        assert dgo.drive_groups_path == '/srv/salt/ceph/configuration/files/drive_groups.yml'

    def test_class_non_default(self, drive_groups_fixture):
        dgo = drive_groups_fixture(dry_run=True)
        assert dgo.dry_run is True

    def test_get_drive_groups(self, drive_groups_fixture):
        dgo = drive_groups_fixture()
        assert dgo.drive_groups == self.default_spec

    def test_get_drive_groups_empty(self, drive_groups_fixture):
        with pytest.raises(RuntimeError):
            drive_groups_fixture(drive_groups={})

    def test_get_drive_groups_not_dict(self, drive_groups_fixture):
        with pytest.raises(RuntimeError):
            drive_groups_fixture(drive_groups=str('not a dict'))

    @patch('srv.modules.runners.disks.destroyed')
    @patch('srv.modules.runners.disks.DriveGroup')
    def test_call_out(self, drive_group, destroyed_mock, drive_groups_fixture):
        dgo = drive_groups_fixture()
        ret = dgo.call_out('test')

        destroyed_mock.return_value = {'data1': [1, 2, 3]}

        call0 = (call('default', {
            'target': 'data*',
            'data_devices': {
                'size': '50G'
            }
        }))
        assert call0 == drive_group.call_args_list[0]

        call1 = call(
            'non_default', {
                'target': 'other*',
                'data_devices': {
                    'rotational': 1
                },
                'db_devices': {
                    'size': ':50G'
                },
                'wal_devices': {
                    'size': ':50G'
                }
            })
        assert call1 == drive_group.call_args_list[1]
        # maybe that would've been enough
        assert len(self.default_spec) == len(drive_group.call_args_list)
        assert isinstance(ret, list)

    @patch('srv.modules.runners.disks.destroyed')
    def test_call(self, destroyed_mock, drive_groups_fixture):
        dgo = drive_groups_fixture()
        destroyed_mock.return_value = {'data1': [1, 2, 3]}
        dgo.call('target*', {'args'}, 'test_command')
        dgo.local_client.cmd.assert_called_with(
            'target*',
            'dg.test_command',
            expr_form='compound',
            kwarg={
                'filter_args': {'args'},
                'dry_run': False,
                'destroyed_osds': {
                    'data1': [1, 2, 3]
                }
            })

    @patch('srv.modules.runners.disks.destroyed')
    def test_call_dry(self, destroyed_mock, drive_groups_fixture):
        dgo = drive_groups_fixture(dry_run=True)
        destroyed_mock.return_value = {'data1': [1, 2, 3]}
        dgo.call('target*', {'args'}, 'test_command')
        dgo.local_client.cmd.assert_called_with(
            'target*',
            'dg.test_command',
            expr_form='compound',
            kwarg={
                'filter_args': {'args'},
                'dry_run': True,
                'destroyed_osds': {
                    'data1': [1, 2, 3]
                }
            })
