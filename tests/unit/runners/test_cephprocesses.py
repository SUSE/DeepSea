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
        roles = [ 'mon' ]

        local = localclient.return_value
        local.cmd.return_value = result

        status = cephprocesses._status(search, roles)
        assert status['mon'] == result

    @patch('srv.modules.runners.cephprocesses._status', autospec=True)
    @patch('srv.modules.runners.cephprocesses._cached_roles', autospec=True)
    def test_check(self, status, cachedroles):
        status.return_value = { 'mon': ['mon2.ceph', 'mon3.ceph', 'mon1.ceph'] }

        cachedroles.return_value = { 'mon': {'mon1.ceph': True, 'mon2.ceph': True, 'mon3.ceph': True}}

        result = cephprocesses.check()
        assert result == True

    @patch('srv.modules.runners.cephprocesses._status', autospec=True)
    @patch('srv.modules.runners.cephprocesses._cached_roles', autospec=True)
    def test_check_fails_for_missing_process(self, status, cachedroles):
        status.return_value = { 'mon': ['mon2.ceph', 'mon3.ceph', 'mon1.ceph'] }

        cachedroles.return_value = { 'mon': {'mon1.ceph': True, 'mon2.ceph': False, 'mon3.ceph': True}}

        result = cephprocesses.check()
        assert result == False

    @patch('srv.modules.runners.cephprocesses._status', autospec=True)
    @patch('srv.modules.runners.cephprocesses._cached_roles', autospec=True)
    def test_check_fails_for_missing_minion(self, status, cachedroles):
        status.return_value = { 'mon': ['mon2.ceph', 'mon3.ceph', 'mon1.ceph'] }

        cachedroles.return_value = { 'mon': {'mon1.ceph': True, 'mon3.ceph': True}}

        result = cephprocesses.check()
        assert result == False

    @patch('salt.client.LocalClient', autospec=True)
    def test_wait(self, localclient):
        local = localclient.return_value
        local.cmd.return_value = {'mon1.ceph': True, 
                                  'mon3.ceph': True, 
                                  'mon2.ceph': True}

        result = cephprocesses.wait(delay=0)
        assert result == True

    @patch('salt.client.LocalClient', autospec=True)
    def test_wait_fails(self, localclient):
        local = localclient.return_value
        local.cmd.return_value = {'mon1.ceph': True, 
                                  'mon3.ceph': False, 
                                  'mon2.ceph': True}

        result = cephprocesses.wait(delay=0)
        assert result == False

    @patch('salt.client.LocalClient', autospec=True)
    def test_timeout(self, localclient):
        local = localclient.return_value
        local.cmd.return_value = { 'virtual' : 'kvm' }

        ret = cephprocesses._timeout()
        assert ret == 120

    @patch('salt.client.LocalClient', autospec=True)
    def test_physical_timeout(self, localclient):
        local = localclient.return_value
        local.cmd.return_value = { 'virtual' : 'physical' }

        ret = cephprocesses._timeout()
        assert ret == 900


