from mock import patch, MagicMock, mock
from srv.modules.runners import populate


class TestCephRoles():
    """
    A class for checking Role methods
    """

    @patch('salt.client.LocalClient')
    def test_publicnetwork_is_ipv6(self, client):
        client.return_value.cmd.return_value = { 'minion1': {'public_network': 'fd00::/64'}}
        with patch.object(populate.CephRoles, "__init__", lambda self, se, c, sv, w: None):
            ceph_roles = populate.CephRoles({}, 'ceph', ['mon.ceph'], mock.Mock())
            ceph_roles.search = '*'
            assert ceph_roles.publicnetwork_is_ipv6()

    @patch('salt.client.LocalClient')
    def test_publicnetwork_is_ipv6_for_multiple(self, client):
        client.return_value.cmd.return_value = { 'minion1': {'public_network': 'fd00::/64, fd01::/64'}}
        with patch.object(populate.CephRoles, "__init__", lambda self, se, c, sv, w: None):
            ceph_roles = populate.CephRoles({}, 'ceph', ['mon.ceph'], mock.Mock())
            ceph_roles.search = '*'
            assert ceph_roles.publicnetwork_is_ipv6()

    @patch('salt.client.LocalClient')
    def test_publicnetwork_is_ipv6_fails(self, client):
        client.return_value.cmd.return_value = { 'minion1': {'public_network': '192.168.0.0/24'}}
        with patch.object(populate.CephRoles, "__init__", lambda self, se, c, sv, w: None):
            ceph_roles = populate.CephRoles({}, 'ceph', ['mon.ceph'], mock.Mock())
            ceph_roles.search = '*'
            assert ceph_roles.publicnetwork_is_ipv6() == False

    @patch('salt.client.LocalClient')
    def test_publicnetwork_is_ipv6_fails_on_malformed_address(self, client):
        client.return_value.cmd.return_value = { 'minion1': {'public_network': 'fdgg::/64'}}
        with patch.object(populate.CephRoles, "__init__", lambda self, se, c, sv, w: None):
            ceph_roles = populate.CephRoles({}, 'ceph', ['mon.ceph'], mock.Mock())
            ceph_roles.search = '*'
            assert ceph_roles.publicnetwork_is_ipv6() == False
