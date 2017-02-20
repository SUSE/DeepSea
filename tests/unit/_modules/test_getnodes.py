import pytest

from mock import patch, MagicMock
from srv.modules.runners import getnodes



class TestGetNodes():

    def test__preserve_order_sorted(self):
        inp = ['mon1', 'mon2', 'mon3', 'data1', 'data2',
               'data2', 'data3', 'mds1', 'mon1', 'mon3', 'rgw1']
        expect = ['mon1', 'mon2', 'mon3', 'data1',
                  'data2', 'data3', 'mds1', 'rgw1']
        assert getnodes._preserve_order_sorted(inp) == expect

