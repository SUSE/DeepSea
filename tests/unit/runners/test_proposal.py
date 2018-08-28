from srv.modules.runners import proposal
import pytest
from mock import patch, mock_open, call
import sys
from collections import namedtuple, OrderedDict

sys.path.insert(0, "srv/modules/pillar")


NUM_MINIONS = 4
@pytest.fixture
def minions():
    minion_tuple = namedtuple("minion_tuple", ["fullpath", "filename"])

    basepath = "/srv/pillar/ceph/proposals/{}/stack/default/ceph/minions/{}"
    min1_name = "data1.ceph"
    min1_filename = "{}.yml-replace".format(min1_name)
    min2_name = "data2.ceph"
    min2_filename = "{}.yml-replace".format(min2_name)
    min3_name = "data-3.ceph"
    min3_filename = "{}.yml-replace".format(min3_name)
    min4_name = "storage-node1.ceph"
    min4_filename = "{}.yml-replace".format(min4_name)
    test_minions = (
        # first minion
        {
            "tuple": minion_tuple(
                basepath.format("profile-default", min1_filename), min1_filename
            ),
            "proposal": {
                "ceph": {
                    "storage": {
                        "osds": {
                            "/dev/vdb": {
                                "format": "bluestore",
                                "old": "vdb",
                                "replace": False,
                            },
                            "/dev/vdd": {
                                "format": "bluestore",
                                "old": "vdd",
                                "replace": True,
                            },
                            "/dev/vdc": {
                                "format": "bluestore",
                                "old": "vdc",
                                "replace": True,
                            },
                        }
                    }
                }
            },
            "disks": [
                {"Device File": "/dev/vdc", "Device Files": "/dev/vdc"},
                {"Device File": "/dev/vdb", "Device Files": "/dev/vdb"},
                {"Device File": "/dev/vdd", "Device Files": "/dev/vdd"},
            ],
            "expected": {
                "proposal_basename": "{}.yml".format(min1_name),
                "proposal_basepath": basepath.format(
                    "profile-default", "{}.yml".format(min1_name)
                ),
                "name": min1_name,
                "unused_disks": ['/dev/vdc', '/dev/vdd'],
                "proposal": {
                    "ceph": {
                        "storage": {
                            "osds": {
                                "/dev/vdb": {"format": "bluestore", "old": "vdb"},
                                "/dev/vdc": {"format": "bluestore", "old": "vdc"},
                                "/dev/vdd": {"format": "bluestore", "old": "vdd"},
                            }
                        }
                    }
                },
            },
        },
        # second minion
        {
            "tuple": minion_tuple(
                basepath.format("profile-backup", min2_filename), min2_filename
            ),
            "proposal": {
                "ceph": {
                    "storage": {
                        "osds": {
                            "/dev/v_d_b": {"format": "bluestore", "old": "v_d_b"},
                            "/dev/v_d_d": {
                                "format": "bluestore",
                                "old": "v_d_d",
                                "replace": True,
                            },
                            "/dev/v_d_c": {
                                "format": "bluestore",
                                "old": "v_d_c",
                                "replace": True,
                            },
                            "/dev/v_d_e": {"format": "bluestore", "old": "v_d_e"},
                        }
                    }
                }
            },
            "disks": [
                {"Device File": "/dev/vdc", "Device Files": "/dev/vdc, /dev/v_d_c"},
                {"Device File": "/dev/vdb", "Device Files": "/dev/vdb, /dev/v_d_b"},
                {"Device File": "/dev/vde", "Device Files": "/dev/vde, /dev/v_d_e"},
                {"Device File": "/dev/vdf", "Device Files": "/dev/vdf, /dev/v_d_f"},
            ],
            "expected": {
                "proposal_basename": "{}.yml".format(min2_name),
                "proposal_basepath": basepath.format(
                    "profile-backup", "{}.yml".format(min2_name)
                ),
                "name": min2_name,
                "unused_disks": ['/dev/v_d_c', '/dev/v_d_f'],
                "proposal": {
                    "ceph": {
                        "storage": {
                            "osds": {
                                "/dev/v_d_b": {"format": "bluestore", "old": "v_d_b"},
                                "/dev/v_d_c": {"format": "bluestore", "old": "v_d_c"},
                                "/dev/v_d_e": {"format": "bluestore", "old": "v_d_e"},
                                "/dev/v_d_f": {"format": "bluestore", "old": "v_d_d"},
                            }
                        }
                    }
                },
            },
        },
        # third minion
        {
            "tuple": minion_tuple(
                basepath.format("profile-default", min3_filename), min3_filename
            ),
            "proposal": {
                "ceph": {
                    "storage": {
                        "osds": {
                            "/dev/vdc": {
                                "format": "bluestore",
                                "old": "vdc",
                                "replace": True,
                            },
                            "/dev/vde": {"format": "bluestore", "old": "vde"},
                        }
                    }
                }
            },
            "disks": [
                {"Device File": "/dev/vdb", "Device Files": "/dev/vdb"},
                {"Device File": "/dev/vde", "Device Files": "/dev/vde"},
            ],
            "expected": {
                "proposal_basename": "{}.yml".format(min3_name),
                "proposal_basepath": basepath.format(
                    "profile-default", "{}.yml".format(min3_name)
                ),
                "name": min3_name,
                "unused_disks": ['/dev/vdb'],
                "proposal": {
                    "ceph": {
                        "storage": {
                            "osds": {
                                "/dev/vdb": {"format": "bluestore", "old": "vdc"},
                                "/dev/vde": {"format": "bluestore", "old": "vde"},
                            }
                        }
                    }
                },
            },
        },
        # fourth minion
        {
            "tuple": minion_tuple(
                "/srv/pillar/ceph/proposal/profile-default/stack/default/minions/we.use.a-very?weird-naming.scheme/{}".format(
                    min4_filename
                ),
                min4_filename,
            ),
            "proposal": {
                "ceph": {
                    "storage": {
                        "osds": {
                            "/dev/vdb": {"format": "bluestore", "old": "vdb"},
                            "/dev/vdc": {"format": "bluestore", "old": "vdc"},
                            "/dev/vdd": {"format": "bluestore", "old": "vdd"},
                            "/dev/vdf": {"format": "bluestore", "old": "vdf"},
                        }
                    }
                }
            },
            "disks": [
                {"Device File": "/dev/vdb", "Device Files": "/dev/vdb"},
                {"Device File": "/dev/vdc", "Device Files": "/dev/vdc"},
                {"Device File": "/dev/vdd", "Device Files": "/dev/vdd"},
                {"Device File": "/dev/vdf", "Device Files": "/dev/vdf"},
            ],
            "expected": {
                "proposal_basename": "{}.yml".format(min4_name),
                "proposal_basepath": "/srv/pillar/ceph/proposal/profile-default/stack/default/minions/we.use.a-very?weird-naming.scheme/{}".format(
                    "{}.yml".format(min4_name)
                ),
                "name": min4_name,
                "unused_disks": [],
                "proposal": {
                    "ceph": {
                        "storage": {
                            "osds": {
                                "/dev/vdb": {"format": "bluestore", "old": "vdb"},
                                "/dev/vdc": {"format": "bluestore", "old": "vdc"},
                                "/dev/vdd": {"format": "bluestore", "old": "vdd"},
                                "/dev/vdf": {"format": "bluestore", "old": "vdf"},
                            }
                        }
                    }
                },
            },
        },
    )
    return test_minions


class TestProposalRunner(object):
    @patch("srv.modules.runners.proposal.isfile", autospec=True)
    @patch("os.listdir", autospec=True)
    def test_find_minions_to_replace(self, mock_listdir, mock_isfile):
        mock_listdir.return_value = ["data1.ceph.yml-replace"]
        mock_isfile.return_value = True
        directory = "/srv/pillar/ceph/proposals/profile-default"
        result = proposal._find_minions_to_replace(directory)

        assert result[0].filename == "data1.ceph.yml-replace"

    @patch("srv.modules.runners.proposal.isfile", autospec=True)
    @patch("os.listdir", autospec=True)
    def test_find_multiple_minions_to_replace(self, mock_listdir, mock_isfile):
        mock_listdir.return_value = ["data1.ceph.yml-replace", "data2.ceph.yml-replace"]
        mock_isfile.return_value = True
        directory = "/srv/pillar/ceph/proposals/profile-default"
        result = proposal._find_minions_to_replace(directory)

        assert result[0].filename == "data1.ceph.yml-replace"
        assert result[1].filename == "data2.ceph.yml-replace"

    @patch("srv.modules.runners.proposal.isfile", autospec=True)
    @patch("os.listdir", autospec=True)
    def test_find_minions_to_replace_no_result(self, mock_listdir, mock_isfile):
        mock_listdir.return_value = [".data1.ceph.yml-replace.swp"]
        mock_isfile.return_value = True
        directory = "/srv/pillar/ceph/proposals/profile-default"
        result = proposal._find_minions_to_replace(directory)

        assert not result

    class NoInitReplaceDisk(proposal.ReplaceDiskOn):
        """ Don't populate attributes via private methods automatically """

        def __init__(self, minion):
            self.minion = minion

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    def test_proposal_basepath(self, execution_number, minions):
        minion = minions[execution_number]
        RD = self.NoInitReplaceDisk(minion["tuple"])

        assert RD._proposal_basepath() == minion["expected"]["proposal_basepath"]

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    def test_proposal_basename(self, execution_number, minions):
        minion = minions[execution_number]
        RD = self.NoInitReplaceDisk(minion["tuple"])

        assert RD._proposal_basename() == minion['expected']["proposal_basename"]

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    def test_minion_name_from_file(self, execution_number, minions):
        minion = minions[execution_number]
        RD = self.NoInitReplaceDisk(minion["tuple"])
        RD.proposal_basename = minion['expected']['proposal_basename']

        assert RD._minion_name_from_file() == minion['expected']["name"]

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    @patch("srv.modules.runners.proposal.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_proposal(self, mock_yaml, mock_file, execution_number, minions):
        minion = minions[execution_number]
        mock_yaml.return_value = minion['proposal']
        RD = self.NoInitReplaceDisk(minion['tuple'])

        assert RD._load_proposal() == minion['proposal']
        mock_yaml.assert_called_once()

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    @patch("salt.client.LocalClient", autospec=True)
    def test_query_node_disks(self, mock_client, execution_number, minions):
        minion = minions[execution_number]
        local_client = mock_client.return_value
        call1 = call(minion['expected']['name'], "mine.flush", tgt_type="compound")
        call2 = call(minion['expected']['name'], "mine.update", tgt_type="compound")
        call3 = call(minion['expected']['name'], "cephdisks.list", tgt_type="compound")
        RD = self.NoInitReplaceDisk(minion)
        RD.name = minion['expected']['name']

        RD._query_node_disks()

        assert local_client.cmd.call_count == 3
        assert local_client.cmd.call_args_list == [call1, call2, call3]

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    @patch("salt.client.LocalClient", autospec=True)
    def test_prepare_device_file(self, mock_client, execution_number, minions):
        minion = minions[execution_number]
        local_client = mock_client.return_value

        RD = self.NoInitReplaceDisk(minion)
        RD.proposal = minion['proposal']
        RD.disks = minion["disks"]
        RD.name = minion['expected']["name"]
        RD._prepare_device_files()
        assert local_client.cmd.call_count == len(minion['expected']['unused_disks'])

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    def test_strip_replace_flages(self, execution_number, minions):
        minion = minions[execution_number]
        RD = self.NoInitReplaceDisk(minion["tuple"])
        RD.proposal = minion['proposal']
        osds_dict = minion['proposal']['ceph']['storage']['osds']
        RD.flagged_replace = sorted([
            x for x in osds_dict if "replace" in osds_dict[x]
        ])

        RD._strip_replace_flags()

        for conf in RD.proposal["ceph"]["storage"]["osds"].values():
            assert "replace" not in conf

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    def test_swap_disks_in_proposal(self, execution_number, minions):
        minion = minions[execution_number]
        RD = self.NoInitReplaceDisk(minion["tuple"])
        RD.proposal = minion['proposal']
        osds_dict = minion['proposal']['ceph']['storage']['osds']
        RD.flagged_replace = sorted([
            x for x in osds_dict if "replace" in osds_dict[x]
        ])
        RD.unused_disks = minion['expected']['unused_disks']
        # a copy is required since RD.unused_disks will be destroyed
        keys_to_add = RD.unused_disks[:]

        RD._swap_disks_in_proposal()

        for i in range(len(minion['expected']['unused_disks'])):
            assert keys_to_add[i] in RD.proposal["ceph"]["storage"]["osds"]

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    @patch("salt.client.LocalClient")
    @patch("srv.modules.runners.proposal.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_replace(
        self, mock_yaml, mock_file, mock_client, execution_number, minions
    ):
        minion = minions[execution_number]
        mock_yaml.return_value = minion['proposal']

        RD = proposal.ReplaceDiskOn(minion["tuple"])
        # salt client has different returns so instead of settings its
        # return value we set the disks and device_files directly and re-run
        # methods that depend on those
        RD.disks = minion["disks"]
        RD.unused_disks = minion['expected']['unused_disks']
        import ipdb; ipdb.set_trace()

        RD.replace()

        mock_yaml.assert_called()
        # it seems that the expected proposal (from @fixture minions) gets sorted by pytest, sorting
        # the modified proposal lets the test pass
        result = OrderedDict(sorted(RD.proposal.items()))
        result == minion["expected"]["proposal"]
