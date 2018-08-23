from mock import patch, MagicMock
from srv.modules.runners import replace


class TestReplace():
    """
    A class for checking notifications
    """

    def test_find_host(self):
        osd_list = {'data1.ceph': ['1', '2', '3'],
                    'data2.ceph': ['4', '5', '6']}
        result = replace._find_host(5, osd_list)
        assert result == 'data2.ceph'

    def test_find_host_missing(self):
        osd_list = {'data1.ceph': ['1', '2', '3'],
                    'data2.ceph': ['4', '5', '6']}
        result = replace._find_host(9, osd_list)
        assert result == ""

