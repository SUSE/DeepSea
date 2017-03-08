import pytest
import salt.client

from mock import patch, MagicMock
from srv.modules.runners import cephservices


class TestCephServices():

    @patch('salt.client.LocalClient', autospec=True)
    def test_status(self, localclient):
        result = {'mon1.ceph': '3420', 
                  'mon3.ceph': '3413', 
                  'mon2.ceph': '3969'}

        processes = { 'mon': [ 'ceph-mon' ] }
        search = "I@cluster:ceph"


        local = localclient.return_value
        local.cmd.return_value = result

        status = cephservices._status(processes, search)
        assert status['mon']['ceph-mon'] == result

    @patch('srv.modules.runners.cephservices._status', autospec=True)
    @patch('srv.modules.runners.cephservices._cached_roles', autospec=True)
    def test_check(self, status, cachedroles):
        status.return_value = { 'mon': ['mon2.ceph', 'mon3.ceph', 'mon1.ceph'] }

        cachedroles.return_value = { 'mon': {'ceph-mon': {'mon1.ceph': '3420', 'mon2.ceph': '3969', 'mon3.ceph': '3413'}}}

        result = cephservices.check()
        assert result == True

    @patch('srv.modules.runners.cephservices._status', autospec=True)
    @patch('srv.modules.runners.cephservices._cached_roles', autospec=True)
    def test_check_fails_for_missing_process(self, status, cachedroles):
        status.return_value = { 'mon': ['mon2.ceph', 'mon3.ceph', 'mon1.ceph'] }

        cachedroles.return_value = { 'mon': {'ceph-mon': {'mon1.ceph': '3420', 'mon2.ceph': '', 'mon3.ceph': '3413'}}}

        result = cephservices.check()
        assert result == False

    @patch('srv.modules.runners.cephservices._status', autospec=True)
    @patch('srv.modules.runners.cephservices._cached_roles', autospec=True)
    def test_check_fails_for_missing_minion(self, status, cachedroles):
        status.return_value = { 'mon': ['mon2.ceph', 'mon3.ceph', 'mon1.ceph'] }

        cachedroles.return_value = { 'mon': {'ceph-mon': {'mon1.ceph': '3420', 'mon3.ceph': '3413'}}}

        result = cephservices.check()
        assert result == False

    @patch('srv.modules.runners.cephservices.check', autospec=True)
    @patch('srv.modules.runners.cephservices._timeout', autospec=True)
    def test_wait(self, check, timeout):
        check.return_value = True
        timeout.return_value = 60

        result = cephservices.wait(delay=0)
        assert result == True

    @patch('srv.modules.runners.cephservices.check', autospec=True)
    @patch('srv.modules.runners.cephservices._timeout', autospec=True)
    def test_wait_raises_runtimeerror(self, check, timeout):
        check.return_value = False
        timeout.return_value = 0

        with pytest.raises(RuntimeError) as excinfo:
            cephservices.wait(delay=0, timeout=0)

