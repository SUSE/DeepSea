# -*- coding: utf-8 -*-

import cephdisks
import logging

log = logging.getLogger(__name__)
NVME_DRIVER = 'nvme'


class Proposal(object):

    def __init__(self, disks, **kwargs):
        self.disks = disks
        self.journal_disks = []
        self.data_disks = []
        self.unassigned_disks = []
        self._parse_filters(kwargs)
        # we differentiate 3 kinds of drives for now
        self.nvmes = [disk for disk in disks if disk['Driver'] == NVME_DRIVER
                      and disk['rotational'] is '0']
        self.ssds = [disk for disk in disks if disk['Driver'] != NVME_DRIVER
                     and disk['rotational'] is '0']
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
            self.data_r = 5
            self.journal_r = 1

        data_filter = kwargs.get('data', '0')
        if data_filter.count(':') is 1:
            self.data_min = int(data_filter.split(':')[0])
            self.data_max = int(data_filter.split(':')[1])
        else:
            self.data_min = self.data_max = int(data_filter)

        journal_filter = kwargs.get('journal', '0')
        if journal_filter.count(':') is 1:
            self.journal_min = int(journal_filter.split(':')[0])
            self.journal_max = int(journal_filter.split(':')[1])
        else:
            self.journal_min = self.journal_max = int(journal_filter)

    # TODO better name
    def create(self):
        # uncertain how hacky this is. This branch is taken if any 2 out of
        # there lists is empty
        if sum([not self.nvmes, not self.ssds, not self.spinners]) is 2:
            # short cut when only one type is present, concatenate all 3 lists
            log.debug('found only one type of disks...proposing standalone')
            return self._propose(self.nvmes + self.ssds + self.spinners)
        # create all proposals
        configs = [('nvmes', 'ssds'), ('nvmes', 'spinners'),
                   ('ssds', 'spinners')]
        proposals = []
        for journal, data in configs:
            # TODO filter here for size. what would that mean for data
            # drives...currently we'd potentially propose filtered standalone
            # osds. might be what we want though
            proposal = self._propose(getattr(self, data),
                                     getattr(self, journal))
            if proposal:
                proposals.append(proposal)
        return proposals

    def _propose(self, data_disks, journal_disks=[]):
        # first consume all journal disks and respective data disks as detailed
        # in ratio
        external = []
        if journal_disks:
            external = self._propose_external(data_disks, journal_disks)
        standalone = []
        if data_disks:
            standalone = self._propose_standalone(data_disks + journal_disks)
        if not external and not standalone:
            return None
        else:
            return {'data+journals': external, 'osds': standalone}

    def _propose_external(self, data_disks, journal_disks):
        external = []
        # lets not divide by 0
        if not journal_disks:
            return external
        ratio = len(data_disks) // len(journal_disks)
        if ratio >= self.data_r:
            while journal_disks:
                journal_disk = journal_disks.pop()
                log.info('consuming {} as journal'.format(journal_disk['device']))
                for i in range(0, self.data_r):
                    data_disk = data_disks.pop()
                    external.append('{}: {}'.format(
                        data_disk['Device File'],
                        journal_disk['Device File']))
        return external

    def _propose_standalone(self, leftovers):
        standalone = []
        for leftover in leftovers:
            log.info('proposing {} as standalone osd'.format(
                leftover['device']))
            standalone.append(leftover['Device File'])
        return standalone

    def _filter_disks(self):
        for disk in self.disks:
            # TODO if we have nvme ssd should be data
            if self._suits(disk, 'data') and disk['rotational'] is 1:
                log.debug(('disks {} rotates, candidate for data or ',
                           'osd').format(disk['device']))
                self.data_disk.append(disk)
            elif self._suits(disk, 'journal'):
                log.debug(('disk {} is solid state, candidate for ',
                           'journal or osd').format(disk['device']))
                self.journal_disk.append(disk)
            else:
                log.debug(('disk {} does not pass capacity filters',
                           '...ignored').format(disk['device']))
                self.unassigned_disk.append(disk)

    def _suits(self, disk, d_j):
        cap = int(disk['Capacity'].split(' ')[0])
        min_ = getattr(self, '{}_min'.format(d_j))
        max_ = getattr(self, '{}_max'.format(d_j))
        return min_ <= cap <= max_


def generate(**kwargs):
    disks = cephdisks.list_(**kwargs)
    proposal = Proposal(disks, **kwargs)
    return proposal.create()
