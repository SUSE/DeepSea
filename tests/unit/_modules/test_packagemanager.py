import pytest
from srv.salt._modules.packagemanager import PackageManager, Zypper, Apt
from mock import MagicMock, patch, mock_open, mock


class TestPackageManager():
    '''
    This class contains a set of functions that test srv.salt._modules.packagemanager
    '''

    @mock.patch('srv.salt._modules.packagemanager.platform.linux_distribution')
    def test_PackageManager_opensuse(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('opensuse', 42.1, 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Zypper) is True

    @mock.patch('srv.salt._modules.packagemanager.platform.linux_distribution')
    def test_PackageManager_suse(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('SUSE', '12.2', 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Zypper) is True
        
    @mock.patch('srv.salt._modules.packagemanager.platform.linux_distribution')
    def test_PackageManager_centos(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('centos', '8', 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Apt) is True
        
    @mock.patch('srv.salt._modules.packagemanager.platform.linux_distribution')
    def test_PackageManager_fedora(self, dist_return):
        """
        Test Packagemanager assignments based on `patform` mocks.
        """
        dist_return.return_value = ('fedora', '23', 'x86_64')
        ret = PackageManager()
        assert isinstance(ret.pm, Apt) is True
    
    @mock.patch('srv.salt._modules.packagemanager.platform.linux_distribution')
    @mock.patch('srv.salt._modules.packagemanager.Popen')
    def test_reboot(self, po, dist_return):
        dist_return.return_value = ('opensuse', '42.2', 'x86_64')
        ret = PackageManager()
        ret.reboot_in()
        assert po.called is True


class TestZypper():

    @pytest.fixture(scope='module')
    def zypp(self):
        self.zypp = patch('srv.salt._modules.packagemanager.PackageManager')
        self.platform = patch('srv.salt._modules.packagemanager.platform.linux_distribution')
        self.platform.return_value = ('opensuse', '42.2', 'x86_64')
        self.zyppr = self.zypp.start()
        args = {'debug': False, 'kernel': False, 'reboot': False}
        yield PackageManager(**args).pm
        self.zyppr.stop()

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

    def test__handle(self, po, zypp):
        pass
