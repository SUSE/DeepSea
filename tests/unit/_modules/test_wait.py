import pytest
import sys
sys.path.insert(0, 'srv/salt/_modules')
from srv.salt._modules import wait
from mock import MagicMock, mock

DEFAULT_MODULE = wait


class TestHealthStatusCheck(object):

    """ Unittests for HealthStatusCheck """
    @pytest.fixture()
    def wait(self):
        wait.rados = MagicMock()
        yield wait

    @mock.patch('srv.salt._modules.wait.time')
    def test_just(self, time_mock, wait):
        kwargs = {'status': "HEALTH_OK"}
        wait.just(**kwargs)
        time_mock.sleep.assert_called_with(6)

    @mock.patch('srv.salt._modules.wait.time')
    def test_just_custom_delay(self, time_mock, wait):
        kwargs = {'status': "HEALTH_OK", 'delay': 7}
        wait.just(**kwargs)
        time_mock.sleep.assert_called_with(7)
