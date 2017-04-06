# -*- coding: utf-8 -*-

import pytest
from srv.salt._modules import proposal
from mock import MagicMock, patch, mock_open, mock
from helpers import OutputHelper


class TestProposal(object):

    @pytest.fixture(scope='module')
    def output_helper(self):
        yield OutputHelper()

    def test_parse_filter(self, output_helper):
        # test defaults
        p = proposal.Proposal([])
        self.check_proposal_init(p, 5, 1, 0, 0, 0, 0)

        p = proposal.Proposal([], ratio="2:1", data='50', journal='20')
        self.check_proposal_init(p, 2, 1, 50, 50, 20, 20)

        p = proposal.Proposal([], ratio="2:1", data='20:50', journal='5:20')
        self.check_proposal_init(p, 2, 1, 20, 50, 5, 20)

        with pytest.raises(AssertionError):
            proposal.Proposal([], ratio="2:3", data='20:50', journal='5:20')
            proposal.Proposal([], ratio="2:1", data='50:20', journal='5:20')
            proposal.Proposal([], ratio="2:1", data='50:60', journal='20:5')

        p = proposal.Proposal(output_helper.cephdisks_output)
        assert len(p.nvmes) is 1
        assert len(p.ssds) is 6
        assert len(p.spinners) is 12

    def check_proposal_init(self, p, dr, jr, dmi, dma, jmi, jma):
        assert p.data_r is dr, 'data_r not correct'
        assert p.journal_r is jr, 'journal_r not correct'
        assert p.data_max is dma, 'data_max not correct'
        assert p.data_min is dmi, 'data_min not correct'
        assert p.journal_max is jma, 'journal_max not correct'
        assert p.journal_min is jmi, 'journal_min not correct'

    def test_propose_standalone(self, output_helper):
        p = proposal.Proposal(output_helper.cephdisks_output)
        expected_len = len(p.spinners)
        prop = p._propose_standalone(p.spinners)
        assert len(prop) is expected_len

    def test_propose_external(self, output_helper):
        p = proposal.Proposal(output_helper.cephdisks_output)
        prop = p._propose_external(p.ssds, p.nvmes)
        assert len(prop) is p.DEFAULT_DATA_R

        p = proposal.Proposal(output_helper.cephdisks_output, ratio='2:1')
        expected_len = len(p.ssds) * 2
        prop = p._propose_external(p.spinners, p.ssds)
        assert len(prop) is expected_len

        p = proposal.Proposal(output_helper.cephdisks_output, ratio='3:1')
        expected_len = len(p.spinners)
        prop = p._propose_external(p.spinners, p.ssds)
        assert len(prop) is expected_len

    def test_propose(self, output_helper):
        p = proposal.Proposal(output_helper.cephdisks_output)
        ssds = len(p.ssds)
        prop = p._propose(p.ssds, p.nvmes)
        assert len(prop['data+journals']) is p.DEFAULT_DATA_R
        assert len(prop['osds']) is ssds - p.DEFAULT_DATA_R

        p = proposal.Proposal(output_helper.cephdisks_output, ratio='3:1')
        ext = len(p.spinners)
        alone = len(p.ssds) - len(p.spinners) / 3
        prop = p._propose(p.spinners, p.ssds)
        assert len(prop['data+journals']) is ext
        assert len(prop['osds']) is alone

        # propose one 7:1 proposal and standalones
        p = proposal.Proposal(output_helper.cephdisks_output, ratio='7:1')
        ext = len(p.spinners)
        # alone = len(p.ssds) - len(p.spinners) / 3
        prop = p._propose(p.spinners, p.ssds)
        assert len(prop['data+journals']) is 7
        assert len(prop['osds']) is 10
