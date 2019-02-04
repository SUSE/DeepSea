from mock import patch, MagicMock, mock_open
import pytest
from pyfakefs import fake_filesystem as fake_fs

from srv.modules.runners import changed

fs = fake_fs.FakeFilesystem()
f_os = fake_fs.FakeOsModule(fs)
f_open = fake_fs.FakeFileOpen(fs)
base_dir = '/srv/salt/ceph/configuration/files/'
conf_dir = '/srv/salt/ceph/configuration/files/ceph.conf.d/'
checksum_dir = '/srv/salt/ceph/configuration/files/ceph.conf.checksum/'


class TestChanged():
    """
    Testing 'changed' runner
    """

    @pytest.fixture(scope='class')
    def cfg(self):
        with patch('srv.modules.runners.changed.salt.client', new_callable=MagicMock):
            yield changed.Config

    @pytest.fixture(scope='class')
    def role(self):
        with patch('srv.modules.runners.changed.salt.client', new_callable=MagicMock):
            yield changed.Role

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('builtins.open', new=f_open)
    @patch('srv.modules.runners.changed.hashlib')
    def test_create_checksum(self, hashlib_mock, cfg, role):
        fs.CreateFile("{}/{}".format(conf_dir, 'rgw.conf'), contents="foo=bar")
        cfg = cfg(role=role(role_name='rgw'))
        ret = cfg.create_checksum()
        assert isinstance(ret, MagicMock) is True

    @patch('srv.modules.runners.changed.log')
    def test_create_checksum_no_files(self, log_mock, cfg, role):
        cfg = cfg(role=role(role_name='rgw'))
        ret = cfg.create_checksum()
        assert ret is None

    @patch('srv.modules.runners.changed.log')
    def test_write_checksum(self, log_mock, cfg, role):
        fs.CreateFile("{}/{}".format(checksum_dir, 'rgw.conf'), contents="foo=bar")
        cfg = cfg(role=role(role_name='rgw'))
        m = mock_open()
        with patch('builtins.open', m, create=True):
            ret = cfg.write_checksum('0b0b0b0b0b0b0b0b0b0b0')
            log_mock.debug.assert_called()
            m.assert_called_once_with('/srv/salt/ceph/configuration/files/ceph.conf.checksum/rgw.conf', 'w')
            m().write.assert_called_once_with('0b0b0b0b0b0b0b0b0b0b0')
            fs.RemoveFile('/srv/salt/ceph/configuration/files/ceph.conf.checksum/rgw.conf')

    @patch('os.path.exists', new=f_os.path.exists)
    @patch('srv.modules.runners.changed.log')
    @patch('srv.modules.runners.changed.open')
    def test_read_checksum(self, open_mock, log_mock, cfg, role):
        fs.CreateFile("{}/{}".format(checksum_dir, 'rgw.conf'), contents="foo=bar")
        cfg = cfg(role=role(role_name='rgw'))
        ret = cfg.read_checksum()
        open_mock.assert_called_with('/srv/salt/ceph/configuration/files/ceph.conf.checksum/rgw.conf', 'r')
        log_mock.debug.assert_called()

    @patch('srv.modules.runners.changed.log')
    def test_read_checksum_no_file(self, log_mock, cfg, role):
        cfg = cfg(role=role(role_name='rgw'))
        ret = cfg.read_checksum()
        log_mock.debug.assert_called()
        assert ret is None

    def test_dependencies(self, cfg, role):
        cfg = cfg(role=role(role_name='rgw'))
        ret = cfg.role.dependencies
        assert type(ret) is list

    @patch('srv.modules.runners.changed.Config.create_checksum')
    @patch('srv.modules.runners.changed.Config.read_checksum')
    @patch('srv.modules.runners.changed.log')
    def test_has_changes_eq(self, log_mock, read_cs_mock, create_cs_mock, cfg, role):
        cfg = cfg(role=role(role_name='rgw'))
        read_cs_mock.return_value = "0b0b"
        create_cs_mock.return_value = "0b0b"
        ret = cfg.has_change()
        log_mock.info.assert_called()
        assert ret is False

    @patch('srv.modules.runners.changed.Config.create_checksum')
    @patch('srv.modules.runners.changed.Config.read_checksum')
    @patch('srv.modules.runners.changed.Config.write_checksum')
    @patch('srv.modules.runners.changed.log')
    def test_has_changes_not_eq(self, log_mock, write_cs_mock, read_cs_mock, create_cs_mock, cfg, role):
        cfg = cfg(role=role(role_name='rgw'))
        read_cs_mock.return_value = "1b1b"
        create_cs_mock.return_value = "0b0b"
        ret = cfg.has_change()
        write_cs_mock.assert_called_once_with('0b0b')
        log_mock.info.assert_called()
        assert ret is True

    @patch('srv.modules.runners.changed.Config.create_checksum')
    @patch('srv.modules.runners.changed.Config.read_checksum')
    @patch('srv.modules.runners.changed.log')
    def test_has_changes_no_current_or_prev_cs(self, log_mock, read_cs_mock, create_cs_mock, cfg, role):
        cfg = cfg(role=role(role_name='rgw'))
        read_cs_mock.return_value = None
        create_cs_mock.return_value = None
        ret = cfg.has_change()
        log_mock.debug.assert_called()
        assert ret is False

    @patch('srv.modules.runners.changed.Config.create_checksum')
    @patch('srv.modules.runners.changed.Config.read_checksum')
    @patch('srv.modules.runners.changed.log')
    @patch('srv.modules.runners.changed.Config.write_checksum')
    def test_has_changes_no_current_cs(self, write_cs_mock, log_mock, read_cs_mock, create_cs_mock, cfg, role):
        cfg = cfg(role=role(role_name='rgw'))
        read_cs_mock.return_value = None
        create_cs_mock.return_value = 'NotNone'
        ret = cfg.has_change()
        log_mock.debug.assert_called()
        assert write_cs_mock.called is True
        assert ret is True

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.changed.requires_conf_change')
    def test_rgw(self, rcc_mock, salt_mock):
        rcc_mock.assert_called

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.changed.requires_conf_change')
    def test_mds(self, rcc_mock, salt_mock):
        rcc_mock.assert_called

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.changed.requires_conf_change')
    def test_mgr(self, rcc_mock, salt_mock):
        changed.mgr()
        rcc_mock.assert_called

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.changed.requires_conf_change')
    def test_osd(self, rcc_mock, salt_mock):
        changed.osd()
        rcc_mock.assert_called

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.changed.requires_conf_change')
    def test_mon(self, rcc_mock, salt_mock):
        changed.mon()
        rcc_mock.assert_called

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.changed.requires_conf_change')
    def test_global_(self, rcc_mock, salt_mock):
        changed.global_()
        rcc_mock.assert_called

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.changed.requires_conf_change')
    def test_client(self, rcc_mock, salt_mock):
        changed.client()
        rcc_mock.assert_called

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.changed.requires_conf_change')
    def test_igw(self, rcc_mock, salt_mock):
        changed.igw()
        rcc_mock.assert_called
