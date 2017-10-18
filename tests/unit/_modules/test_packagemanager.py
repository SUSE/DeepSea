import pytest
from srv.salt._modules.packagemanager import PackageManager, Zypper, Apt
from mock import MagicMock, patch, mock


class TestPackageManager():
    '''
    This class contains a set of functions that test srv.salt._modules.packagemanager
    '''

    @mock.patch('srv.salt._modules.packagemanager.linux_distribution')
    def test_PackageManager_opensuse(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('opensuse', 42.1, 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Zypper) is True

    @mock.patch('srv.salt._modules.packagemanager.linux_distribution')
    def test_PackageManager_suse(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('SUSE', '12.2', 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Zypper) is True

    @mock.patch('srv.salt._modules.packagemanager.linux_distribution')
    def test_PackageManager_debian(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('debian', '8', 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Apt) is True

    @mock.patch('srv.salt._modules.packagemanager.linux_distribution')
    def test_PackageManager_ubuntu(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('ubuntu', '23', 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Apt) is True

    @mock.patch('srv.salt._modules.packagemanager.linux_distribution')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test_not_implemented(self, po, dist_return):
        """
        Your platform is not supported
        """
        dist_return.return_value = ('ScientificLinux', '42.2', 'x86_64')
        with pytest.raises(ValueError) as excinfo:
            PackageManager()
        excinfo.match('Failed to detect PackageManager for OS.*')


class TestZypper():

    @pytest.fixture(scope='class')
    def zypp(self):
        """
        Fixture to always get Zypper.
        """
        self.linux_dist = patch('srv.salt._modules.packagemanager.linux_distribution')
        self.lnx_dist_object = self.linux_dist.start()
        self.lnx_dist_object.return_value = ('opensuse', '42.2', 'x86_64')
        args = {'debug': False, 'kernel': False, 'reboot': False}
        yield PackageManager(**args).pm
        self.linux_dist.stop()

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__refresh(self, po, zypp):
        """
        Refresh method
        """
        zypp._refresh()
        assert po.called is True

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__updates_needed_not(self, po, zypp):
        """
        No pending updates.
        :returns bool(False)
        """
        po.return_value.returncode = 0
        ret = zypp._updates_needed()
        assert po.called is True
        assert ret is False

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__updates_needed(self, po, zypp):
        """
        Updates are pending.
        :returns bool(True)
        """
        po.return_value.returncode = 1
        ret = zypp._updates_needed()
        assert po.called is True
        assert ret is True

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__patches_needed(self, po, zypp):
        """
        Patches are pending.
        :returns bool(True)
        """
        po.return_value.returncode = 100
        ret = zypp._patches_needed()
        assert po.called is True
        assert ret is True

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__patches_needed_not(self, po, zypp):
        """
        No patches are pending.
        :returns bool(True)
        """
        po.return_value.returncode = 0
        ret = zypp._patches_needed()
        assert po.called is True
        assert ret is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Zypper._updates_needed')
    def test__handle_updates_present(self, updates_needed, po, _reboot, zypp):
        """
        Given there are updates pending.
        Zypper returns 102 which should lead to a reboot.
        """
        updates_needed.return_value = True
        po.return_value.returncode = 102
        po.return_value.communicate.return_value = ("packages out", "error")
        zypp._handle()
        assert updates_needed.called is True
        assert po.called is True
        assert _reboot.called is True

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Zypper._updates_needed')
    def test__handle_updates_not_present(self, updates_needed, po, _reboot, zypp):
        """
        Given there are no updates pending.
        Zypper returns 102 which should lead to a reboot.
        But the reboot block should not be reached, therefore no reboot.
        """
        updates_needed.return_value = False
        po.return_value.returncode = 102
        po.return_value.communicate.return_value = ("packages out", "error")
        zypp._handle()
        assert updates_needed.called is True
        assert po.called is False
        assert _reboot.called is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Zypper._patches_needed')
    def test__handle_patches(self, patches_needed, po, _reboot, zypp):
        """
        Given there are no updates patches.
        Zypper returns 102 which should lead to a reboot.
        But the reboot block should not be reached, therefore no reboot.
        """
        patches_needed.return_value = False
        po.return_value.returncode = 102
        po.return_value.communicate.return_value = ("packages out", "error")
        zypp._handle(strat='patch')
        assert patches_needed.called is True
        assert po.called is False
        assert _reboot.called is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__handle_migration(self, po, _reboot, zypp):
        """
        Given there is a no migration available.
        Zypper returns 0 which should not lead to a reboot.
        """
        po.return_value.returncode = 0
        po.return_value.communicate.return_value = ("packages out", "error")
        zypp._migrate()
        assert po.called is True
        assert _reboot.called is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__handle_migration_with_reboot(self, po, _reboot, zypp):
        """
        Given there is a migration available.
        Zypper returns 102 which should lead to a reboot.
        But the reboot block should be reached.
        """
        po.return_value.returncode = 102
        po.return_value.communicate.return_value = ("packages out", "error")
        zypp._migrate()
        assert po.called is True
        assert _reboot.called is True

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Zypper._updates_needed')
    def test__handle_updates_present_failed_99(self, updates_needed, po, _reboot, zypp):
        """
        Given there are updates pending.
        The returncode is > 0 but < 100.
        According to zypper this indicates an issue. -> Raise
        """
        updates_needed.return_value = True
        po.return_value.returncode = 99
        po.return_value.communicate.return_value = ("packages out", "error")
        with pytest.raises(Exception) as excinfo:
            zypp._handle()
            assert po.called is True
            assert _reboot.called is False
        excinfo.match('Zypper failed with*')

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Zypper._updates_needed')
    def test__handle_updates_present_failed_1(self, updates_needed, po, _reboot, zypp):
        """
        Given there are updates pending.
        The returncode is > 0 but < 100.
        According to zypper this indicates an issue. -> Raise
        """
        updates_needed.return_value = True
        po.return_value.returncode = 1
        po.return_value.communicate.return_value = ("packages out", "error")
        with pytest.raises(Exception) as excinfo:
            zypp._handle()
            assert po.called is True
            assert _reboot.called is False
        excinfo.match('Zypper failed with*')

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__handle_unknown_param(self, po, _reboot, zypp):
        """
        Given _handle is passed a unkown parameter.
        Then _handle should raise an exception
        """
        with pytest.raises(Exception) as excinfo:
            zypp._handle(strat='Unknown')
            assert po.called is False
            assert _reboot.called is False
        excinfo.match("Don't know what to do with strategy: *")


class TestApt():

    @pytest.fixture(scope='class')
    def apt(self):
        """
        Fixture to always get Apt.
        """
        self.linux_dist = patch('srv.salt._modules.packagemanager.linux_distribution')
        self.lnx_dist_object = self.linux_dist.start()
        self.lnx_dist_object.return_value = ('ubuntu', '42.2', 'x86_64')
        # Test all permutations of :debug :kernel and :reboot
        args = {'debug': False, 'kernel': False, 'reboot': False}
        yield PackageManager(**args).pm
        self.linux_dist.stop()

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__refresh(self, po, apt):
        """
        Refresh method
        """
        apt._refresh()
        assert po.called is True

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__updates_needed_not(self, po, apt):
        """
        No updates pending
        """
        process_mock = mock.Mock()
        attrs = {'communicate.return_value': ("", "0;0")}
        process_mock.configure_mock(**attrs)
        po.return_value = process_mock
        ret = apt._updates_needed()
        assert po.called is True
        assert ret is False

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__updates_needed(self, po, apt):
        """
        Updates pending
        """
        process_mock = mock.Mock()
        attrs = {'communicate.return_value': ("", "1;1")}
        process_mock.configure_mock(**attrs)
        po.return_value = process_mock
        ret = apt._updates_needed()
        assert po.called is True
        assert ret is True

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Apt._updates_needed')
    def test__handle_updates_present_reboot_file_present(self, updates_needed, po, _reboot, apt):
        """
        Given there are pending updates.
        And Apt returns with 0
        And Apt touches the /var/run/reboot-required file
        A reboot will be triggered
        """
        updates_needed.return_value = True
        po.return_value.communicate.return_value = ("packages out", "error")
        po.return_value.returncode = 0
        with patch("srv.salt._modules.packagemanager.os.path.isfile") as mock_file:
            mock_file.return_value = True
            apt._handle()
            assert po.called is True
            assert _reboot.called is True

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Apt._updates_needed')
    def test__handle_updates_present_reboot_file_present_raise(self, updates_needed, po, _reboot, apt):
        """
        Given there are pending updates.
        And Apt returns with non-0
        And Apt touches the /var/run/reboot-required file
        Then no reboot should be triggered
        And an Error will be raised
        """
        updates_needed.return_value = True
        po.return_value.communicate.return_value = ("packages out", "error")
        po.return_value.returncode = 1
        with patch("srv.salt._modules.packagemanager.os.path.isfile") as mock_file:
            mock_file.return_value = True
            with pytest.raises(Exception) as excinfo:
                apt._handle()
                excinfo.match('Apt exited with non-0 return*')
                assert po.called is True
                assert _reboot.called is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Apt._updates_needed')
    def test__handle_updates_present_reboot_file_not_present(self, updates_needed, po, _reboot, apt):      
        """
        Given there are pending updates.
        And Apt returns with 0
        And Apt does not touch the /var/run/reboot-required file
        Then no reboot should be  triggered
        """
        updates_needed.return_value = True
        po.return_value.communicate.return_value = ("packages out", "error")
        po.return_value.returncode = 0
        with patch("srv.salt._modules.packagemanager.os.path.isfile") as mock_file:
            mock_file.return_value = False
            apt._handle()
            assert po.called is True
            assert _reboot.called is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Apt._updates_needed')
    def test__handle_updates_present_failed_99(self, updates_needed, po, _reboot, apt):
        """
        Given there are pending updates.
        And Apt returns non-0 returncodes
        And There is no /var/run/reboot-required file
        Then no reboot should be triggered
        And an Error will be raised
        """
        updates_needed.return_value = True
        po.return_value.returncode = 99
        po.return_value.communicate.return_value = ("packages out", "error")
        with pytest.raises(Exception) as excinfo:
            apt._handle()
            excinfo.match('Apt exited with non-0 return*')
            assert po.called is True
            assert _reboot.called is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager._reboot')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Apt._updates_needed')
    def test__handle_updates_not_present(self, updates_needed, po, _reboot, apt):
        """
        Given there are no pending updates.
        And Apt returns non-0 returncodes
        And There is no /var/run/reboot-required file
        Then no reboot should be triggered
        """
        updates_needed.return_value = False
        po.return_value.returncode = 1
        po.return_value.communicate.return_value = ("packages out", "error")
        assert po.called is False
        _reboot.called is False
