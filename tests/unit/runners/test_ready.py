from mock import patch, MagicMock
from srv.modules.utils import ready


class TestChecks():
    """
    A class for checking the Checks 
    """

    @patch('salt.client.LocalClient', autospec=True)
    def test_firewall(self, localclient):
        result = { 'minion': { 'retcode': 0, 'stdout': "-P INPUT ACCEPT\n-P FORWARD ACCEPT\n-P OUTPUT ACCEPT"}}
        local = localclient.return_value
        local.cmd.return_value = result

        check = ready.Checks("I@cluster:ceph")
        check.firewall()
        assert check.passed['firewall'] == 'disabled'

    @patch('salt.client.LocalClient', autospec=True)
    def test_firewall_not_installed(self, localclient):
         result = { 'minion': { 'retcode': 127, 'stdout': "/bin/sh: /usr/sbin/iptables2: No such file or directory"}}
         local = localclient.return_value
         local.cmd.return_value = result

         check = ready.Checks("I@cluster:ceph")
         check.firewall()
         assert check.passed['firewall'] == 'not installed'

    @patch('salt.client.LocalClient', autospec=True)
    def test_firewall_with_chains(self, localclient):
        result = { 'minion': { 'retcode': 0, 'stdout': "-P INPUT ACCEPT\n-P FORWARD ACCEPT\n-P OUTPUT ACCEPT\n-N neutron-filter-top\n-N neutron-openvswi-FORWARD"}}
        local = localclient.return_value
        local.cmd.return_value = result

        check = ready.Checks("I@cluster:ceph")
        check.firewall()
        assert check.passed['firewall'] == 'disabled'

    @patch('salt.client.LocalClient', autospec=True)
    def test_firewall_issues_warning(self, localclient):
        result = { 'minion': { 'retcode': 0, 'stdout': "-P INPUT DROP\n-P FORWARD DROP\n-P OUTPUT ACCEPT\n-N forward_ext\n-N input_ext\n-N reject_func"}}
        local = localclient.return_value
        local.cmd.return_value = result

        check = ready.Checks("I@cluster:ceph")
        check.firewall()
        assert check.warnings['firewall'] 
