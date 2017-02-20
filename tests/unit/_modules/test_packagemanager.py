import pytest
from srv.salt._modules.packagemanager import PackageManager, Zypper, Apt
from mock import MagicMock, patch, mock_open, mock


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
    def test_PackageManager_centos(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('centos', '8', 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Apt) is True
        
    @mock.patch('srv.salt._modules.packagemanager.linux_distribution')
    def test_PackageManager_fedora(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('fedora', '23', 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Apt) is True
    
    @mock.patch('srv.salt._modules.packagemanager.linux_distribution')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test_reboot(self, po, dist_return):
        dist_return.return_value = ('opensuse', '42.2', 'x86_64')
        ret = PackageManager()
        ret.reboot_in()
        assert po.called is True

    @mock.patch('srv.salt._modules.packagemanager.linux_distribution')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test_not_implemented(self, po, dist_return):
        dist_return.return_value = ('ScientificLinux', '42.2', 'x86_64')
        with pytest.raises(ValueError) as excinfo:
            PackageManager()
        excinfo.match('Failed to detect PackageManager for OS.*')

class TestZypper():

    @pytest.fixture(scope='class')
    def zypp(self):
        self.linux_dist = patch('srv.salt._modules.packagemanager.linux_distribution')
        self.lnx_dist_object  = self.linux_dist.start()
        self.lnx_dist_object.return_value = ('opensuse', '42.2', 'x86_64')
        args = {'debug': False, 'kernel': False, 'reboot': False}
        yield PackageManager(**args).pm
        self.linux_dist.stop()

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__refresh(self, po, zypp):
        zypp._refresh()
        assert po.called is True

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__updates_needed_not(self, po, zypp):
        po.return_value.returncode = 0
        ret = zypp._updates_needed()
        assert po.called is True
        assert ret is False

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__updates_needed(self, po, zypp):
        po.return_value.returncode = 1
        ret = zypp._updates_needed()
        assert po.called is True
        assert ret is True

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__patches_needed(self, po, zypp):
        po.return_value.returncode = 100
        ret = zypp._patches_needed()
        assert po.called is True
        assert ret is True

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__patches_needed_not(self, po, zypp):
        po.return_value.returncode = 0
        ret = zypp._patches_needed()
        assert po.called is True
        assert ret is False
        
    @mock.patch('srv.salt._modules.packagemanager.PackageManager.reboot_in')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Zypper._updates_needed')
    def test__handle_updates_present(self, updates_needed, po, reboot_in, zypp):
        updates_needed.return_value = True
        po.return_value.returncode = 102
        po.return_value.communicate.return_value = ("packages out", "error")
        zypp._handle()
        po.called is True
        reboot_in.called is True

    @mock.patch('srv.salt._modules.packagemanager.PackageManager.reboot_in')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Zypper._updates_needed')
    def test__handle_updates_not_present(self, updates_needed, po, reboot_in, zypp):
        updates_needed.return_value = False
        po.return_value.returncode = 102
        po.return_value.communicate.return_value = ("packages out", "error")
        zypp._handle()
        po.called is False
        reboot_in.called is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager.reboot_in')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Zypper._updates_needed')
    def test__handle_updates_present_failed_99(self, updates_needed, po, reboot_in, zypp):
        updates_needed.return_value = True
        po.return_value.returncode = 99
        po.return_value.communicate.return_value = ("packages out", "error")
        po.called is True
        reboot_in.called is False
        with pytest.raises(StandardError) as excinfo:
            zypp._handle()
        excinfo.match('Zypper failed. Look at the logs*')

    @mock.patch('srv.salt._modules.packagemanager.PackageManager.reboot_in')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Zypper._updates_needed')
    def test__handle_updates_present_failed_1(self, updates_needed, po, reboot_in, zypp):
        updates_needed.return_value = True
        po.return_value.returncode = 1
        po.return_value.communicate.return_value = ("packages out", "error")
        po.called is True
        reboot_in.called is False
        with pytest.raises(StandardError) as excinfo:
            zypp._handle()
        excinfo.match('Zypper failed. Look at the logs*')

class TestApt():

    @pytest.fixture(scope='class')
    def apt(self):
        self.linux_dist = patch('srv.salt._modules.packagemanager.linux_distribution')
        self.lnx_dist_object  = self.linux_dist.start()
        self.lnx_dist_object.return_value = ('fedora', '42.2', 'x86_64')
        args = {'debug': False, 'kernel': False, 'reboot': False}
        yield PackageManager(**args).pm
        self.linux_dist.stop()

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__refresh(self, po, apt):
        apt._refresh()
        assert po.called is True

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__updates_needed_not(self, po, apt):
        po.return_value.returncode = 0
        ret = apt._updates_needed()
        assert po.called is True
        assert ret is False

    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test__updates_needed(self, po, apt):
        po.return_value.returncode = 1
        ret = apt._updates_needed()
        assert po.called is True
        assert ret is True

    @mock.patch('srv.salt._modules.packagemanager.PackageManager.reboot_in')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Apt._updates_needed')
    def test__handle_updates_present(self, updates_needed, po, reboot_in, apt):
        updates_needed.return_value = True
        po.return_value.returncode = 102
        po.return_value.communicate.return_value = ("packages out", "error")
        apt._handle()
        po.called is True
        reboot_in.called is True

    @mock.patch('srv.salt._modules.packagemanager.PackageManager.reboot_in')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Apt._updates_needed')
    def test__handle_updates_present_failed_99(self, updates_needed, po, reboot_in, apt):
        updates_needed.return_value = True
        po.return_value.returncode = 99
        po.return_value.communicate.return_value = ("packages out", "error")
        po.called is True
        reboot_in.called is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager.reboot_in')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Apt._updates_needed')
    def test__handle_updates_present_failed_1(self, updates_needed, po, reboot_in, apt):
        updates_needed.return_value = True
        po.return_value.returncode = 1
        po.return_value.communicate.return_value = ("packages out", "error")
        po.called is True
        reboot_in.called is False

    @mock.patch('srv.salt._modules.packagemanager.PackageManager.reboot_in')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    @mock.patch('srv.salt._modules.packagemanager.Apt._updates_needed')
    def test__handle_updates_not_present(self, updates_needed, po, reboot_in, apt):
        updates_needed.return_value = False
        po.return_value.returncode = 1
        po.return_value.communicate.return_value = ("packages out", "error")
        po.called is False
        reboot_in.called is False
