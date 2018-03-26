import pytest
import salt.client
import sys
sys.path.insert(0, 'srv/salt/_modules')
sys.path.insert(0, 'srv/modules/runners')
sys.path.insert(0, 'srv/modules/runners/utils')

from mock import patch, MagicMock
from srv.modules.runners import validate

# Trivial tests to validate the unittest itself is working
def test_get_printer():
    assert(isinstance(validate.get_printer(), validate.PrettyPrinter))
    assert(isinstance(validate.get_printer('json'), validate.JsonPrinter))
    assert(isinstance(validate.get_printer('quiet'), validate.JsonPrinter))


class TestClusterAssignment():

    @patch('salt.client.LocalClient', autospec=True)
    def test_single_cluster(self, localclient):
        cluster_dict = {"minionA":"ceph", "minionB": "ceph", "minionC": "ceph"}

        local = localclient.return_value
        local.cmd.return_value = cluster_dict

        cluster = validate.ClusterAssignment(salt.client.LocalClient())
        assert len(cluster.names) == 1
        assert set(cluster.names['ceph']) == set(["minionA","minionB","minionC"])

    @patch('salt.client.LocalClient', autospec=True)
    def test_single_cluster_unassigned(self, localclient):
        cluster_dict = {"minionA":"ceph", "minionB": "ceph",
                        "minionC": "unassigned", "minionD": "ceph",
                        "minionE": "unassigned"}

        local = localclient.return_value
        local.cmd.return_value = cluster_dict

        cluster = validate.ClusterAssignment(salt.client.LocalClient())
        assert len(cluster.names) == 1
        assert set(cluster.names['ceph']) == set(["minionA","minionB","minionD"])

    @patch('salt.client.LocalClient', autospec=True)
    def test_multi_cluster_unassigned(self, localclient):
        cluster_dict = {"minionA":"ceph", "minionB": "kraken",
                        "minionC": "unassigned", "minionD": "ceph",
                        "minionE": "kraken"}

        local = localclient.return_value
        local.cmd.return_value = cluster_dict

        cluster = validate.ClusterAssignment(salt.client.LocalClient())
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
