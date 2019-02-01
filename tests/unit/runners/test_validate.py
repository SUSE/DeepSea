import pytest
import salt.client
import sys
import types
sys.path.insert(0, 'srv/modules/runners')
sys.path.insert(0, 'srv/modules/runners/utils')

from mock import patch, MagicMock, mock_open
from srv.modules.runners import validate


# Trivial tests to validate the unittest itself is working
def test_get_printer():
    assert(isinstance(validate.get_printer(), validate.PrettyPrinter))
    assert(isinstance(validate.get_printer('json'), validate.JsonPrinter))
    assert(isinstance(validate.get_printer('quiet'), validate.JsonPrinter))


# LocalClient() is instanziated by
# ClusterAssignment(). They require Mocking for the test environment
class TestClusterAssignment():
    @patch('salt.client.LocalClient')
    def test_single_cluster(self, mock_localclient):
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})
        cluster_dict = {"minionA":"ceph", "minionB": "ceph", "minionC": "ceph"}

        local = mock_localclient.return_value
        local.cmd.return_value = cluster_dict

        cluster = validate.ClusterAssignment()
        assert len(cluster.names) == 1
        assert set(cluster.names['ceph']) == set(["minionA","minionB","minionC"])

    @patch('salt.client.LocalClient', autospec=True)
    def test_single_cluster_unassigned(self, mock_localclient):
        cluster_dict = {"minionA":"ceph", "minionB": "ceph",
                        "minionC": "unassigned", "minionD": "ceph",
                        "minionE": "unassigned"}

        local = mock_localclient.return_value
        local.cmd.return_value = cluster_dict

        cluster = validate.ClusterAssignment()
        assert len(cluster.names) == 1
        assert set(cluster.names['ceph']) == set(["minionA","minionB","minionD"])

    @patch('salt.client.LocalClient', autospec=True)
    def test_multi_cluster_unassigned(self, mock_localclient):
        cluster_dict = {"minionA":"ceph", "minionB": "kraken",
                        "minionC": "unassigned", "minionD": "ceph",
                        "minionE": "kraken"}

        local = mock_localclient.return_value
        local.cmd.return_value = cluster_dict

        cluster = validate.ClusterAssignment()
        assert len(cluster.names) == 2
        assert set(cluster.names['ceph']) == set(["minionA","minionD"])
        assert set(cluster.names['kraken']) == set(["minionB","minionE"])


class TestUtilMethods():
    def test_parse_empty_string_list(self):
        assert validate.Util.parse_list_from_string("", ",") == []

    def test_parse_single_element_string_list(self):
        assert validate.Util.parse_list_from_string("1", ",") == ['1']

    def test_parse_string_list(self):
        list_str = "1, 4     ,   5, , 7"
        assert validate.Util.parse_list_from_string(list_str, ",") == ['1', '4', '5', '7']


# LocalClient() is instanziated by
# ClusterAssignment(). They require Mocking for the test environment
class TestValidation():
    @patch('salt.client.LocalClient', autospec=True)
    def test_dev_env(self, mock_localclient, monkeypatch):
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})
        monkeypatch.setenv('DEV_ENV', 'true')
        validator = validate.Validate("setup")

        assert len(validator.passed) == 0
        validator.dev_env()
        assert validator.passed['DEV_ENV'] == 'True'

    @patch('salt.client.LocalClient', autospec=True)
    def test_fsid(self, mock_localclient):
        fsid = 'ba0ae5e1-4282-3282-a745-2bf12888a393'
        fake_data = {'admin.ceph':
                         {'fsid': fsid}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.passed) == 0
        validator.fsid()
        assert validator.passed['fsid'] == 'valid'

    @patch('salt.client.LocalClient', autospec=True)
    def test_fsid_invalid(self, mock_localclient):
        fsid = 'not a valid-uuid  but still 36 chars'
        fake_data = {'admin.ceph':
                         {'fsid': fsid}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.errors) == 0
        validator.fsid()
        assert "does not appear to be a UUID" in validator.errors['fsid'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_fsid_too_short(self, mock_localclient):
        fsid = 'too short'
        fake_data = {'admin.ceph': {'fsid': fsid}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.errors) == 0
        validator.fsid()
        assert "characters, not 36" in validator.errors['fsid'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_public_interface_for_ipv4(self, mock_localclient):
        data = {'mon.ceph': {'public_network': '192.168.0.0/24'},
                'mgr.ceph': {'public_network': '192.168.0.0/24'}}
        grains = {'mon.ceph': {'ipv4': ['192.168.0.100'], 'ipv6': ['fd00::1']},
                  'mgr.ceph': {'ipv4': ['192.168.0.101'], 'ipv6': ['fd00::2']}}

        with patch.object(validate.Validate, "__init__", lambda self, n: None):
            validator = validate.Validate("setup")
            validator.errors = {}
            validator.warnings = {}
            validator.passed = {}
            validator.data = data
            validator.grains = grains

            validator.public_interface()
            assert validator.passed['public_interface'] == "valid"

    @patch('salt.client.LocalClient', autospec=True)
    def test_public_interface_for_ipv4_only(self, mock_localclient):
        data = {'mon.ceph': {'public_network': '192.168.0.0/24'},
                'mgr.ceph': {'public_network': '192.168.0.0/24'}}
        grains = {'mon.ceph': {'ipv4': ['192.168.0.100']},
                  'mgr.ceph': {'ipv4': ['192.168.0.101']}}

        with patch.object(validate.Validate, "__init__", lambda self, n: None):
            validator = validate.Validate("setup")
            validator.errors = {}
            validator.warnings = {}
            validator.passed = {}
            validator.data = data
            validator.grains = grains

            validator.public_interface()
            assert validator.passed['public_interface'] == "valid"

    @patch('salt.client.LocalClient', autospec=True)
    def test_public_interface_for_ipv4_errors(self, mock_localclient):
        data = {'mon.ceph': {'public_network': '192.168.1.0/24'},
                'mgr.ceph': {'public_network': '192.168.1.0/24'}}
        grains = {'mon.ceph': {'ipv4': ['192.168.0.100'], 'ipv6': ['fd00::1']},
                  'mgr.ceph': {'ipv4': ['192.168.0.101'], 'ipv6': ['fd00::2']}}

        with patch.object(validate.Validate, "__init__", lambda self, n: None):
            validator = validate.Validate("setup")
            validator.errors = {}
            validator.warnings = {}
            validator.passed = {}
            validator.data = data
            validator.grains = grains

            validator.public_interface()
            assert "missing address" in validator.errors['public_interface'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_public_interface_for_ipv6(self, mock_localclient):
        data = {'mon.ceph': {'public_network': 'fd00::/64'},
                'mgr.ceph': {'public_network': 'fd00::/64'}}
        grains = {'mon.ceph': {'ipv4': ['192.168.0.100'], 'ipv6': ['fd00::1']},
                  'mgr.ceph': {'ipv4': ['192.168.0.101'], 'ipv6': ['fd00::2']}}

        with patch.object(validate.Validate, "__init__", lambda self, n: None):
            validator = validate.Validate("setup")
            validator.errors = {}
            validator.warnings = {}
            validator.passed = {}
            validator.data = data
            validator.grains = grains

            validator.public_interface()
            assert validator.passed['public_interface'] == "valid"

    @patch('salt.client.LocalClient', autospec=True)
    def test_public_interface_for_ipv6_errors(self, mock_localclient):
        data = {'mon.ceph': {'public_network': 'fd01::/64'},
                'mgr.ceph': {'public_network': 'fd01::/64'}}
        grains = {'mon.ceph': {'ipv4': ['192.168.0.100'], 'ipv6': ['fd00::1']},
                  'mgr.ceph': {'ipv4': ['192.168.0.101'], 'ipv6': ['fd00::2']}}

        with patch.object(validate.Validate, "__init__", lambda self, n: None):
            validator = validate.Validate("setup")
            validator.errors = {}
            validator.warnings = {}
            validator.passed = {}
            validator.data = data
            validator.grains = grains

            validator.public_interface()
            assert "missing address" in validator.errors['public_interface'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_check_ipversion(self, mock_localclient):
        with patch.object(validate.Validate, "__init__", lambda self, n: None):
            validator = validate.Validate("setup")
            validator.errors = {}
            validator.warnings = {}
            validator.passed = {}
            validator.ipversion = set([4])

            validator.check_ipversion()
            assert validator.passed['ip_version'] == "valid"

    @patch('salt.client.LocalClient', autospec=True)
    def test_check_ipversion_fails(self, mock_localclient):
        with patch.object(validate.Validate, "__init__", lambda self, n: None):
            validator = validate.Validate("setup")
            validator.errors = {}
            validator.warnings = {}
            validator.passed = {}
            validator.ipversion = set([4, 6])

            validator.check_ipversion()
            assert "Networks must be" in validator.errors['ip_version'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_monitors(self, mock_localclient):
        fake_data = {'mon1': { 'roles': 'mon'},
                     'mon2': { 'roles': 'mon'},
                     'mon3': { 'roles': 'mon'}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.passed) == 0
        validator.monitors()
        assert validator.passed['monitors'] == "valid"

    @patch('salt.client.LocalClient', autospec=True)
    def test_monitors_too_few(self, mock_localclient):
        fake_data = {'mon1': { 'roles': 'mon'},
                     'mon2': { 'roles': 'mon'}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.errors) == 0
        validator.monitors()
        assert "Too few monitors" in validator.errors['monitors'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_mgrs(self, mock_localclient):
        fake_data = {'mgr1': { 'roles': 'mgr'},
                     'mgr2': { 'roles': 'mgr'},
                     'mgr3': { 'roles': 'mgr'}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.passed) == 0
        validator.mgrs()
        assert validator.passed['mgrs'] == "valid"

    @patch('salt.client.LocalClient', autospec=True)
    def test_mgrs_too_few(self, mock_localclient):
        fake_data = {'mgr1': { 'roles': 'mgr'},
                     'mgr2': { 'roles': 'mgr'}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.errors) == 0
        validator.mgrs()
        assert "Too few mgrs" in validator.errors['mgrs'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_ceph_updates(self, mock_localclient):
        """
        Refresh works for both minions
        and there are new packages
        """
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})

        fake_data = {'admin.ceph': {'packages': [{'arch': 'x86_64',
                                                  'edition': '13.2.1.427+g6cd01d4dd2-1.10',
                                                  'edition-old': '13.2.1.427+g6cd01d4dd2-1.8',
                                                  'kind': 'package',
                                                  'name': 'ceph'},
                                                  {'arch': 'x86_64',
                                                  'edition': '13.2.1.427+g6cd01d4dd2-1.10',
                                                  'edition-old': '13.2.1.427+g6cd01d4dd2-1.8',
                                                  'kind': 'package',
                                                  'name': 'python3-cephfs'}],
                                    'status': 'True'},
                     'data1.ceph': {'packages': [{'arch': 'x86_64',
                                                  'edition': '13.2.1.427+g6cd01d4dd2-1.10',
                                                  'edition-old': '13.2.1.427+g6cd01d4dd2-1.8',
                                                  'kind': 'package',
                                                  'name': 'ceph'},
                                                  {'arch': 'x86_64',
                                                  'edition': '13.2.1.427+g6cd01d4dd2-1.10',
                                                  'edition-old': '13.2.1.427+g6cd01d4dd2-1.8',
                                                  'kind': 'package',
                                                  'name': 'python3-cephfs'}],
                                    'status': 'True'}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)
        validator.ceph_updates()
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 1
        assert "On or more of your minions have updates pending that might cause ceph-daemons to restart. This might extend the duration of this Stage depending on your cluster size." in validator.warnings['ceph_updates'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_ceph_updates_1(self, mock_localclient):
        """
        Refresh fails for one of the minions
        and there are new packages
        """
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})

        fake_data = {'admin.ceph': {'packages': [{'arch': 'x86_64',
                                                  'edition': '13.2.1.427+g6cd01d4dd2-1.10',
                                                  'edition-old': '13.2.1.427+g6cd01d4dd2-1.8',
                                                  'kind': 'package',
                                                  'name': 'ceph'},
                                                  {'arch': 'x86_64',
                                                  'edition': '13.2.1.427+g6cd01d4dd2-1.10',
                                                  'edition-old': '13.2.1.427+g6cd01d4dd2-1.8',
                                                  'kind': 'package',
                                                  'name': 'python3-cephfs'}],
                                    'status': False},
                     'data1.ceph': {'packages': [{'arch': 'x86_64',
                                                  'edition': '13.2.1.427+g6cd01d4dd2-1.10',
                                                  'edition-old': '13.2.1.427+g6cd01d4dd2-1.8',
                                                  'kind': 'package',
                                                  'name': 'ceph'},
                                                  {'arch': 'x86_64',
                                                  'edition': '13.2.1.427+g6cd01d4dd2-1.10',
                                                  'edition-old': '13.2.1.427+g6cd01d4dd2-1.8',
                                                  'kind': 'package',
                                                  'name': 'python3-cephfs'}],
                                    'status': True}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)
        validator.ceph_updates()
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 2
        assert "On or more of your minions have updates pending that might cause ceph-daemons to restart. This might extend the duration of this Stage depending on your cluster size." in validator.warnings['ceph_updates'][0]
        assert "Experienced trouble refreshing the repositories" in validator.warnings['refresh_repos'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_no_ceph_updates(self, mock_localclient):
        """
        no updates
        repos refresh works
        """
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})
        fake_data = {'admin.ceph': {'packages': [],
                                    'status': True},
                     'data1.ceph': {'packages': [],
                                    'status': True}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)
        validator.ceph_updates()
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 0

    @patch('salt.client.LocalClient', autospec=True)
    def test_no_ceph_updates_1(self, mock_localclient):
        """
        no updates
        repos refresh doesn't work for one node
        """
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})
        fake_data = {'admin.ceph': {'packages': [],
                                    'status': False},
                     'data1.ceph': {'packages': [],
                                    'status': True}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)
        validator.ceph_updates()
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 1
        assert "Experienced trouble refreshing the repositories" in validator.warnings['refresh_repos'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_salt_updates(self, mock_localclient):
        """
        updates
        repo refresh works
        """
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})
        fake_data = {'admin.ceph': {'packages': [{'arch': 'x86_64',
                                                  'name': 'ceph'},
                                                  {'arch': 'x86_64',
                                                  'name': 'salt-minion'}],
                                    'status': True},
                     'data1.ceph': {'packages': [{'arch': 'x86_64',
                                                  'name': 'ceph'},
                                                  {'arch': 'x86_64',
                                                  'name': 'salt-master'}],
                                    'status': True}}
        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)
        validator.salt_updates()
        assert len(validator.errors) == 1
        assert len(validator.warnings) == 0
        assert "You have a salt update pending" in validator.errors['salt_updates'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_salt_updates_1(self, mock_localclient):
        """
        updates
        repo refresh works on one node
        """
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})
        fake_data = {'admin.ceph': {'packages': [{'arch': 'x86_64',
                                                  'name': 'ceph'},
                                                  {'arch': 'x86_64',
                                                  'name': 'salt-minion'}],
                                    'status': False},
                     'data1.ceph': {'packages': [{'arch': 'x86_64',
                                                  'name': 'ceph'},
                                                  {'arch': 'x86_64',
                                                  'name': 'salt-master'}],
                                    'status': True}}
        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)
        validator.salt_updates()
        assert len(validator.errors) == 1
        assert len(validator.warnings) == 1
        assert "You have a salt update pending" in validator.errors['salt_updates'][0]
        assert "Experienced trouble refreshing repositories" in validator.warnings['refresh_repos'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_no_salt_updates(self, mock_localclient):
        """
        updates present
        refresh works
        """
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})
        fake_data = {'admin.ceph': {'packages': [],
                                    'status': True},
                     'data1.ceph': {'packages': [],
                                    'status': True}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)
        validator.salt_updates()
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 0

    @patch('salt.client.LocalClient', autospec=True)
    def test_no_salt_updates_1(self, mock_localclient):
        """
        updates present
        refresh failed on one node
        """
        validate.__utils__ = {'deepsea_minions.show': lambda: '*'}
        validate.__utils__.update({'deepsea_minions.matches': lambda: ['node1', 'node2']})
        fake_data = {'admin.ceph': {'packages': [],
                                    'status': False},
                     'data1.ceph': {'packages': [],
                                    'status': True}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)
        validator.salt_updates()
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 1
        assert "Experienced trouble refreshing repositories" in validator.warnings['refresh_repos'][0]


    @patch('salt.client.LocalClient', autospec=True)
    def test_storage(self, mock_localclient):
        fake_data = {'node1': {'roles': 'storage',
                               'ceph': {'storage': 'dummy_osds'}},
                     'node2': {'roles': 'storage',
                               'ceph': {'storage': 'dummy_osds'}},
                     'node3': {'roles': 'storage',
                               'ceph': {'storage': 'dummy_osds'}},
                     'node4': {'roles': 'storage',
                               'ceph': {'storage': 'dummy_osds'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.passed) == 0
        validator.storage()
        assert validator.passed['storage'] == 'valid'

    @patch('salt.client.LocalClient', autospec=True)
    def test_storage_missing_attribute(self, mock_localclient):
        fake_data = {'node1': {'roles': 'storage',
                               'ceph': {'storage': 'dummy_osds'}},
                     'node2': {'roles': 'storage',
                               'ceph': {'storage': 'dummy_osds'}},
                     'node3': {'roles': 'storage',
                               'ceph': {'storage': 'dummy_osds'}},
                     'node4': {'roles': 'storage'}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.errors) == 0
        validator.storage()
        assert "missing storage attribute" in validator.errors['storage'][0]

    @patch('salt.client.LocalClient', autospec=True)
    def test_storage_too_few(self, mock_localclient):
        fake_data = {'node1': {'roles': 'storage',
                               'ceph': {'storage': 'dummy_osds'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        assert len(validator.errors) == 0
        validator.storage()
        assert "Too few storage nodes" in validator.errors['storage'][0]

    @patch('salt.client.LocalClient')
    def test_check_installed_succeeds(self, mock_localclient):
        fake_data = {'admin.ceph': {'ceph-common': {'version': '13.0.1'}},
                     'data.ceph': {'ceph-common': {'version': '13.0.1'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup")

        validator._check_installed()
        assert 'ceph_version' not in validator.errors

    @patch('salt.client.LocalClient')
    def test_rgw_succeeds(self, mock_localclient):
        fake_data = {'node1': {'roles': 'rgw'}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        validator.rgw()
        assert 'rgw' not in validator.errors

    @patch('salt.client.LocalClient')
    def test_rgw_fails(self, mock_localclient):
        fake_data = {'node1': {'roles': 'rgw-ssl',
                               'rgw_configurations': 'rgw-ssl',
                               'rgw_init': 'default-ssl'}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_pillar=True)

        validator.rgw()
        assert 'rgw' in validator.errors

    @patch('salt.client.LocalClient')
    def test_check_installed_is_older(self, mock_localclient):
        fake_data = {'admin.ceph': {'ceph-common': {'version': '10.1.1'}},
                     'data.ceph': {'ceph-common': {'version': '13.0.1'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup")

        validator._check_installed()
        assert 'admin.ceph' in validator.errors['ceph_version']

    @patch('salt.client.LocalClient')
    def test_check_installed_has_broken_version(self, mock_localclient):
        fake_data = {'admin.ceph': {'ceph-common': {'nope': 'x.x.x'}},
                     'data.ceph': {'ceph-common': {'version': '13.0.1'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup")

        validator._check_installed()
        assert 'admin.ceph' in validator.errors['ceph_version']

    @patch('salt.client.LocalClient')
    def test_check_installed_is_not_installed(self, mock_localclient):
        fake_data = {'admin.ceph': 'ERROR: package ceph-common is not installed',
                     'data.ceph': {'ceph-common': {'version': '13.0.1'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup")

        validator._check_installed()
        assert 'admin.ceph' in validator.uninstalled

    @patch('salt.client.LocalClient')
    def test_check_available_succeeds(self, mock_localclient):
        fake_data = {'admin.ceph': {'ceph-common': {'version': '13.0.1'}},
                     'data.ceph': {'ceph-common': {'version': '13.0.1'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup")

        validator.uninstalled = ['admin.ceph', 'data.ceph']
        validator._check_available()
        assert 'ceph_version' not in validator.errors

    @patch('salt.client.LocalClient')
    def test_check_available_succeeds_with_no_minions(self, mock_localclient):
        validator = validate.Validate("setup")

        validator.uninstalled = []
        validator._check_available()
        assert 'ceph_version' not in validator.errors

    @patch('salt.client.LocalClient')
    def test_check_available_is_older(self, mock_localclient):
        fake_data = {'admin.ceph': {'ceph-common': {'version': '10.1.1'}},
                     'data.ceph': {'ceph-common': {'version': '13.0.1'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup")

        validator.uninstalled = ['admin.ceph']
        validator._check_available()
        assert 'admin.ceph' in validator.errors['ceph_version']

    @patch('salt.client.LocalClient')
    def test_check_available_has_broken_version(self, mock_localclient):
        fake_data = {'admin.ceph': {'ceph-common': {'nope': 'x.x.x'}},
                     'data.ceph': {'ceph-common': {'version': '13.0.1'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup")

        validator.uninstalled = ['admin.ceph']
        validator._check_available()
        assert 'admin.ceph' in validator.errors['ceph_version']

    @patch('salt.client.LocalClient')
    def test_check_available_has_no_repo(self, mock_localclient):
        fake_data = {'admin.ceph': '',
                     'data.ceph': {'ceph-common': {'version': '13.0.1'}}}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup")

        validator.uninstalled = ['admin.ceph']
        validator._check_available()
        assert 'admin.ceph' in validator.errors['ceph_version']

    @patch('validate.DeepseaMinions')
    @patch('salt.client.LocalClient')
    def test_salt_version(self, mock_localclient, mock_deepsea):
        fake_data = { 'admin.ceph': '2018.1.99',
                      'data.ceph': '2018.1.99'}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_grains=True)

        assert len(validator.passed) == 0
        validator.salt_version()
        assert validator.passed['salt_version'] == 'valid'

    @patch('salt.client.LocalClient')
    def test_salt_version(self, mock_localclient):
        fake_data = { 'admin.ceph': '2018.1.99',
                      'data.ceph': '2018.1.99'}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_grains=True)

        assert len(validator.passed) == 0
        validator.salt_version()
        assert validator.passed['salt_version'] == 'valid'

    @patch('salt.client.LocalClient')
    def test_salt_version_unsupported(self, mock_localclient):
        fake_data = { 'admin.ceph': '2016.11.9',
                      'data.ceph': '2018.1.99'}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = validate.Validate("setup", search_grains=True)

        assert len(validator.warnings) == 0
        validator.salt_version()
        assert 'not supported' in validator.warnings['salt_version'][0]

    class MockedValidate(validate.Validate):
        """ This Class just exists to use a defined pillar """
        def set_pillar(self):
            self.data = {'admin.ceph': {'roles': 'admin'},
                         'igw1.ceph': {'roles': 'igw'}}

    @patch('salt.client.LocalClient')
    def test_kernel(self, mock_localclient):
        fake_data = {'admin.ceph': True,
                     'igw1.ceph': True}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = self.MockedValidate("kernel")
        validator.set_pillar()

        assert len(validator.passed) == 0
        validator.kernel()
        assert validator.passed['kernel_module'] == 'valid'


    @patch('salt.client.LocalClient')
    def test_kernel_wrong(self, mock_localclient):
        fake_data = {'admin.ceph': True,
                     'igw1.ceph': False}

        local = mock_localclient.return_value
        local.cmd.return_value = fake_data
        validator = self.MockedValidate("kernel")
        validator.set_pillar()

        assert len(validator.passed) == 0
        validator.kernel()
        assert 'igw1.ceph:' in validator.errors['kernel_module'][0]

    class MockedValidate(validate.Validate):
        """ This Class just exists to use a defined pillar """
        def set_pillar(self):
            self.data = {'admin.ceph': {'roles': 'admin'},
                         'igw1.ceph': {'roles': 'igw'}}


class TestConfigCheck():

    @pytest.fixture(scope='class')
    def fxtr(self):
        """
        Fixture to prepopulate the 'map' attr.
        Avoid loading that from a file
        """
        with patch.object(validate.ConfigCheck, "__init__", lambda slf: None):
            cc = validate.ConfigCheck()
            cc.map = {'release1':
                        {'k1': 'v1'},
                      'release2':
                        {'k2': ['v2', 'v2.1']},
                      'release3':
                        {'k3': 'any'}}
            cc.files = ['file1', 'file2']
            cc.issues = []
            yield cc

    def test_extract_k_v(self, fxtr):
        """
        Test if ConfigObj yields a generator-type
        """
        out = fxtr.extract_k_v('dummy_filename')
        assert isinstance(out, types.GeneratorType)

    def test_compare_k_v_to_map_str(self, fxtr):
        """
        Matching k1,v1 in isinstance(map, str)
        """
        ret = fxtr.compare_k_v_to_map('k1', 'v1')
        assert ret.key == 'k1'
        assert ret.values == ['v1']
        assert ret.release == 'release1'

    def test_compare_k_v_to_map_list(self, fxtr):
        """
        Matching k2,v2 in isinstance(map, list)
        """
        ret = fxtr.compare_k_v_to_map('k2', 'v2')
        assert ret.key == 'k2'
        assert ret.values == ['v2']
        assert ret.release == 'release2'

    def test_compare_k_v_to_map_list_missmatch(self, fxtr):
        """
        Not Matching v2 in isinstance(map, list)
        """
        ret = fxtr.compare_k_v_to_map('k2', 'v3')
        assert ret.key == 'k2'
        assert ret.values == []
        assert ret.release == 'release2'

    @pytest.mark.parametrize('key', ['any_key', 'random_key', 'foo'])
    def test_compare_k_v_to_map_any(self, fxtr, key):
        """
        Any key is set in the map
        """
        ret = fxtr.compare_k_v_to_map('k3', key)
        assert ret.key == 'k3'
        assert ret.values == []
        assert ret.release == 'release3'

    def test_compare_k_v_to_map_list_missmatch_key(self, fxtr):
        """
        Not Matching k2 in 'not in kv_map'
        """
        ret = fxtr.compare_k_v_to_map('k4', 'v2')
        assert ret is None

    @pytest.mark.parametrize("test_input, expected", [
                            ('foo_bar', 'foo bar'),
                            ('bar_baz', 'bar baz'),
                            ('bar baz', 'bar baz'),
                            ('foo ', 'foo ')])
    def test_normalize_config_key(self, fxtr, test_input, expected):
        ret = fxtr.normalize_config_key(test_input)
        assert ret == expected
