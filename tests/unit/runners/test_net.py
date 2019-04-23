from mock import patch, MagicMock
from srv.modules.runners import net


class TestNet():
    """
    A class for checking the net runner
    """

    def test_address_single_ipv4(self):
        addresses = ['192.168.0.1']
        networks = "192.168.0.0/24"
        result = net._address(addresses, networks)
        assert result == ['192.168.0.1']

    def test_address_single_ipv4_no_match(self):
        addresses = ['192.168.0.1']
        networks = "192.168.1.0/24"
        result = net._address(addresses, networks)
        assert result == []

    def test_address_multiple_ipv4(self):
        addresses = ['192.168.0.1', '192.168.1.1']
        networks = "192.168.0.0/24, 192.168.1.0/24"
        result = net._address(addresses, networks)
        assert result == ['192.168.0.1', '192.168.1.1']

    def test_address_multiple_ipv4_no_match(self):
        addresses = ['192.168.0.1', '192.168.1.1']
        networks = "192.168.2.0/24, 192.168.3.0/24"
        result = net._address(addresses, networks)
        assert result == []

    def test_address_single_ipv6(self):
        addresses = ['fd00:1::1']
        networks = "fd00:1::/64"
        result = net._address(addresses, networks)
        assert result == ['fd00:1::1']

    def test_address_single_ipv6_no_match(self):
        addresses = ['fd00:1::1']
        networks = "fd00:2::/64"
        result = net._address(addresses, networks)
        assert result == []

    def test_address_multiple_ipv6(self):
        addresses = ['fd00:1::1', 'fd00:2::1']
        networks = "fd00:1::/64, fd00:2::/64"
        result = net._address(addresses, networks)
        assert result == ['fd00:1::1', 'fd00:2::1']

    def test_address_multiple_ipv6_no_match(self):
        addresses = ['fd00:1::1', 'fd00:2::1']
        networks = "fd00:3::/64, fd00:4::/64"
        result = net._address(addresses, networks)
        assert result == []

