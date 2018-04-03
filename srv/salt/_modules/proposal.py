# -*- coding: utf-8 -*-
# pylint: disable=fixme

"""
Generates hardware profiles for Ceph storage nodes
"""

from __future__ import absolute_import
# pylint: disable=import-error, redefined-builtin,3rd-party-module-not-gated
import logging
from salt.ext.six.moves import range
# pylint: disable=incompatible-py3-code
log = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class Proposal(object):
    """
    Generates a hardware proposal for OSDs
    """

    NVME_DRIVER = 'nvme'
    DEFAULT_DATA_R = 5
    DEFAULT_DB_R = 5

    def __init__(self, disks, **kwargs):
        """
        Initialize disk types
        """
        self.disks = disks
        self.journal_disks = []
        self.data_disks = []
        self._parse_args(kwargs)
        # we differentiate 3 kinds of drives for now
        self.nvme = [disk for disk in disks if disk['Driver'] ==
                     self.NVME_DRIVER and disk['rotational'] == '0']
        self.ssd = [disk for disk in disks if disk['Driver'] !=
                    self.NVME_DRIVER and disk['rotational'] == '0']
        self.spinner = [disk for disk in disks if disk['rotational'] == '1']
        log.warning(self.nvme)
        log.warning(self.ssd)
        log.warning(self.spinner)

    def _parse_args(self, kwargs):
        """
        Parse arguments
        """
        self.data_r = kwargs.get('ratio', self.DEFAULT_DATA_R)
        assert isinstance(self.data_r, int) and self.data_r >= 1

        self.db_r = kwargs.get('db-ratio', kwargs.get('db_ratio', self.DEFAULT_DB_R))
        assert isinstance(self.db_r, int) and self.db_r >= 1

        data_filter = kwargs.get('data', '0')
        if isinstance(data_filter, str) and data_filter.count('-') is 1:
            self.data_min = int(data_filter.split('-')[0])
            self.data_max = int(data_filter.split('-')[1])
            assert self.data_max >= self.data_min
        else:
            self.data_min = int(data_filter)
            self.data_max = 0

        # in case of bluestore db is equal to journal
        journal_filter = kwargs.get('journal', '0')
        journal_filter = kwargs.get('db', journal_filter)
        if isinstance(journal_filter, str) and journal_filter.count('-') is 1:
            self.journal_min = int(journal_filter.split('-')[0])
            self.journal_max = int(journal_filter.split('-')[1])
            assert self.journal_max >= self.journal_min
        else:
            self.journal_min = int(journal_filter)
            self.journal_max = 0

        wal_filter = kwargs.get('wal', '0')
        if isinstance(wal_filter, str) and wal_filter.count('-') is 1:
            self.wal_min = int(wal_filter.split('-')[0])
            self.wal_max = int(wal_filter.split('-')[1])
            assert self.wal_max >= self.wal_min
        else:
            self.wal_min = int(wal_filter)
            self.wal_max = 0

        self.add_leftover_as_standalone = kwargs.get('leftovers',
                                                     False)

    # TODO better name
    def create(self):
        """
        Create a proposal
        """
        proposals = {'standalone': [],
                     'nvme-ssd-spinner': [],
                     'nvme-ssd': [],
                     'nvme-spinner': [],
                     'ssd-spinner': []}
        standalone = self._filter(self.nvme + self.ssd + self.spinner,
                                  'data')
        proposals['standalone'] = self._propose_standalone(standalone)

        # uncertain how hacky this is. This branch is taken if any 2 out of
        # there lists are empty
        if sum([not self.nvme, not self.ssd, not self.spinner]) == 2:
            log.debug('found only one type of disks...proposing standalone')
            return proposals

        proposals['nvme-ssd-spinner'] = self._propose_external_db_wal(
            self._filter(self.spinner, 'data'),
            self._filter(self.ssd, 'journal'),
            self._filter(self.nvme, 'wal'))

        # create all other proposals
        configs = [('nvme', 'ssd', 'spinner'),
                   ('nvme', 'spinner', 'ssd'),
                   ('ssd', 'spinner', 'nvme')]
        for journal, data, other in configs:
            # copy the disk lists here so the proposal methods only mutate the
            # copies and we can run mutliple proposals
            _data = self._filter(getattr(self, data), 'data')
            _journal = self._filter(getattr(self, journal), 'journal')
            _other = self._filter(getattr(self, other), 'data')
            proposals['{}-{}'.format(journal, data)] = self._propose(_data, _journal, _other)
        return proposals

    # pylint: disable=dangerous-default-value
    def _propose(self, d_disks, j_disks=[], o_disks=[]):
        """
        Returns external and standalone disks
        """
        # first consume all journal disks and respective data disks as detailed
        # in ratio
        external = []
        if j_disks:
            external = self._propose_external(d_disks, j_disks)
        # then add standalones if any leftovers and if we have proposed any
        # external at all. If no data+journal proposals have been made we'd
        # just recreate everything as standalone
        standalone = []
        if (self.add_leftover_as_standalone and (d_disks or j_disks or o_disks)
                and external):
            standalone = self._propose_standalone(d_disks + j_disks + o_disks)
        return external + standalone

    def _propose_external_db_wal(self, data_disks, db_disks, wal_disks):
        """
        This method is bluestore specific. It proposes three drives for spliting
        of the db and wal on separate drives. This only makes sense if nvme, ssd
        and spinners are present
        """
        # create proposal with wal, db and data on distinct drives. Only
        # sensible when nvme, ssd and spinners are available.
        if sum([not data_disks, not db_disks, not wal_disks]) > 0:
            log.debug(('found only two types of disks...not proposing '
                       'external wal AND db'))
            return []
        assert data_disks and db_disks and wal_disks

        external = []
        while (wal_disks and len(db_disks) >= self.db_r and
               len(data_disks) >= self.db_r * self.data_r):
            wal_disk = wal_disks.pop()
            # pylint: disable=unused-variable
            for i in range(0, self.db_r):
                data_dbs = self._get_one_external_proposal(data_disks,
                                                           db_disks)
                for data_db in data_dbs:
                    for data in data_db:
                        external.append({data: {data_db[data]:
                                                _device(wal_disk)}})
        # then add standalones if any leftovers and if we have proposed any
        # external at all. If no data+journal proposals have been made we'd
        # just recreate everything as standalone
        standalone = []
        if (self.add_leftover_as_standalone and (data_disks or db_disks or
                                                 wal_disks) and external):
            standalone = self._propose_standalone(data_disks +
                                                  db_disks +
                                                  wal_disks)
        return external + standalone

    def _propose_external(self, data_disks, journal_disks):
        """
        this method proposes external journals. On bluestore this means db and
        wal on the same drive
        """
        external = []
        # lets not divide by 0
        if not journal_disks:
            return external
        while journal_disks and len(data_disks) >= self.data_r:
            external.extend(self._get_one_external_proposal(data_disks,
                                                            journal_disks))
        return external

    def _get_one_external_proposal(self, data_disks, journal_disks):
        """
        Return proposal with journal disk
        """
        _proposal = []
        journal_disk = journal_disks.pop()
        log.info('consuming {} as journal'.format(journal_disk['device']))
        # pylint: disable=unused-variable
        for i in range(0, self.data_r):
            data_disk = data_disks.pop()
            _proposal.append({_device(data_disk):
                              _device(journal_disk)})
        return _proposal

    # pylint: disable=no-self-use
    def _propose_standalone(self, disks):
        """
        Return proposal with standalone disk
        """
        standalone = []
        for disk in disks:
            log.info('proposing {} as standalone osd'.format(
                disk['Device File']))
            standalone.append({_device(disk): ''})
        return standalone

    def _filter(self, disks, d_j):
        """
        Returns disk within range
        """
        filtered = []
        min_ = getattr(self, '{}_min'.format(d_j))
        max_ = getattr(self, '{}_max'.format(d_j))
        for disk in disks:
            cap = int(disk['Capacity'].split(' ')[0])
            if min_ <= cap:
                if not max_ or cap <= max_:
                    filtered.append(disk)
        return filtered


def _device(drive):
    """
    Default to Device File value.  Use by-id if available.
    """
    if 'Device Files' in drive:
        for path in drive['Device Files'].split(', '):
            if 'by-id' in path:
                return path
    # fallback to Device File if no by-id path was found
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
    disks = __salt__['cephdisks.list'](**kwargs)
    proposal = Proposal(disks, **kwargs)
    return proposal.create()


def test(**kwargs):
    """
    Runtime test case
    """
    disks = [
        # 12 spinners
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sda',
         'Device Files':
             ('/dev/sda, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c18240b47a526, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_0026a5470b24183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c18240b47a526, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:0:0'),
         'Device Number': 'block 8:0-8:15 (char 21:0)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '0026a5470b24183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:0:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:0/0:2:0:0',
         'SysFS ID': '/class/block/sda',
         'Unique ID': 'R7kM.0TLCB5BniZD',
         'Vendor': 'DELL',
         'device': 'sda',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdb',
         'Device Files':
             ('/dev/sdb, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c183d0cc8e637, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_0037e6c80c3d183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c183d0cc8e637, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:1:0'),
         'Device Number': 'block 8:16-8:31 (char 21:1)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '0037e6c80c3d183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:1:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:1/0:2:1:0',
         'SysFS ID': '/class/block/sdb',
         'Unique ID': 'uI_Q.HJm7aEFBSS9',
         'Vendor': 'DELL',
         'device': 'sdb',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdc',
         'Device Files':
             ('/dev/sdc, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c18500df0096c, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_006c09f00d50183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c18500df0096c, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:2:0'),
         'Device Number': 'block 8:32-8:47 (char 21:2)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '006c09f00d50183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:2:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:2/0:2:2:0',
         'SysFS ID': '/class/block/sdc',
         'Unique ID': 'LUEV.WaO0Q0E8lxA',
         'Vendor': 'DELL',
         'device': 'sdc',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdd',
         'Device Files':
             ('/dev/sdd, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c185e0eba17ba, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_00ba17ba0e5e183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c185e0eba17ba, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:3:0'),
         'Device Number': 'block 8:48-8:63 (char 21:3)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '00ba17ba0e5e183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:3:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:3/0:2:3:0',
         'SysFS ID': '/class/block/sdd',
         'Unique ID': 'ofUZ.aNUy_q62Ji4',
         'Vendor': 'DELL',
         'device': 'sdd',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sde',
         'Device Files':
             ('/dev/sde, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c186c0f99b9d4, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_00d4b9990f6c183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c186c0f99b9d4, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:4:0'),
         'Device Number': 'block 8:64-8:79 (char 21:4)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '00d4b9990f6c183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:4:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:4/0:2:4:0',
         'SysFS ID': '/class/block/sde',
         'Unique ID': 'Frkd.pMflbBww4y1',
         'Vendor': 'DELL',
         'device': 'sde',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdf',
         'Device Files':
             ('/dev/sdf, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c1877103c2c1d, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_001d2c3c1077183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c1877103c2c1d, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:5:0'),
         'Device Number': 'block 8:80-8:95 (char 21:5)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '001d2c3c1077183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:5:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:5/0:2:5:0',
         'SysFS ID': '/class/block/sdf',
         'Unique ID': 'i0+h.6ayK5lc4Xt9',
         'Vendor': 'DELL',
         'device': 'sdf',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdg',
         'Device Files':
             ('/dev/sdg, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c188310f26f9b, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_009b6ff21083183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c188310f26f9b, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:6:0'),
         'Device Number': 'block 8:96-8:111 (char 21:6)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '009b6ff21083183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:6:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:6/0:2:6:0',
         'SysFS ID': '/class/block/sdg',
         'Unique ID': 'ACFm.267Pl1OCWDF',
         'Vendor': 'DELL',
         'device': 'sdg',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdh',
         'Device Files':
             ('/dev/sdh, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c188d118d3cf4, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_00f43c8d118d183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c188d118d3cf4, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:7:0'),
         'Device Number': 'block 8:112-8:127 (char 21:7)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '00f43c8d118d183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:7:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:7/0:2:7:0',
         'SysFS ID': '/class/block/sdh',
         'Unique ID': 'dNVq.HxnexyYOPED',
         'Vendor': 'DELL',
         'device': 'sdh',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdi',
         'Device Files':
             ('/dev/sdi, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c189e12889493, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_00939488129e183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c189e12889493, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:8:0'),
         'Device Number': 'block 8:128-8:143 (char 21:8)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '00939488129e183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:8:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:8/0:2:8:0',
         'SysFS ID': '/class/block/sdi',
         'Unique ID': '4Zlu.X4kNWjyyCAF',
         'Vendor': 'DELL',
         'device': 'sdi',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdj',
         'Device Files':
             ('/dev/sdj, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c18ad1370a306, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_0006a37013ad183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c18ad1370a306, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:9:0'),
         'Device Number': 'block 8:144-8:159 (char 21:9)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '0006a37013ad183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:9:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:9/0:2:9:0',
         'SysFS ID': '/class/block/sdj',
         'Unique ID': 'Xk+y.nVICJcxw+20',
         'Vendor': 'DELL',
         'device': 'sdj',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdk',
         'Device Files':
             ('/dev/sdk, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c18b81419956d, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_006d951914b8183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c18b81419956d, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:10:0'),
         'Device Number': 'block 8:160-8:175 (char 21:10)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '006d951914b8183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:10:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:10/0:2:10:0',
         'SysFS ID': '/class/block/sdk',
         'Unique ID': '_vF1.mkw5XL+tam3',
         'Vendor': 'DELL',
         'device': 'sdk',
         'rotational': '1'},
        {'Attached to': '#31 (RAID bus controller)',
         'Bytes': '1999844147200',
         'Capacity': '1862 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'PERC H700',
         'Device File': '/dev/sdl',
         'Device Files':
             ('/dev/sdl, '
              '/dev/disk/by-id/scsi-36b82a720ce6af3001b3c18c214aeff83, '
              '/dev/disk/by-id/scsi-SDELL_PERC_H700_0083ffae14c2183c1b00f36ace20a782, '
              '/dev/disk/by-id/wwn-0x6b82a720ce6af3001b3c18c214aeff83, '
              '/dev/disk/by-path/pci-0000:02:00.0-scsi-0:2:11:0'),
         'Device Number': 'block 8:176-8:191 (char 21:11)',
         'Driver': 'megaraid_sas, sd',
         'Driver Modules': 'megaraid_sas, sd_mod',
         'Geometry (Logical)': 'CHS 243133/255/63',
         'Hardware Class': 'disk',
         'Model': 'DELL PERC H700',
         'Parent ID': 'B35A.z2vxpHnh8UC',
         'Revision': '2.10',
         'Serial ID': '0083ffae14c2183c1b00f36ace20a782',
         'Size': '3905945600 sectors a 512 bytes',
         'SysFS BusID': '0:2:11:0',
         'SysFS Device Link':
             '/devices/pci0000:00/0000:00:04.0/0000:02:00.0/host0/target0:2:11/0:2:11:0',
         'SysFS ID': '/class/block/sdl',
         'Unique ID': 'R5W5.sSJzSkkNkUB',
         'Vendor': 'DELL',
         'device': 'sdl',
         'rotational': '1'},
        # 6 ssds
        {'Attached to': '#20 (SATA controller)',
         'Bytes': '400088457216',
         'Capacity': '372 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'SSDSC2BA40',
         'Device File': '/dev/sdm',
         'Device Files':
             ('/dev/sda, '
              '/dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTHV6082036J400NGN, '
              '/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTHV6082036J400NGN, '
              '/dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTHV6082036J400NGN, '
              '/dev/disk/by-id/scsi-355cd2e404c1c976d, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40BTHV6082036J400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTHV6082036J400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA4BTHV6082036J400NGN, '
              '/dev/disk/by-id/wwn-0x55cd2e404c1c976d, '
              '/dev/disk/by-path/pci-0000:00:11.4-ata-1, '
              '/dev/disk/by-path/pci-0000:00:11.4-scsi-0:0:0:0'),
         'Device Number': 'block 8:0-8:15',
         'Driver': 'ahci, sd',
         'Driver Modules': 'ahci, sd_mod',
         'Geometry (Logical)': 'CHS 48641/255/63',
         'Hardware Class': 'disk',
         'Model': 'INTEL SSDSC2BA40',
         'Parent ID': 'bXTC.c01btg+k4h5',
         'Revision': '0140',
         'Serial ID': 'BTHV6082036J400NGN',
         'Size': '781422768 sectors a 512 bytes',
         'SysFS BusID': '0:0:0:0',
         'SysFS Device Link': '/devices/pci0000:00/0000:00:11.4/ata1/host0/target0:0:0/0:0:0:0',
         'SysFS ID': '/class/block/sda',
         'Unique ID': '3OOL.gD3AJLHgvM9',
         'Vendor': 'INTEL',
         'device': 'sdm',
         'rotational': '0'},
        {'Attached to': '#20 (SATA controller)',
         'Bytes': '400088457216',
         'Capacity': '372 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'SSDSC2BA40',
         'Device File': '/dev/sdn',
         'Device Files':
             ('/dev/sdb, '
              '/dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTHV608203DY400NGN, '
              '/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTHV608203DY400NGN, '
              '/dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTHV608203DY400NGN, '
              '/dev/disk/by-id/scsi-355cd2e404c1c9869, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40BTHV608203DY400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTHV608203DY400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA4BTHV608203DY400NGN, '
              '/dev/disk/by-id/wwn-0x55cd2e404c1c9869, '
              '/dev/disk/by-path/pci-0000:00:11.4-ata-2, '
              '/dev/disk/by-path/pci-0000:00:11.4-scsi-1:0:0:0'),
         'Device Number': 'block 8:16-8:31',
         'Driver': 'ahci, sd',
         'Driver Modules': 'ahci, sd_mod',
         'Geometry (Logical)': 'CHS 48641/255/63',
         'Hardware Class': 'disk',
         'Model': 'INTEL SSDSC2BA40',
         'Parent ID': 'bXTC.c01btg+k4h5',
         'Revision': '0140',
         'Serial ID': 'BTHV608203DY400NGN',
         'Size': '781422768 sectors a 512 bytes',
         'SysFS BusID': '1:0:0:0',
         'SysFS Device Link': '/devices/pci0000:00/0000:00:11.4/ata2/host1/target1:0:0/1:0:0:0',
         'SysFS ID': '/class/block/sdb',
         'Unique ID': 'WZeP.NratckjVAa1',
         'Vendor': 'INTEL',
         'device': 'sdn',
         'rotational': '0'},
        {'Attached to': '#29 (SATA controller)',
         'Bytes': '400088457216',
         'Capacity': '372 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'SSDSC2BA40',
         'Device File': '/dev/sdo',
         'Device Files':
             ('/dev/sdc, '
              '/dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTHV608204Y8400NGN, '
              '/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTHV608204Y8400NGN, '
              '/dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTHV608204Y8400NGN, '
              '/dev/disk/by-id/scsi-355cd2e404c1c9f4e, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40BTHV608204Y8400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTHV608204Y8400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA4BTHV608204Y8400NGN, '
              '/dev/disk/by-id/wwn-0x55cd2e404c1c9f4e, '
              '/dev/disk/by-path/pci-0000:00:1f.2-ata-1, '
              '/dev/disk/by-path/pci-0000:00:1f.2-scsi-4:0:0:0'),
         'Device Number': 'block 8:32-8:47',
         'Driver': 'ahci, sd',
         'Driver Modules': 'ahci, sd_mod',
         'Geometry (Logical)': 'CHS 48641/255/63',
         'Hardware Class': 'disk',
         'Model': 'INTEL SSDSC2BA40',
         'Parent ID': 'w7Y8.6FPgl8dOW95',
         'Revision': '0140',
         'Serial ID': 'BTHV608204Y8400NGN',
         'Size': '781422768 sectors a 512 bytes',
         'SysFS BusID': '4:0:0:0',
         'SysFS Device Link': '/devices/pci0000:00/0000:00:1f.2/ata5/host4/target4:0:0/4:0:0:0',
         'SysFS ID': '/class/block/sdc',
         'Unique ID': '_kuT.K30QsLOGbmF',
         'Vendor': 'INTEL',
         'device': 'sdo',
         'rotational': '0'},
        {'Attached to': '#29 (SATA controller)',
         'Bytes': '400088457216',
         'Capacity': '372 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'SSDSC2BA40',
         'Device File': '/dev/sdp',
         'Device Files':
             ('/dev/sdd, '
              '/dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTHV608203EN400NGN, '
              '/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTHV608203EN400NGN, '
              '/dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTHV608203EN400NGN, '
              '/dev/disk/by-id/scsi-355cd2e404c1c9881, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40BTHV608203EN400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTHV608203EN400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA4BTHV608203EN400NGN, '
              '/dev/disk/by-id/wwn-0x55cd2e404c1c9881, '
              '/dev/disk/by-path/pci-0000:00:1f.2-ata-2, '
              '/dev/disk/by-path/pci-0000:00:1f.2-scsi-5:0:0:0'),
         'Device Number': 'block 8:48-8:63',
         'Driver': 'ahci, sd',
         'Driver Modules': 'ahci, sd_mod',
         'Geometry (Logical)': 'CHS 48641/255/63',
         'Hardware Class': 'disk',
         'Model': 'INTEL SSDSC2BA40',
         'Parent ID': 'w7Y8.6FPgl8dOW95',
         'Revision': '0140',
         'Serial ID': 'BTHV608203EN400NGN',
         'Size': '781422768 sectors a 512 bytes',
         'SysFS BusID': '5:0:0:0',
         'SysFS Device Link': '/devices/pci0000:00/0000:00:1f.2/ata6/host5/target5:0:0/5:0:0:0',
         'SysFS ID': '/class/block/sdd',
         'Unique ID': 'Rw8Y.5ESts_+FXB7',
         'Vendor': 'INTEL',
         'device': 'sdp',
         'rotational': '0'},
        {'Attached to': '#29 (SATA controller)',
         'Bytes': '400088457216',
         'Capacity': '372 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'SSDSC2BA40',
         'Device File': '/dev/sdq',
         'Device Files':
             ('/dev/sde, '
              '/dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTHV611201FX400NGN, '
              '/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTHV611201FX400NGN, '
              '/dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTHV611201FX400NGN, '
              '/dev/disk/by-id/scsi-355cd2e404c1e0bfa, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40BTHV611201FX400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTHV611201FX400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA4BTHV611201FX400NGN, '
              '/dev/disk/by-id/wwn-0x55cd2e404c1e0bfa, '
              '/dev/disk/by-path/pci-0000:00:1f.2-ata-3, '
              '/dev/disk/by-path/pci-0000:00:1f.2-scsi-6:0:0:0'),
         'Device Number': 'block 8:64-8:79',
         'Driver': 'ahci, sd',
         'Driver Modules': 'ahci, sd_mod',
         'Geometry (Logical)': 'CHS 48641/255/63',
         'Hardware Class': 'disk',
         'Model': 'INTEL SSDSC2BA40',
         'Parent ID': 'w7Y8.6FPgl8dOW95',
         'Revision': '0140',
         'Serial ID': 'BTHV611201FX400NGN',
         'Size': '781422768 sectors a 512 bytes',
         'SysFS BusID': '6:0:0:0',
         'SysFS Device Link': '/devices/pci0000:00/0000:00:1f.2/ata7/host6/target6:0:0/6:0:0:0',
         'SysFS ID': '/class/block/sde',
         'Unique ID': 'u5Pc.8oYOddzSmA4',
         'Vendor': 'INTEL',
         'device': 'sdq',
         'rotational': '0'},
        {'Attached to': '#29 (SATA controller)',
         'Bytes': '400088457216',
         'Capacity': '372 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'SSDSC2BA40',
         'Device File': '/dev/sds',
         'Device Files':
             ('/dev/sdf, '
              '/dev/disk/by-id/ata-INTEL_SSDSC2BA400G4_BTHV608204YF400NGN, '
              '/dev/disk/by-id/scsi-0ATA_INTEL_SSDSC2BA40_BTHV608204YF400NGN, '
              '/dev/disk/by-id/scsi-1ATA_INTEL_SSDSC2BA400G4_BTHV608204YF400NGN, '
              '/dev/disk/by-id/scsi-355cd2e404c1c9f55, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40BTHV608204YF400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA40_BTHV608204YF400NGN, '
              '/dev/disk/by-id/scsi-SATA_INTEL_SSDSC2BA4BTHV608204YF400NGN, '
              '/dev/disk/by-id/wwn-0x55cd2e404c1c9f55, '
              '/dev/disk/by-path/pci-0000:00:1f.2-ata-4, '
              '/dev/disk/by-path/pci-0000:00:1f.2-scsi-7:0:0:0'),
         'Device Number': 'block 8:80-8:95',
         'Driver': 'ahci, sd',
         'Driver Modules': 'ahci, sd_mod',
         'Geometry (Logical)': 'CHS 48641/255/63',
         'Hardware Class': 'disk',
         'Model': 'INTEL SSDSC2BA40',
         'Parent ID': 'w7Y8.6FPgl8dOW95',
         'Revision': '0140',
         'Serial ID': 'BTHV608204YF400NGN',
         'Size': '781422768 sectors a 512 bytes',
         'SysFS BusID': '7:0:0:0',
         'SysFS Device Link': '/devices/pci0000:00/0000:00:1f.2/ata8/host7/target7:0:0/7:0:0:0',
         'SysFS ID': '/class/block/sdf',
         'Unique ID': 'LHfg.YDqu1nxjyKF',
         'Vendor': 'INTEL',
         'device': 'sds',
         'rotational': '0'},
        # 1 nvme
        {'Attached to': '#50 (Non-Volatile memory controller)',
         'Bytes': '800166076416',
         'Capacity': '745 GB',
         'Config Status': 'cfg=no, avail=yes, need=no, active=unknown',
         'Device': 'pci 0x0953 PCIe Data Center SSD',
         'Device File': '/dev/nvme1n1',
         'Device Files':
             ('/dev/nvme1n1, '
              '/dev/disk/by-id/nvme-SNVMe_INTEL_SSDPEDMD80CVFT5470001N800CGN, '
              '/dev/disk/by-path/pci-0000:81:00.0'),
         'Device Number': 'block 259:1',
         'Driver': 'nvme',
         'Driver Modules': 'nvme',
         'Geometry (Logical)': 'CHS 763097/64/32',
         'Hardware Class': 'disk',
         'Model': 'Intel DC P3700 SSD',
         'Parent ID': 'rESj.np8xWEPU5+7',
         'Revision': '0171',
         'Serial ID': 'CVFT5470001N800CGN',
         'Size': '1562824368 sectors a 512 bytes',
         'SubDevice': 'pci 0x3702 DC P3700 SSD',
         'SubVendor': 'pci 0x8086 Intel Corporation',
         'SysFS BusID': 'nvme1',
         'SysFS Device Link': '/devices/pci0000:80/0000:80:01.0/0000:81:00.0/nvme/nvme1',
         'SysFS ID': '/class/block/nvme1n1',
         'Unique ID': 'nghH.Ew4MkaIiHEF',
         'Vendor': 'pci 0x8086 Intel Corporation',
         'device': 'nvme1n1',
         'rotational': '0'}]
    proposal = Proposal(disks, **kwargs)
    return proposal.create()
