from mock import patch, MagicMock
from srv.modules.runners import advise


class TestAdvise():
    """
    A class for checking notifications
    """

    def test_tidy(self):
        report = {'data1.ceph': {'unconfigured': {'/dev/sdb', '/dev/sdc'}}}
        result = advise._tidy('unconfigured', report)
        expected = "data1.ceph: /dev/sdb, /dev/sdc\n"
        assert result == expected

    def test_tidy_malformed(self):
        report = {'data1.ceph': {'': "nothing"}}
        result = advise._tidy('unconfigured', report)
        expected = ""
        assert result == expected

    def test_tidy_long(self):
        report = {'data1.long.domain.name': 
                   {'unconfigured': 
                     {'/dev/disk/by-id/scsi-012345678901234567890123456789', 
                      '/dev/disk/by-id/scsi-abcdefghijklmnopqrstuvwxyzabcd'}}}
        result = advise._tidy('unconfigured', report)
        expected = "\ndata1.long.domain.name:\n  /dev/disk/by-id/scsi-012345678901234567890123456789\n  /dev/disk/by-id/scsi-abcdefghijklmnopqrstuvwxyzabcd\n"
        assert result == expected

