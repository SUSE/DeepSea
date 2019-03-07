import os
import pytest
from srv.salt._modules import multi
from mock import MagicMock, patch, mock, mock_open


class Testiperf_server_cmd():
    '''
    Check the returns of iperf_server_cmd
    '''
    def test_iperf_path_is_not_set(self):
        result = multi.iperf_server_cmd()
        assert "iperf3 not found in path" in result

    @mock.patch('srv.salt._modules.multi.Popen')
    def test_iperf_server_cmd(self, popen):
        '''
        Verify that "salt" is part of the command line
        '''
        multi.iperf_path = "/usr/bin/iperf3"
        result = multi.iperf_server_cmd()
        for call in popen.call_args_list:
            args, kwargs = call
            assert 'salt' in args[0]
        assert "iperf3 started at cpu" in result

class Testkill_iperf_cmd():
    '''
    Check the return of kill_iperf_cmd
    '''
    @mock.patch('srv.salt._modules.multi.Popen')
    def test_kill_iperf_cmd(self, popen):
        '''
        Verify that "iperf3.*salt" is part of the command line
        '''
        result = multi.kill_iperf_cmd()
        for call in popen.call_args_list:
            args, kwargs = call
            assert 'iperf3.*salt' in args[0]
        assert result == True

