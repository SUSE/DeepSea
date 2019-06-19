import pytest
from srv.salt._modules import mds


@pytest.mark.parametrize(
    'hostname, mds_name',
    [
        ('my_hostname', 'my_hostname'),
        ('my_hostname1', 'my_hostname1'),
        ('2my_hostname', 'mds.2my_hostname'),
        ('666', 'mds.666'),
    ])
def test_get_name(hostname, mds_name):
    res = mds.get_name(hostname)
    err_report = 'get_name returned wrong mds name: {} vs {}'.format(res,
                                                                     mds_name)
    assert res == mds_name, err_report

