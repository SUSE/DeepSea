# -*- coding: utf-8 -*-

import pytest
from srv.salt._modules import proposal
from tests.unit.helper.output import OutputHelper


class TestProposal(object):

    @pytest.fixture(scope='module')
    def output_helper(self):
        yield OutputHelper()

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
