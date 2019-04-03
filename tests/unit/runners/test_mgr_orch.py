# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4

import pytest
from mock import patch
from srv.modules.runners import mgr_orch
from tests.unit.helper.output import OutputHelper


class TestMgrOrch():
    @pytest.fixture(scope='module')
    def output_helper(self):
        yield OutputHelper()

    @patch('salt.client.LocalClient', autospec=True)
    def test_get_inventory(self, localclient, output_helper):
        result = {
            "admin.ceph": [],
            "data1.ceph": output_helper.cephdisks_output
        }

        local = localclient.return_value
        local.cmd.return_value = result

        mgr_orch.get_inventory()

        local.cmd.assert_called_with(
            "I@cluster:ceph", 'cephdisks.all', [], tgt_type="compound")

    @patch('salt.client.LocalClient', autospec=True)
    def test_get_inventory_1_node(self, localclient):
        local = localclient.return_value
        mgr_orch.get_inventory(nodes='data1.ceph')
        local.cmd.assert_called_with(
            "I@cluster:ceph and ( data1.ceph )",
            'cephdisks.all', [],
            tgt_type="compound")

    @patch('salt.client.LocalClient', autospec=True)
    def test_get_inventory_1_role(self, localclient):
        local = localclient.return_value
        mgr_orch.get_inventory(roles='mon')
        local.cmd.assert_called_with(
            "I@cluster:ceph and ( I@roles:mon )",
            'cephdisks.all', [],
            tgt_type="compound")

    @patch('salt.client.LocalClient', autospec=True)
    def test_get_inventory_multiple_nodes_or_roles(self, localclient):
        local = localclient.return_value
        mgr_orch.get_inventory(
            nodes=['admin.ceph', 'data1.ceph'], roles=['mon', 'mgr'])
        local.cmd.assert_called_with(
            "I@cluster:ceph and ( admin.ceph or data1.ceph or I@roles:mon or I@roles:mgr )",
            'cephdisks.all', [],
            tgt_type="compound")

    @patch('salt.client.LocalClient', autospec=True)
    @patch('srv.modules.runners.mgr_orch._run_master_module_function', autospec=True)
    def test_describe_service(self, mastermodule, localclient):
        daemon_ids = {
            "data1.ceph": {
                "host": "data1"
            },
            "data2.ceph": {
                "host": "data2"
            },
            "data3.ceph": {
                "host": "data3"
            },
            "data4.ceph": {
                "host": "data4"
            }
        }
        minion_roles = {
            "data1.ceph": ["storage", "admin", "mon", "mgr"],
            "data2.ceph": ["storage", "admin", "mon", "rgw"],
            "data3.ceph": ["storage", "admin", "mon"],
            "data4.ceph": ["storage", "mds", "igw", "ganesha"]
        }
        igw_address = {
            "data4.ceph": "172.16.1.24"
        }
        igw_take_default = {
            "data4.ceph": ""
        }

        local = localclient.return_value
        local.cmd.side_effect = [daemon_ids, minion_roles, igw_address,
            igw_take_default, igw_take_default, igw_take_default, igw_take_default]

        mastermodule.return_value = 'cephfs_data'

        services = mgr_orch.describe_service()

        local.cmd.assert_any_call(
            ("I@cluster:ceph and "
             "( I@roles:mon or I@roles:mgr or I@roles:mds or I@roles:rgw or I@roles:ganesha or I@roles:igw )"),
            'pillar.get', ['roles'],
            tgt_type="compound")

        assert services == {
            "data1.ceph": {
                "mon": {
                    "service_instance": "data1"
                },
                "mgr": {
                    "service_instance": "data1"
                }
            },
            "data2.ceph": {
                "mon": {
                    "service_instance": "data2"
                },
                "rgw": {
                    "service_instance": "data2"
                }
            },
            "data3.ceph": {
                "mon": {
                    "service_instance": "data3"
                }
            },
            "data4.ceph": {
                "mds": {
                    "service_instance": "data4"
                },
                "igw": {
                    "service_instance": "data4",
                    "service_url": "http://admin:admin@172.16.1.24:5000"
                },
                "ganesha": {
                    "service_instance": "data4",
                    "rados_config_location": "rados://cephfs_data/ganesha/conf-data4"
                }
            }
        }

    @patch('salt.client.LocalClient', autospec=True)
    def test_describe_service_igw_ipv6(self, localclient):
        daemon_ids = {"data4.ceph": {"host": "data4"}}
        minion_roles = {"data4.ceph": ["igw"]}
        igw_address = { "data4.ceph": "2001:db8::" }
        igw_take_default = { "data4.ceph": "" }

        local = localclient.return_value
        local.cmd.side_effect = [daemon_ids, minion_roles, igw_address,
            igw_take_default, igw_take_default, igw_take_default, igw_take_default]

        services = mgr_orch.describe_service(role='igw', service_id='data4')

        local.cmd.assert_any_call(
            "I@cluster:ceph and I@roles:igw",
            'pillar.get', ['roles'],
            tgt_type="compound")

        assert services == {
            "data4.ceph": {
                "igw": {
                    "service_instance": "data4",
                    "service_url": "http://admin:admin@[2001:db8::]:5000"
                },
            }
        }

    @patch('salt.client.LocalClient', autospec=True)
    def test_describe_service_1_role(self, localclient):
        daemon_ids = {
            "data1.ceph": {
                "host": "data1"
            },
            "data2.ceph": {
                "host": "data2"
            },
            "data3.ceph": {
                "host": "data3"
            }
        }
        minion_roles = {
            "data1.ceph": ["storage", "admin", "mon", "mgr"],
            "data2.ceph": ["storage", "admin", "mon", "rgw"],
            "data3.ceph": ["storage", "admin", "mon"],
        }

        local = localclient.return_value
        local.cmd.side_effect = [daemon_ids, minion_roles]

        services = mgr_orch.describe_service(role='mon')

        local.cmd.assert_called_with(
            "I@cluster:ceph and I@roles:mon",
            'pillar.get', ['roles'],
            tgt_type="compound")

        assert services == {
            "data1.ceph": {
                "mon":  {
                    "service_instance": "data1"
                }
            },
            "data2.ceph": {
                "mon":  {
                    "service_instance": "data2"
                }
            },
            "data3.ceph": {
                "mon":  {
                    "service_instance": "data3"
                }
            }
        }

    @patch('salt.client.LocalClient', autospec=True)
    def test_describe_service_role_plus_id(self, localclient):
        daemon_ids = {"data2.ceph": {"host": "data2"}}
        minion_roles = {"data2.ceph": ["storage", "admin", "mon", "rgw"]}

        local = localclient.return_value
        local.cmd.side_effect = [daemon_ids, minion_roles]

        services = mgr_orch.describe_service(role='rgw', service_id='data2')

        local.cmd.assert_called_with(
            "I@cluster:ceph and I@roles:rgw",
            'pillar.get', ['roles'],
            tgt_type="compound")

        assert services == {"data2.ceph": {"rgw": { "service_instance": "data2" } } }

    @patch('salt.client.LocalClient', autospec=True)
    def test_describe_service_role_wrong_id(self, localclient):
        daemon_ids = {"data2.ceph": {"host": "data2"}}
        minion_roles = {"data2.ceph": ["storage", "admin", "mon", "rgw"]}

        local = localclient.return_value
        local.cmd.side_effect = [daemon_ids, minion_roles]

        services = mgr_orch.describe_service(role='rgw', service_id='data4')

        local.cmd.assert_called_with(
            "I@cluster:ceph and I@roles:rgw",
            'pillar.get', ['roles'],
            tgt_type="compound")

        assert services == {}

    @patch('salt.client.LocalClient', autospec=True)
    def test_describe_service_node(self, localclient):
        daemon_ids = {"data1.ceph": {"host": "data1"}}
        minion_roles = {"data1.ceph": ["storage", "admin", "mon", "mgr"]}

        local = localclient.return_value
        local.cmd.side_effect = [daemon_ids, minion_roles]

        services = mgr_orch.describe_service(node='data1.ceph')

        local.cmd.assert_called_with((
            "I@cluster:ceph and "
            "( I@roles:mon or I@roles:mgr or I@roles:mds or I@roles:rgw or I@roles:ganesha or I@roles:igw ) and data1.ceph"
        ),
                                     'pillar.get', ['roles'],
                                     tgt_type="compound")

        assert services == {
            "data1.ceph": {
                "mon": {
                    "service_instance": "data1"
                },
                "mgr": {
                    "service_instance": "data1"
                }
            }
        }
