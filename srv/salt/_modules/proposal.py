# -*- coding: utf-8 -*-

import cephdisks
import logging


log = logging.getLogger(__name__)

'''
This module will propose OSD layouts for the local machine. It uses
cephdisks.list.
'''


class Proposal(object):

    NVME_DRIVER = 'nvme'
    DEFAULT_DATA_R = 5

    def __init__(self, disks, **kwargs):
        self.disks = disks
        self.journal_disks = []
        self.data_disks = []
        self.unassigned_disks = []
        self._parse_filters(kwargs)
        # we differentiate 3 kinds of drives for now
        self.nvmes = [disk for disk in disks if disk['Driver'] ==
                      self.NVME_DRIVER and disk['rotational'] is '0']
        self.ssds = [disk for disk in disks if disk['Driver'] !=
                     self.NVME_DRIVER and disk['rotational'] is '0']
        self.spinners = [disk for disk in disks if disk['rotational'] is '1']
        log.warn(self.nvmes)
        log.warn(self.ssds)
        log.warn(self.spinners)

    def _parse_filters(self, kwargs):
        ratio = kwargs.get('ratio', '')
        if ratio.count(':') is 1:
            self.data_r = int(ratio.split(':')[0])
            self.journal_r = int(ratio.split(':')[1])
        else:
            self.data_r = self.DEFAULT_DATA_R
            self.journal_r = 1
        assert self.data_r >= self.journal_r

        data_filter = kwargs.get('data', '0')
        if data_filter.count(':') is 1:
            self.data_min = int(data_filter.split(':')[0])
            self.data_max = int(data_filter.split(':')[1])
            assert self.data_max >= self.data_min
        else:
            self.data_min = int(data_filter)
            self.data_max = 0

        journal_filter = kwargs.get('journal', '0')
        if journal_filter.count(':') is 1:
            self.journal_min = int(journal_filter.split(':')[0])
            self.journal_max = int(journal_filter.split(':')[1])
            assert self.journal_max >= self.journal_min
        else:
            self.journal_min = int(journal_filter)
            self.journal_max = 0

    # TODO better name
    def create(self):
        # uncertain how hacky this is. This branch is taken if any 2 out of
        # there lists is empty
        if sum([not self.nvmes, not self.ssds, not self.spinners]) is 2:
            # short cut when only one type is present, concatenate all 3 lists
            log.debug('found only one type of disks...proposing standalone')
            standalone = self._filter(self.nvmes + self.ssds + self.spinners,
                                      'data')
            return {'standalone': self._propose(standalone)}
        # create all proposals
        configs = [('nvmes', 'ssds', 'spinners'),
                   ('nvmes', 'spinners', 'ssds'),
                   ('ssds', 'spinners', 'nvmes')]
        proposals = {}
        for journal, data, other in configs:
            # copy the disk lists here so the proposal methods only mutate the
            # copies and we can run mutliple proposals
            d = self._filter(getattr(self, data), 'data')
            j = self._filter(getattr(self, journal), 'journal')
            o = self._filter(getattr(self, other), 'data')
            proposal = self._propose(d, j, o)
            if proposal:
                proposals['{}:{}'.format(journal, data)] = proposal
        return proposals

    def _propose(self, d_disks, j_disks=[], o_disks=[]):
        # first consume all journal disks and respective data disks as detailed
        # in ratio
        external = []
        if j_disks:
            external = self._propose_external(d_disks, j_disks)
        standalone = []
        # then add standalones if any leftovers
        if d_disks or j_disks or o_disks:
            standalone = self._propose_standalone(d_disks + j_disks + o_disks)
        if not external and not standalone:
            # don't return empty proposals
            return None
        else:
            return {'data+journals': external, 'osds': standalone}

    def _propose_external(self, data_disks, journal_disks):
        external = []
        # lets not divide by 0
        if not journal_disks:
            return external
        while journal_disks and len(data_disks) >= self.data_r:
            journal_disk = journal_disks.pop()
            log.info('consuming {} as journal'.format(journal_disk['device']))
            for i in range(0, self.data_r):
                data_disk = data_disks.pop()
                external.append('{}: {}'.format(
                    self._device(data_disk),
                    self._device(journal_disk)))
        return external

    def _propose_standalone(self, leftovers):
        standalone = []
        for leftover in leftovers:
            log.info('proposing {} as standalone osd'.format(
                leftover['device']))
            standalone.append(self._device(leftover))
        return standalone

    def _filter(self, disks, d_j):
        filtered = []
        min_ = getattr(self, '{}_min'.format(d_j))
        max_ = getattr(self, '{}_max'.format(d_j))
        for disk in disks:
            cap = int(disk['Capacity'].split(' ')[0])
            if min_ <= cap:
                if not max_ or cap <= max_:
                    filtered.append(disk)
        return filtered

    def _device(self, drive):
        """
        Default to Device File value.  Use by-id if available.
        """
        if 'Device Files' in drive:
            for path in drive['Device Files'].split(', '):
                if 'by-id' in path:
                    return path
        else:
            return drive['Device File']


def generate(**kwargs):
    disks = cephdisks.list_(**kwargs)
    proposal = Proposal(disks, **kwargs)
    return proposal.create()
