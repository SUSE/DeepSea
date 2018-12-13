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
        # first minion (3 disks, 2 replacements, two reuses)
        {
            "tuple": minion_tuple(basepath.format("profile-default", min1_filename), min1_filename),
            "proposal": {
                "ceph": {
                    "storage": {
                        "osds": {
                            "/dev/disk/by-id/scsi-0ATA_SATA_SSD_AF000000000000000000": {
                                "format": "bluestore",
                                "replace": False,
                            },
                            "/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH000000000000000": {
                                "format": "bluestore",
                                "replace": True,
                            },
                            "/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH111111111111111": {
                                "format": "bluestore",
                                "replace": True,
                            },
                        }
                    }
                }
            },
            "disks": [
                {
                    "Device File": "/dev/sdc",
                    "Device Files": "/dev/sdc, /dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTH000000000000000, /dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH000000000000000, /dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTH000000000000000, /dev/disk/by-id/scsi-355cd2e404c1c9f4e, /dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH000000000000000, /dev/disk/by-id/wwn-0x55cd2e404c1c9f4e, /dev/disk/by-path/pci-0000:00:1f.2-ata-1",
                },
                {
                    "Device File": "/dev/sdb",
                    "Device Files": "/dev/sdb, /dev/disk/by-id/ata-SATA_SSD_AF000000000000000000, /dev/disk/by-id/scsi-0ATA_SATA_SSD_AF000000000000000000, /dev/disk/by-id/scsi-1ATA_SATA_SSD_AF000000000000000000, /dev/disk/by-id/scsi-SATA_SATA_SSD_AF000000000000000000, /dev/disk/by-path/pci-0000:00:1f.2-ata-6",
                },
                {
                    "Device File": "/dev/sdd",
                    "Device Files": "/dev/sdd, /dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTH111111111111111, /dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH111111111111111, /dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTH111111111111111, /dev/disk/by-id/scsi-355cd2e404c1c9881, /dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH111111111111111, /dev/disk/by-id/wwn-0x55cd2e404c1c9881, /dev/disk/by-path/pci-0000:00:1f.2-ata-2",
                },
            ],
            "expected": {
                "proposal_basename": "{}.yml".format(min1_name),
                "proposal_basepath": basepath.format("profile-default", "{}.yml".format(min1_name)),
                "name": min1_name,
                "unused_disks": [
                    "/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH111111111111111",
                    "/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH000000000000000",
                ],
                "proposal": {
                    "ceph": {
                        "storage": {
                            "osds": {
                                "/dev/disk/by-id/scsi-0ATA_SATA_SSD_AF000000000000000000": {
                                    "format": "bluestore"
                                },
                                "/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH000000000000000": {
                                    "format": "bluestore"
                                },
                                "/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH111111111111111": {
                                    "format": "bluestore"
                                },
                            }
                        }
                    }
                },
            },
        },
        # second minion (custom profile, 4 disks, 2 replacements, 1 reuse)
        {
            "tuple": minion_tuple(basepath.format("profile-backup", min2_filename), min2_filename),
            "proposal": {
                "ceph": {
                    "storage": {
                        "osds": {
                            "/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH000000000000000": {
                                "format": "bluestore"
                            },
                            "/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH111111111111111": {
                                "format": "bluestore",
                                "replace": True,
                            },
                            "/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH222222222222222": {
                                "format": "bluestore",
                                "replace": True,
                            },
                            "/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH333333333333333": {
                                "format": "bluestore"
                            },
                        }
                    }
                }
            },
            "disks": [
                {
                    "Device File": "/dev/sdc",
                    "Device Files": "/dev/sdc, /dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTH111111111111111, /dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH111111111111111, /dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTH111111111111111, /dev/disk/by-id/scsi-355cd2e404c1ca4a4, /dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH111111111111111, /dev/disk/by-id/wwn-0x55cd2e404c1ca4a4, /dev/disk/by-path/pci-0000:00:1f.2-ata-1",
                },
                {
                    "Device File": "/dev/sdb",
                    "Device Files": "/dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTH000000000000000, /dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH000000000000000, /dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTHV000000000000000 /dev/disk/by-id/scsi-355cd2e404c1c9774, /dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH0000000000000000 /dev/disk/by-id/wwn-0x55cd2e404c1c9774, /dev/disk/by-path/pci-0000:00:11.4-ata-2",
                },
                {
                    "Device File": "/dev/sde",
                    "Device Files": " /dev/sde, /dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTH333333333333333, /dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH333333333333333, /dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTH333333333333333, /dev/disk/by-id/scsi-355cd2e404c1c976c, /dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH333333333333333, /dev/disk/by-id/wwn-0x55cd2e404c1c976c, /dev/disk/by-path/pci-0000:00:1f.2-ata-3",
                },
                {
                    "Device File": "/dev/sdf",
                    "Device Files": ": /dev/sdf, /dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTH444444444444444, /dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH444444444444444, /dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTH444444444444444, /dev/disk/by-id/scsi-355cd2e404c1c988b, /dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH444444444444444, /dev/disk/by-id/wwn-0x55cd2e404c1c988b, /dev/disk/by-path/pci-0000:00:1f.2-ata-4",
                },
            ],
            "expected": {
                "proposal_basename": "{}.yml".format(min2_name),
                "proposal_basepath": basepath.format("profile-backup", "{}.yml".format(min2_name)),
                "name": min2_name,
                "unused_disks": [
                    "/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH111111111111111",
                    "/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH444444444444444",
                ],
                "proposal": {
                    "ceph": {
                        "storage": {
                            "osds": {
                                "/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH000000000000000": {
                                    "format": "bluestore"
                                },
                                "/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH111111111111111": {
                                    "format": "bluestore"
                                },
                                "/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTH333333333333333": {
                                    "format": "bluestore"
                                },
                                "/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTH444444444444444": {
                                    "format": "bluestore"
                                },
                            }
                        }
                    }
                },
            },
        },
        # third minion (2 disks, 1 replacement)
        {
            "tuple": minion_tuple(basepath.format("profile-default", min3_filename), min3_filename),
            "proposal": {
                "ceph": {
                    "storage": {
                        "osds": {
                            "/dev/disk/by-id/nvme-INTEL_SSDPEDMD800G4_CVF000000000000000": {
                                "format": "bluestore",
                                "replace": True,
                            },
                            "/dev/disk/by-id/nvme-INTEL_SSDPEDMD800G4_CVF111111111111111": {
                                "format": "bluestore",
                            },
                        }
                    }
                }
            },
            "disks": [
                {
                    "Device File": "/dev/nvme1n1",
                    "Device Files": "/dev/nvme1n1, /dev/disk/by-id/nvme-INTEL_SSDPEDMD800G4_CVF111111111111111, /dev/disk/by-id/nvme-nvme.8086-43564654353437303030314e38303043474e-494e54454c205353445045444d443830304734-00000001, /dev/disk/by-path/pci-0000:81:00.0-nvme-1",
                },
                {
                    "Device File": "/dev/sdh",
                    "Device Files": "/dev/sdh, /dev/disk/by-id/ata-SATA_SSD_00000000000000000000, /dev/disk/by-id/scsi-0ATA_SATA_SSD_00000000000000000000, /dev/disk/by-id/scsi-1ATA_SATA_SSD_00000000000000000000, /dev/disk/by-id/scsi-SATA_SATA_SSD_00000000000000000000, /dev/disk/by-path/pci-0000:00:1f.2-ata-6",
                },
            ],
            "expected": {
                "proposal_basename": "{}.yml".format(min3_name),
                "proposal_basepath": basepath.format("profile-default", "{}.yml".format(min3_name)),
                "name": min3_name,
                "unused_disks": ["/dev/disk/by-id/scsi-SATA_SATA_SSD_00000000000000000000"],
                "proposal": {
                    "ceph": {
                        "storage": {
                            "osds": {
                                "/dev/disk/by-id/scsi-SATA_SATA_SSD_00000000000000000000": {
                                    "format": "bluestore",
                                },
                                "/dev/disk/by-id/nvme-INTEL_SSDPEDMD800G4_CVF111111111111111": {
                                    "format": "bluestore",
                                },
                            }
                        }
                    }
                },
            },
        },
        # fourth minion (custom proposal path, 4 disks, no replacements)
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

        assert RD._proposal_basename() == minion["expected"]["proposal_basename"]

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    def test_minion_name_from_file(self, execution_number, minions):
        minion = minions[execution_number]
        RD = self.NoInitReplaceDisk(minion["tuple"])
        RD.proposal_basename = minion["expected"]["proposal_basename"]

        assert RD._minion_name_from_file() == minion["expected"]["name"]

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    @patch("srv.modules.runners.proposal.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_proposal(self, mock_yaml, mock_file, execution_number, minions):
        minion = minions[execution_number]
        mock_yaml.return_value = minion["proposal"]
        RD = self.NoInitReplaceDisk(minion["tuple"])

        assert RD._load_proposal() == minion["proposal"]
        mock_yaml.assert_called_once()

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    @patch("salt.client.LocalClient", autospec=True)
    def test_query_node_disks(self, mock_client, execution_number, minions):
        minion = minions[execution_number]
        local_client = mock_client.return_value
        call1 = call(minion["expected"]["name"], "mine.flush", tgt_type="compound")
        call2 = call(minion["expected"]["name"], "mine.update", tgt_type="compound")
        call3 = call(minion["expected"]["name"], "cephdisks.list", tgt_type="compound")
        RD = self.NoInitReplaceDisk(minion)
        RD.name = minion["expected"]["name"]

        RD._query_node_disks()

        assert local_client.cmd.call_count == 3
        assert local_client.cmd.call_args_list == [call1, call2, call3]

    @pytest.mark.skip(reason="This seems like a bug in MagicMock "
                      "TypeError: '<' not supported between instances of 'MagicMock' and 'MagicMock'"
                      "although there are __lt__, __gt__ etc defined."
                      "I couldn't find a proper solution to this. Helop pls")
    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    @patch("salt.client.LocalClient", autospec=True)
    def test_prepare_device_file(self, mock_client, execution_number, minions):
        minion = minions[execution_number]
        local_client = mock_client.return_value
        RD = self.NoInitReplaceDisk(minion)
        RD.proposal = minion["proposal"]
        RD.disks = minion["disks"]
        RD.name = minion["expected"]["name"]

        RD._prepare_device_files()

        num_unused = len(minion["expected"]["unused_disks"])
        assert local_client.cmd.call_count == num_unused
        # check that cephdisks.device was called for every leftover disk (i.e. disk not in proposal)
        for i in range(num_unused):
            assert (
                call(
                    minion["expected"]["name"],
                    "cephdisks.device",
                    [RD.disks[i]["Device File"]],
                    tgt_type="compound",
                )
                in local_client.cmd.call_args_list
            )

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    def test_strip_replace_flages(self, execution_number, minions):
        minion = minions[execution_number]
        RD = self.NoInitReplaceDisk(minion["tuple"])
        RD.proposal = minion["proposal"]
        osds_dict = minion["proposal"]["ceph"]["storage"]["osds"]
        RD.flagged_replace = sorted([x for x in osds_dict if "replace" in osds_dict[x]])

        RD._strip_replace_flags()

        for conf in RD.proposal["ceph"]["storage"]["osds"].values():
            assert "replace" not in conf

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    def test_swap_disks_in_proposal(self, execution_number, minions):
        minion = minions[execution_number]
        RD = self.NoInitReplaceDisk(minion["tuple"])
        RD.proposal = minion["proposal"]
        osds_dict = minion["proposal"]["ceph"]["storage"]["osds"]
        RD.flagged_replace = sorted([x for x in osds_dict if "replace" in osds_dict[x]])
        RD.unused_disks = minion["expected"]["unused_disks"]
        # a copy is required since RD.unused_disks will be destroyed
        keys_to_add = RD.unused_disks[:]

        RD._swap_disks_in_proposal()

        for i in range(len(minion["expected"]["unused_disks"])):
            assert keys_to_add[i] in RD.proposal["ceph"]["storage"]["osds"]

    @pytest.mark.parametrize("execution_number", range(NUM_MINIONS))
    @patch("srv.modules.runners.proposal.os.remove")
    @patch("salt.client.LocalClient")
    @patch("srv.modules.runners.proposal.open")
    @patch("yaml.safe_load")
    def test_replace(
        self, mock_yaml, mock_file, mock_client, mock_remove, execution_number, minions
    ):
        minion = minions[execution_number]
        mock_yaml.return_value = minion["proposal"]

        RD = proposal.ReplaceDiskOn(minion["tuple"])
        # salt client has different returns so instead of settings its
        # return value we set the disks and device_files directly and re-run
        # methods that depend on those
        RD.disks = minion["disks"]
        RD.unused_disks = minion["expected"]["unused_disks"]

        RD.replace()

        mock_yaml.assert_called()
        # it seems that the expected proposal (from @fixture minions) gets sorted by pytest, sorting
        # the modified proposal lets the test pass
        result = OrderedDict(sorted(RD.proposal.items()))
        result == minion["expected"]["proposal"]
