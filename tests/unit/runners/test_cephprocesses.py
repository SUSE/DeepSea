import pytest
import salt.client

from mock import patch, MagicMock
from srv.modules.runners import cephprocesses


class TestCephProcesses():

    @patch('salt.client.LocalClient', autospec=True)
    def test_status(self, localclient):
        result = {'mon1.ceph': True,
                  'mon3.ceph': True,
                  'mon2.ceph': True}

        search = "I@cluster:ceph"
        roles = ['mon']

        local = localclient.return_value
        local.cmd.return_value = result

        status = cephprocesses._status(search, roles, False)
        assert status['mon'] == result

    @patch('srv.modules.runners.cephprocesses._status', autospec=True)
    @patch('srv.modules.runners.cephprocesses._cached_roles', autospec=True)
    def test_check(self, cachedroles, status):
        cachedroles.return_value = ['mon']

        status.return_value = {'mon': {'mon1.ceph': True,
                                       'mon2.ceph': True,
                                       'mon3.ceph': True}}

        result = cephprocesses.check()
        assert cachedroles.called is True
        assert result is True

    @patch('srv.modules.runners.cephprocesses._cached_roles', autospec=True)
    @patch('srv.modules.runners.cephprocesses._status', autospec=True)
    def test_check_fails_for_missing_process(self, status, cachedroles):
        cachedroles.return_value = ['mon']

        status.return_value = {'mon': {'mon1.ceph': True,
                                       'mon2.ceph': False,
                                       'mon3.ceph': True}}

        result = cephprocesses.check()
        assert cachedroles.called is True
        assert result is False

    @patch('srv.modules.runners.cephprocesses._cached_roles', autospec=True)
    @patch('srv.modules.runners.cephprocesses._status', autospec=True)
    def test_check_fails_specified_roles(self, status, cachedroles):
        status.return_value = {'mon': {'mon1.ceph': False,
                                       'mon3.ceph': False}}

        result = cephprocesses.check(roles=['storage'])
        assert cachedroles.called is False
        assert result is False

    @patch('srv.modules.runners.cephprocesses._cached_roles', autospec=True)
    @patch('srv.modules.runners.cephprocesses._status', autospec=True)
    def test_check_fails_specified_roles_mixed(self, status, cachedroles):
        status.return_value = {'mon': {'mon1.ceph': False,
                                       'mon3.ceph': True},
                               'rgw': {'rgw1.ceph': True,
                                       'rgw2.ceph': True}}

        result = cephprocesses.check(roles=['rgw', 'mon'])
        assert cachedroles.called is False
        assert result is False

    @patch('srv.modules.runners.cephprocesses._cached_roles', autospec=True)
    @patch('srv.modules.runners.cephprocesses._status', autospec=True)
    def test_check_tolerate_1(self, status, cachedroles):
        status.return_value = {'mon': {'mon1.ceph': False,
                                       'mon3.ceph': True}}

        result = cephprocesses.check(roles=['storage'], tolerate_down=1)
        assert cachedroles.called is False
        assert result is True

    @patch('srv.modules.runners.cephprocesses._cached_roles', autospec=True)
    @patch('srv.modules.runners.cephprocesses._status', autospec=True)
    def test_check_tolerate_0(self, status, cachedroles):
        status.return_value = {'mon': {'mon1.ceph': False,
                                       'mon3.ceph': True}}

        result = cephprocesses.check(roles=['storage'], tolerate_down=0)
        assert cachedroles.called is False
        assert result is False

    @patch('salt.client.LocalClient', autospec=True)
    def test_wait(self, localclient):
        local = localclient.return_value
        local.cmd.return_value = {'mon1.ceph': True,
                                  'mon3.ceph': True,
                                  'mon2.ceph': True}

        result = cephprocesses.wait(delay=0)
        assert result is True

    @patch('salt.client.LocalClient', autospec=True)
    def test_wait_fails(self, localclient):
        local = localclient.return_value
        local.cmd.return_value = {'mon1.ceph': True,
                                  'mon3.ceph': False,
                                  'mon2.ceph': True}

        result = cephprocesses.wait(delay=0)
        assert result is False

    @patch('salt.client.LocalClient', autospec=True)
    def test_timeout(self, localclient):
        local = localclient.return_value
        local.cmd.return_value = {'virtual': 'kvm'}

        ret = cephprocesses._timeout()
        assert ret == 120

    @patch('salt.client.LocalClient', autospec=True)
    def test_physical_timeout(self, localclient):
        local = localclient.return_value
        local.cmd.return_value = {'virtual': 'physical'}

        ret = cephprocesses._timeout()
        assert ret == 900
