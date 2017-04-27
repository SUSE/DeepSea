# -*- coding: utf-8 -*-

import cephdisks
import logging


log = logging.getLogger(__name__)


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
        self.nvme = [disk for disk in disks if disk['Driver'] ==
                     self.NVME_DRIVER and disk['rotational'] is '0']
        self.ssd = [disk for disk in disks if disk['Driver'] !=
                    self.NVME_DRIVER and disk['rotational'] is '0']
        self.spinner = [disk for disk in disks if disk['rotational'] is '1']
        log.warn(self.nvme)
        log.warn(self.ssd)
        log.warn(self.spinner)

    def _parse_filters(self, kwargs):
        self.data_r = kwargs.get('ratio', self.DEFAULT_DATA_R)
        assert type(self.data_r) is int and self.data_r >= 1

        data_filter = kwargs.get('data', '0')
        if type(data_filter) is str and data_filter.count('-') is 1:
            self.data_min = int(data_filter.split('-')[0])
            self.data_max = int(data_filter.split('-')[1])
            assert self.data_max >= self.data_min
        else:
            self.data_min = int(data_filter)
            self.data_max = 0

        journal_filter = kwargs.get('journal', '0')
        if type(journal_filter) is str and journal_filter.count('-') is 1:
            self.journal_min = int(journal_filter.split('-')[0])
            self.journal_max = int(journal_filter.split('-')[1])
            assert self.journal_max >= self.journal_min
        else:
            self.journal_min = int(journal_filter)
            self.journal_max = 0

        self.add_leftover_as_standalone = False

    # TODO better name
    def create(self):
        proposals = {'standalone': [],
                     'nvme-ssd': [],
                     'nvme-spinner': [],
                     'ssd-spinner': []}
        standalone = self._filter(self.nvme + self.ssd + self.spinner,
                                  'data')
        proposals['standalone'] = self._propose_standalone(standalone)

        # uncertain how hacky this is. This branch is taken if any 2 out of
        # there lists is empty
        if sum([not self.nvme, not self.ssd, not self.spinner]) is 2:
            log.debug('found only one type of disks...proposing standalone')
            return proposals

        # create all other proposals
        configs = [('nvme', 'ssd', 'spinner'),
                   ('nvme', 'spinner', 'ssd'),
                   ('ssd', 'spinner', 'nvme')]
        for journal, data, other in configs:
            # copy the disk lists here so the proposal methods only mutate the
            # copies and we can run mutliple proposals
            d = self._filter(getattr(self, data), 'data')
            j = self._filter(getattr(self, journal), 'journal')
            o = self._filter(getattr(self, other), 'data')
            proposals['{}-{}'.format(journal, data)] = self._propose(d, j, o)
        return proposals

    def _propose(self, d_disks, j_disks=[], o_disks=[]):
        # first consume all journal disks and respective data disks as detailed
        # in ratio
        external = []
        if j_disks:
            external = self._propose_external(d_disks, j_disks)
        standalone = []
        # then add standalones if any leftovers
        if self.add_leftover_as_standalone and (d_disks or j_disks or o_disks):
            standalone = self._propose_standalone(d_disks + j_disks + o_disks)
        return external + standalone

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
                external.append({self._device(data_disk):
                                 self._device(journal_disk)})
        return external

    def _propose_standalone(self, disks):
        standalone = []
        for disk in disks:
            log.info('proposing {} as standalone osd'.format(
                disk['device']))
            standalone.append({self._device(disk): ''})
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
    '''
    A function to generate a storage profile proposal for ceph. It will try to
    propose 4 different setups, that depending on the hardware and the passed
    arguments might be empty. It will return (potentially empty) proposals for
    - journals on nvme, data on ssd
    - journals on nvme, data on spinners
    - journals on ssds, data on spinners and
    - only standalone OSDS.
    All unpartitioned disks will be considered.

    The OSD/journal disk ration can be influenced by passing 'ratio=6'
    meaning 6 OSDs will share one journal device (default is 5).

    'data' and 'journal' are size filters that tell the module to consider only
    drives of a certain size to be data or journal devices. Both filters can
    either be a number, which will only consider drives of an exact size , or a
    range 'min-max'. Both filters are interpreted as gigabytes.

    CLI Examples::
        salt '*' proposal.generate
        salt '*' proposal.generate ratio=7"
        salt '*' proposal.generate data="1000-3000" journal="1000"
            Only consider drives between 1TB and 3TB for data drives and 1TB
            drives for journal devices.
        salt '*' proposal.generate journal="2000"
            Consider verything for data drives and only 2TB drives for journal
            devices.

    Returns::
        {'nvme-ssd': <proposal>,
         'nvme-spinner': <proposal>,
         'ssd-spinner': <proposal>,
         'standalone': <proposal>}
    '''
    disks = cephdisks.list_(**kwargs)
    proposal = Proposal(disks, **kwargs)
    return proposal.create()
