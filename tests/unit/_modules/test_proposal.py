# -*- coding: utf-8 -*-

import pytest
import sys
import random
sys.path.insert(0, 'srv/salt/_modules')
from srv.salt._modules import proposal
from srv.salt._modules import helper
from tests.unit.helper.output import OutputHelper, GenHwinfo


class TestProposal(object):

    @pytest.fixture(scope='module')
    def output_helper(self):
        yield OutputHelper()

    @pytest.fixture()
    def replaced_disk_hdd(self):
        return self.replace_disk()

    @pytest.fixture()
    def replaced_disk_ssd(self):
        return self.replace_disk(type='ssd')

    @pytest.fixture()
    def replaced_disk_nvme(self):
        return self.replace_disk(type='nvme')

    def test_parse_filter(self, output_helper):
        # test defaults
        p = proposal.Proposal([])
        self.check_proposal_init(p, 5, 5, 0, 0, 0, 0)

        p = proposal.Proposal([], ratio=2, db_ratio=1,
                              data='50', journal='20')
        self.check_proposal_init(p, 2, 1, 50, 0, 20, 0)

        p = proposal.Proposal([], ratio=2, db_ratio=1,
                              data='20-50', journal='5-20')
        self.check_proposal_init(p, 2, 1, 20, 50, 5, 20)

        p = proposal.Proposal([], ratio=2, db_ratio=2,
                              data='20-50', journal='5-20')
        self.check_proposal_init(p, 2, 2, 20, 50, 5, 20)

        with pytest.raises(AssertionError):
            proposal.Proposal([], ratio=-3, data='20-50', journal='5-20')
            proposal.Proposal([], ratio=2, data='50-20', journal='5-20')
            proposal.Proposal([], ratio=2, data='50-60', journal='20-5')

        p = proposal.Proposal(output_helper.cephdisks_output)
        assert len(p.nvme) is 1
        assert len(p.ssd) is 6
        assert len(p.spinner) is 12

    def check_proposal_init(self, p, dr, dbr, dmi, dma, jmi, jma):
        assert p.data_r is dr, 'data_r not correct'
        assert p.db_r is dbr, 'db_r not correct'
        assert p.data_max is dma, 'data_max not correct'
        assert p.data_min is dmi, 'data_min not correct'
        assert p.journal_max is jma, 'journal_max not correct'
        assert p.journal_min is jmi, 'journal_min not correct'

    def test_propose_standalone(self, output_helper):
        p = proposal.Proposal(output_helper.cephdisks_output)
        expected_len = len(p.spinner)
        prop = p._propose_standalone(p.spinner)
        assert len(prop) is expected_len

    def test_propose_external(self, output_helper):
        p = proposal.Proposal(output_helper.cephdisks_output)
        prop = p._propose_external(p.ssd, p.nvme)
        assert len(prop) is p.DEFAULT_DATA_R

        p = proposal.Proposal(output_helper.cephdisks_output, ratio=2)
        expected_len = len(p.ssd) * 2
        prop = p._propose_external(p.spinner, p.ssd)
        assert len(prop) is expected_len

        p = proposal.Proposal(output_helper.cephdisks_output, ratio=3)
        expected_len = len(p.spinner)
        prop = p._propose_external(p.spinner, p.ssd)
        assert len(prop) is expected_len

    def test_propose_external_db_wal(self, output_helper):
        p = proposal.Proposal(output_helper.cephdisks_output)
        prop = p._propose_external_db_wal(p.spinner, p.ssd, p.nvme)
        assert len(prop) is 0

        r = 2
        p = proposal.Proposal(output_helper.cephdisks_output, ratio=r)
        prop = p._propose_external_db_wal(p.spinner, p.ssd, p.nvme)
        assert len(prop) is p.DEFAULT_DB_R * r

    def test_propose(self, output_helper):
        p = proposal.Proposal(output_helper.cephdisks_output)
        prop = p._propose(p.ssd, p.nvme)
        assert len(prop) is p.DEFAULT_DATA_R

        r = 4
        p = proposal.Proposal(output_helper.cephdisks_output, ratio=r,
                              leftovers=True)
        expected_len = r + (len(p.ssd) - r)
        prop = p._propose(p.ssd, p.nvme)
        assert len(prop) is expected_len

    def test_filter(self, output_helper):
        # currently the disks in output_helper.cephdisks_ouput are
        # spinners: 1862 GB
        # ssds:     372 GB
        # nvme:     745 GB
        p = proposal.Proposal(output_helper.cephdisks_output, ratio=3,
                              data='500')
        filtered = p._filter(p.spinner, 'data')
        assert len(filtered) is len(p.spinner)
        filtered = p._filter(p.ssd, 'data')
        assert len(filtered) is 0

        p = proposal.Proposal(output_helper.cephdisks_output, ratio=3,
                              data='500-800')
        filtered = p._filter(p.spinner, 'data')
        assert len(filtered) is 0
        filtered = p._filter(p.ssd, 'data')
        assert len(filtered) is 0
        filtered = p._filter(p.nvme, 'data')
        assert len(filtered) is len(p.nvme)

        p = proposal.Proposal(output_helper.cephdisks_output, ratio=3,
                              journal='500-800')
        filtered = p._filter(p.ssd, 'journal')
        assert len(filtered) is 0
        filtered = p._filter(p.nvme, 'journal')
        assert len(filtered) is len(p.nvme)

    def test_create(self, output_helper):
        p = proposal.Proposal(output_helper.cephdisks_output)
        prop = p.create()
        assert len(prop['standalone']) is (len(p.ssd) + len(p.spinner) +
                                           len(p.nvme))
        assert len(prop['ssd-spinner']) is p.DEFAULT_DATA_R * 2
        assert len(prop['nvme-ssd-spinner']) is 0
        assert len(prop['nvme-ssd']) is p.DEFAULT_DATA_R
        assert len(prop['nvme-spinner']) is p.DEFAULT_DATA_R


    def replace_disk(self, type='hdd'):
        # idx 0-11 -> HDD
        # idx 12-17 -> SSD
        # idx 18 -> NVME
        wal_db_replaced = None
        hwinfo_out = OutputHelper().cephdisks_output
        p = proposal.Proposal(OutputHelper().cephdisks_output)
        old_prop = p.create()

        # replace a HDD
        hwinfo_out_new = hwinfo_out
        replace_idx = random.randint(0, 11)
        replaced_hdd = hwinfo_out_new[replace_idx]
        del hwinfo_out_new[replace_idx]
        new_disk = GenHwinfo(type=type).generate()

        hwinfo_out_new.insert(random.randint(0, len(hwinfo_out)), new_disk)

        # gen new proposal
        new_p = proposal.Proposal(hwinfo_out_new)
        new_prop = new_p.create()

        for prop_name, prop in  old_prop.items():
            for disk_set in old_prop[prop_name]:
                # ensure that its a proposal with dedicated wal/db
                if disk_set.keys()[0] in replaced_hdd['Device Files']:
                    if prop_name in ['ssd-spinner', 'nvme-ssd-spinner', 'nvme-ssd', 'nvme-spinner']:
                        wal_db_replaced = disk_set.values()[0]
                        break

        return old_prop, new_prop, replaced_hdd, wal_db_replaced

    def is_deterministic(self, replaced_disk):
        old_prop = replaced_disk[0]
        new_prop = replaced_disk[1]
        replaced_hdd = replaced_disk[2]
        wal_db_replaced = replaced_disk[3]

        for prop_name, prop in new_prop.items():
            for disk_set in old_prop[prop_name]:
                found = [x for x in prop if disk_set == x]
                osd_disk = disk_set.keys()[0]
                wal_db = disk_set.values()[0]
                if not found and osd_disk not in replaced_hdd['Device Files']:
                    if 'GENERATED' in osd_disk:
                        if wal_db != wal_db_replaced:
                            return False, found, osd_disk, wal_db, wal_db_replaced
                if found:
                    assert osd_disk == found[0].keys()[0]
                    assert wal_db == found[0].values()[0]
                return True, [], osd_disk, wal_db, wal_db_replaced

    @pytest.mark.parametrize('execution_number', range(1, 1000))
    def test_determ_hdd(self, execution_number, replaced_disk_hdd):
        """
        This test tries to confirm determinism in profile.generate

        Theory:
        The fear is that in a 'replace' operation we _may_ end up with
        different osd - wal/db mappings than before. This would mean that
        a user will have to edit the profiles manually or face a migration.
        We never introduced pre-sorting of disk information that we get from
        hwinfo, which means that we can't guarantee a consistently sorted
        input.

        In order to test this, we try to do the following:

        1) Generate a profile
        2) 'replace' a disk ( replaced.disk() )
        2.1) Generate a 'new' disk ( suffixed with 'GENERATED' )
        2.2) Inject it a at a random index in the output from hwinfo
        2.3) Find the old, replaced disk to compare the wal/db pointer
        3) Compare the new and the old proposal for a match of
           old wal/db pointer and the new wal/db pointer

        To eliminate the factor of 'luck', repeat if 1000 times.

        Caveat:
          * Currently we are only testing if the newly replaced disk
            is matching it's old entry.
            Maybe we should test it for _every_ disk.
            OTOH, there is no difference in the generated disks and the
            'old' disks. If the proposal generator is not deterministic,
            we would have noticed it.
          * The number of repetitions could me reduced by adding more disks
            and therefore an increase in probability of a 'missplacement'


        There are complement test methods for SSDs and NVMEs

        :param execution_number:
        :param replaced_disk_hdd:
        :return:
        """
        ret, found, osd_disk, wal_db, wal_db_replaced = self.is_deterministic(replaced_disk_hdd)
        assert ret is True

    @pytest.mark.parametrize('execution_number', range(1, 1000))
    def test_determ_ssd(self, execution_number, replaced_disk_ssd):
        """
        See docstring of test_determ_hdd.

        :param execution_number:
        :param replaced_disk_ssd:
        :return:
        """
        ret, found, osd_disk, wal_db, wal_db_replaced = self.is_deterministic(replaced_disk_ssd)
        assert ret is True

    @pytest.mark.parametrize('execution_number', range(1, 1000))
    def test_determ_nvme(self, execution_number, replaced_disk_nvme):
        """
        See docstring of test_determ_hdd.

        :param execution_number:
        :param replaced_disk_nvme:
        :return:
        """
        ret, found, osd_disk, wal_db, wal_db_replaced = self.is_deterministic(replaced_disk_nvme)
        assert ret is True
