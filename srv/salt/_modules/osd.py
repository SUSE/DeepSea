# -*- coding: utf-8 -*-

import os
import glob
import rados
import json
import logging
import time
import re
import pprint
import yaml
import salt.client
from subprocess import call, Popen, PIPE

log = logging.getLogger(__name__)

"""
The first functions are different queries for osds.  These can be combined.

The two classes should be combined as well.  I thought I would wait for now.
"""


# These first three methods should be combined... saving for later
def paths():
    """
    Return an array of pathnames
    """
    return [ pathname for pathname in glob.glob("/var/lib/ceph/osd/*") ]

def devices():
    """
    Return an array of devices
    """
    paths = [ pathname for pathname in glob.glob("/var/lib/ceph/osd/*") ]
    devices = []
    with open('/proc/mounts') as mounts:
        for line in mounts:
            device, path = line.split()[:2]
            if path in paths:
                devices.append(device)

    return devices

def pairs():
    """
    Return an array of devices and paths
    """
    paths = [ pathname for pathname in glob.glob("/var/lib/ceph/osd/*") ]
    pairs = []
    with open('/proc/mounts') as mounts:
        for line in mounts:
            partition, path = line.split()[:2]
            if path in paths:
                m = re.match(r'^(.+)\d+$', partition)
                device = m.group(1)
                if 'nvme' in device:
                    device = device[:-1]
                pairs.append([ device, path ])

    return pairs

def _filter_devices(devices, **kwargs):
    """
    Filter devices if provided.

    Only supporting format currently.
    """
    if 'format' in kwargs:
        devices = [ device for device in devices if devices[device]['format'] == kwargs['format'] ]

    return devices

def configured(**kwargs):
    """
    Return the osds from the ceph namespace or original namespace, optionally
    filtered by attributes.
    """
    osds = []
    devices = []
    # That doesn't allow mixed configurations
    # storage[osds] OR storage[data+journals]
    # TODO: append devices from one config version
    if ('ceph' in __pillar__ and 'storage' in __pillar__['ceph']
        and 'osds' in __pillar__['ceph']['storage']):
        devices = __pillar__['ceph']['storage']['osds']
        devices = _filter_devices(devices, **kwargs)
        devices = devices.keys()
    if 'storage' in __pillar__ and 'osds' in __pillar__['storage']:
        devices = __pillar__['storage']['osds']
        log.debug("devices: {}".format(devices))
        if 'format' in kwargs and kwargs['format'] != 'filestore':
            return []
    if 'storage' in __pillar__ and 'data+journals' in __pillar__['storage']:
        [devices.append(x.keys()[0]) for x in __pillar__['storage']['data+journals']]
    log.debug("devices: {}".format(devices))

    return devices

def list():
    """
    Return the array of ids.
    """
    return [ path.split('-')[1] for path in glob.glob("/var/lib/ceph/osd/*") if '-' in path ]

def ids():
    """
    Synonym for list
    """
    return list()

class OSDState(object):
    """
    Manage the OSD state
    """

    def __init__(self, id, **kwargs):
        """
        Initialize settings, connect to Ceph cluster
        """
        self.id = id
        self.settings = {
            'conf': "/etc/ceph/ceph.conf" ,
            'filename': '/var/run/ceph/osd.{}-weight'.format(id),
            'timeout': 3600,
            'delay': 6
        }
        self.settings.update(kwargs)
        self.cluster=rados.Rados(conffile=self.settings['conf'])
        self.cluster.connect()

    def down(self):
        """
        """
        print self.osd_tree()


    def osd_tree(self):
        """
        """
        cmd = json.dumps({"prefix":"osd tree", "format":"json" })
        ret,output,err = self.cluster.mon_command(cmd, b'', timeout=6)
        log.debug(json.dumps((json.loads(output)['nodes']), indent=4))
        for entry in json.loads(output)['nodes']:
            print entry
            if entry['id'] == self.id:
                return entry
        log.warn("ID {} not found".format(self.id))
        return {}

    def wait(self):
        """
        Wait until PGs reach 0 or timeout expires
        """
        i = 0
        while i < self.settings['timeout']/self.settings['delay']:
            entry = self.osd_tree()
            if 'pgs' in entry:
                if entry['pgs'] == 0:
                    log.info("osd.{} has no PGs".format(self.id))
                    return
                else:
                    log.warn("osd.{} has {} PGs remaining".format(self.id, entry['pgs']))
            else:
                log.warn("osd.{} does not exist".format(self.id))
                return
            i += 1
            time.sleep(self.settings['delay'])

        log.debug("Timeout expired")
        raise RuntimeError("Timeout expired")

def down(id, **kwargs):
    """
    Set an OSD to down and wait until the status is down
    """
    o = OSDState(id, **kwargs)
    o.down()



class OSDWeight(object):
    """
    Manage the setting and restoring of OSD crush weights
    """

    def __init__(self, id, **kwargs):
        """
        Initialize settings, connect to Ceph cluster
        """
        self.id = id
        self.settings = {
            'conf': "/etc/ceph/ceph.conf" ,
            'filename': '/var/run/ceph/osd.{}-weight'.format(id),
            'timeout': 3600,
            'delay': 6
        }
        self.settings.update(kwargs)
        self.cluster=rados.Rados(conffile=self.settings['conf'])
        self.cluster.connect()

    def save(self):
        """
        Capture the current weight allowing the admin to undo simple mistakes.

        The weight file defaults to the /var/run directory and will not
        survive a reboot.
        """
        entry = self.osd_df()
        if 'crush_weight' in entry and entry['crush_weight'] != 0:
            with open(self.settings['filename'], 'w') as weightfile:
                weightfile.write("{}\n".format(entry['crush_weight']))


    def restore(self):
        """
        Set weight to previous setting
        """
        if os.path.isfile(self.settings['filename']):
            with open(self.settings['filename']) as weightfile:
                saved_weight = weightfile.read().rstrip('\n')
                log.info("Restoring weight {} to osd.{}".format(saved_weight, self.id))
                self.reweight(saved_weight)


    def reweight(self, weight):
        """
        Set the weight for the OSD
        Note: haven't found the equivalent api call for reweight
        """
        stdout = []
        stderr = []
        cmd = [ 'ceph', 'osd', 'crush', 'reweight', 'osd.{}'.format(self.id), weight ]
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        for line in proc.stdout:
            stdout.append(line.rstrip('\n'))
        for line in proc.stderr:
            stderr.append(line.rstrip('\n'))
        proc.wait()
        log.debug("Reweighting: {}".format(stderr))

    def osd_df(self):
        """
        Retrieve df entry for an osd
        """
        cmd = json.dumps({"prefix":"osd df", "format":"json" })
        ret,output,err = self.cluster.mon_command(cmd, b'', timeout=6)
        log.debug(json.dumps((json.loads(output)['nodes']), indent=4))
        for entry in json.loads(output)['nodes']:
            if entry['id'] == self.id:
                return entry
        log.warn("ID {} not found".format(self.id))
        return {}

    def wait(self):
        """
        Wait until PGs reach 0 or timeout expires
        """
        i = 0
        while i < self.settings['timeout']/self.settings['delay']:
            entry = self.osd_df()
            if 'pgs' in entry:
                if entry['pgs'] == 0:
                    log.info("osd.{} has no PGs".format(self.id))
                    return
                else:
                    log.warn("osd.{} has {} PGs remaining".format(self.id, entry['pgs']))
            else:
                log.warn("osd.{} does not exist".format(self.id))
                return
            i += 1
            time.sleep(self.settings['delay'])

        log.debug("Timeout expired")
        raise RuntimeError("Timeout expired")

def zero_weight(id, **kwargs):
    """
    Set weight to zero and wait until PGs are moved
    """
    o = OSDWeight(id, **kwargs)
    o.save()
    o.reweight('0.0')
    o.wait()
    return True

def restore_weight(id, **kwargs):
    """
    Restore the previous setting for an OSD if possible
    """
    o = OSDWeight(id, **kwargs)
    o.restore()
    return True

class OSDConfig(object):
    """
    Attributes:
    * format
      * xfs
        * raw(TBD)
        * journal
        * journal_size
      * bluestore
        * raw(TBD)
        * wal_size
        * wal_device
        * db_size
        * db_device
    * encrypted
    * capacity
    """

    V1 = 'v1'
    V2 = 'v2'
    DEFAULT_FORMAT_FOR_V1 = 'filestore'
    DEFAULT_FORMAT_FOR_V2 = 'bluestore'

    def __init__(self, device, **kwargs):
        """
        Set attributes for an OSD
        """
        filters = kwargs.get('filters', None)
        # top_level_identifiier
        self.tli = self._set_tli()
        self.device = self.set_device(device)
        self.by_id_path = device
        self.capacity = self.set_capacity()
        self.size = self.set_bytes()
        self.small = self._set_small()
        self.disk_format = self.set_format()
        self.journal = self.set_journal()
        self.journal_size = self.set_journal_size()
        self.wal_size = self.set_wal_size()
        self.wal = self.set_wal()
        self.db_size = self.set_db_size()
        self.db = self.set_db()
        # default for encryption can be retrieved from the global pillar
        self.encryption = self.set_encryption()
        log.debug("OSD config: \n{}".format(pprint.pformat(vars(self))))

    def _set_tli(self):
        """
        Return the dictionary below ceph:storage:osds, if available
        """
        if ('ceph' in __pillar__ and
           'storage' in __pillar__['ceph'] and
           'osds' in __pillar__['ceph']['storage']):
            return __pillar__['ceph']['storage']['osds']
        return None

    def set_bytes(self):
        """
        Return the bytes from the mine for this disk
        """
        disks = __salt__['mine.get'](tgt=__grains__['id'], fun='cephdisks.list')
        if disks:
            for disk in disks[__grains__['id']]:
                if disk['Device File'] == self.device:
                    return int(disk['Bytes'])
        else:
            error = "Mine on {} for cephdisks.list".format(__grains__['id'])
            log.error(error)
            raise RuntimeError(error)

    def set_device(self, device):
        """
        Return the short symlink for a by-id device path
        """
        cmd = "readlink -f {}".format(device)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        result = proc.stdout.read().rstrip()
        log.debug(pprint.pformat(result))
        log.debug(pprint.pformat(proc.stderr.read()))
        return result

    def set_capacity(self):
        """
        Return the capacity from the mine for this disk
        """
        disks = __salt__['mine.get'](tgt=__grains__['id'], fun='cephdisks.list')
        if disks:
            for disk in disks[__grains__['id']]:
                if disk['Device File'] == self.device:
                    return disk['Capacity']
        else:
            error = "Mine on {} for cephdisks.list".format(__grains__['id'])
            log.error(error)
            raise RuntimeError(error)

    def _set_small(self):
        """
        Check disk is less than 10GB, useful in VM environments
        """
        return self.size < 10000000000 # 10GB

    def _config_version(self):
        """
        Return version based on structure
        """
        if 'storage' in __pillar__ and 'osds' in __pillar__['storage']:
            return OSDConfig.V1
        if 'ceph' in __pillar__ and 'storage' in __pillar__['ceph']:
            return OSDConfig.V2

    def set_format(self):
        """
        The original structure defaults to filestore.  The structure using
        the ceph namespace defaults to bluestore.
        """
        if self._config_version() == OSDConfig.V1:
            # Needs there be checks if the device is actually there?
            # I think that stack.py takes care of removing the old entry..
            # but that also means you can have EITHER the new version
            # OR the old version..
            return OSDConfig.DEFAULT_FORMAT_FOR_V1
        if self._config_version() == OSDConfig.V2:
            if 'format' in self.tli[self.device]:
                return __pillar__['ceph']['storage']['osds'][self.device]['format']
            return OSDConfig.DEFAULT_FORMAT_FOR_V2

        raise("Probably a parsing Error or something not written to the pillar yet..")

    def set_journal(self, default=False):
        """
        Return the journal device, if defined
        """
        if self._config_version() == OSDConfig.V1:
            struct = __pillar__['storage']['data+journals']
            # struct is a list of dicts
            base_devices = [osddata.keys()[0] for osddata in struct]
            # to use 'in' reduce to list of strs
            if self.device in base_devices:
                # find value in in original struct
                journal = [x[self.device] for x in struct if self.device in x]
                return journal[0]
            else:
                log.info("No journal specified for {}".format(self.device))
        if self._config_version() == OSDConfig.V2:
            if (self.device in self.tli and
               'journal' in self.tli[self.device]):
                return self.tli[self.device]['journal']
            else:
                log.info("No journal specified for {}".format(self.device))
        return default


    def _check_existence(self, key, ident, device, default=None):
        """
        Check that key exists and return value
        """
        if key in ident[device]:
            return ident[device][key]
        return default

    def set_journal_size(self, default=None):
        """
        Return journal size if defined.  Otherwise, return a size that is
        10% of the corresponding disk if the disk is under 10GB.  For larger
        disks, return 5G.
        """
        if self._config_version() == OSDConfig.V1:
            return self._journal_default()
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('journal_size', self.tli, self.device, default=self._journal_default())

    def _journal_default(self):
        """
        """
        if self.journal:
            disks = __salt__['mine.get'](tgt=__grains__['id'], fun='cephdisks.list')
            if disks:
                for disk in disks[__grains__['id']]:
                    # Check size of journal disk
                    if disk['Device File'] == self.journal:
                        if int(disk['Bytes']) < 10000000000: # 10GB
                            return "{}K".format(int(int(disk['Bytes']) * 0.0001))
                        else:
                            return "5242880K"
                log.error("Journal {} not found in cephdisks.list mine".format(self.journal))
        else:
            # Journal is same as OSD
            if self.small:
                if self.size:
                    return "{}K".format(int(int(self.size) * 0.0001))
                log.error("Size for {} not found in cephdisks.list mine".format(self.device))
            else:
                return "5242880K"

    def set_wal_size(self, default=None):
        """
        Return the size of the wal, if defined
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('wal_size', self.tli, self.device, default=default)

    def set_wal(self):
        """
        Return the device of the wal, if defined
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('wal', self.tli, self.device)

    def set_db_size(self, default=None):
        """
        Return the size of the db, if defined
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('db_size', self.tli, self.device, default=default)

    def set_db(self):
        """
        Return the device of the db, if defined
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('db', self.tli, self.device)

    def set_encryption(self, default=False):
        """
        Return the type of encryption
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('encryption', self.tli, self.device, default=default)

class OSDPartitions(object):
    """
    Manage the creation/deletion of partitions related to OSDs
    """

    def __init__(self, config):
        """
        """
        self.osd = config
        self.disks = __salt__['mine.get'](tgt=__grains__['id'], fun='cephdisks.list')

    def partition(self):
        """
        """
        if self.osd.disk_format == 'filestore':
            self._xfs_partitions(self.osd.device, self.osd.size)
        if self.osd.disk_format == 'bluestore':
            self._bluestore_partitions(self.osd.device)
        return 0

    def _xfs_partitions(self, device, disk_size):
        """
        Create partitions when journal_size is specified, use a default when
        journal_size is not specified and do nothing when neither journal nor
        journal_size are specified.
        """
        log.debug("xfs_paritions: {} {}".format(device, disk_size))
        if self.osd.journal:
            if self.osd.journal_size:
                if self.osd.journal == device:
                    # Create journal of journal_size, data as remainder
                    self.create(self.osd.journal, [('journal', self.osd.journal_size), ('osd', None)])
                else:
                    # Create journal of journal_size on journal device
                    # and data partition on whole disk of device
                    self.create(self.osd.journal, [('journal', self.osd.journal_size)])
                    self.create(self.osd.device, [('osd', None)])
            else:
                if self.osd.journal == self.osd.device:
                    # Create journal, data as remainder
                    self.create(self.osd.device, [('journal', self.osd.journal_size),
                                                 ('osd', None)])
                else:
                    # Create journal on journal device
                    # and data partition on whole disk of device
                    self.create(self.osd.journal, [('journal', self.osd.journal_size)])
                    self.create(self.osd.device, [('osd', None)])
        else:
            log.debug("xfs_paritions: no journal")
            if self.osd.journal_size:
                # Create journal of journal_size, data as remainder
                self.create(self.osd.device, [('journal', self.osd.journal_size), ('osd', None)])
            elif self.osd.small:
                # Create journal, data as remainder
                self.create(self.osd.device, [('journal', self.osd.journal_size),
                                              ('osd', None)])

        log.debug("xfs_paritions: leaving")

    def _double(self, size):
        """
        Double the value of numeral
        """
        log.info("double {}".format(size))
        numeral = int(size[0:-1])
        suffix = size[-1]
        return "{}{}".format(numeral * 2, suffix)


    def _halve(self, size):
        """
        Halve the value of numeral
        """
        log.info("halve {}".format(size))
        numeral = int(size[0:-1])
        suffix = size[-1]
        return "{}{}".format(int(numeral / 2), suffix)

    def _bluestore_partitions(self, device):
        """
        Create partitions when wal_size and/or db_size is specified
        """
        if (self.osd.device == self.osd.wal or
           self.osd.device == self.osd.db):
            # Create OSD first, if necessary
            self.create(self.osd.device, [('osd', '100M')])

        if self.osd.wal and self.osd.db:
            if self.osd.wal:
                if self.osd.wal_size:
                    # Create wal of wal_size on wal device
                    self.create(self.osd.wal, [('wal', self.osd.wal_size)])
            else:
                if self.osd.wal_size:
                    # Create wal of wal_size on device
                    self.create(self.osd.device, [('wal', self.osd.wal_size)])

            if self.osd.db:
                if self.osd.db_size:
                    # Create db of db_size on db device
                    self.create(self.osd.db, [('db', self.osd.db_size)])
            else:
                if self.osd.db_size:
                    # Create db of db_size on device
                    self.create(self.osd.device, [('db', self.osd.db_size)])
        else:
            # This situation seems unintentional - use faster media for
            # the wal or db but not the other.  Help newbies out by
            # putting wal and db on same device
            if self.osd.wal:
                if self.osd.wal_size:
                    # Create wal of wal_size on wal device
                    # Create db on wal device
                    log.warn("Setting db to same device {} as wal".format(self.osd.wal))
                    self.create(self.osd.wal, [('wal', self.osd.wal_size),
                                             ('db', self._halve(self.osd.wal_size))])
            else:
                if self.osd.wal_size:
                    # Create wal of wal_size on device
                    # Create db on device
                    log.warn("Setting db to same device {} as wal".format(self.osd.wal))
                    self.create(self.osd.device, [('wal', self.osd.wal_size),
                                         ('db', self._halve(self.osd.wal_size))])
            if self.osd.db:
                if self.osd.db_size:
                    # Create db of db_size on db device
                    # Create wal on db device
                    log.warn("Setting wal to same device {} as db".format(self.osd.db))
                    self.create(self.osd.db, [('wal', self._double(self.osd.db_size)),
                                            ('db', self.osd.db_size)])
            else:
                if self.osd.db_size:
                    # Create db of db_size on device
                    # Create wal on device
                    log.warn("Setting wal to same device {} as db".format(self.osd.db))
                    self.create(self.osd.device, [('wal', self._double(self.osd.db_size)),
                                         ('db', self.osd.db_size)])

    def create(self, device, partitions):
        """
        Create a partition
        """
        types = {'osd': '4FBD7E29-9D25-41B8-AFD0-062C0CEFF05D',
                 'journal': '45B0969E-9B03-4F30-B4C6-B4B80CEFF106',
                 'wal': '5CE17FCE-4087-4169-B7FF-056CC58473F9',
                 'db': '30CD0809-C2B2-499C-8879-2D6B78529876',
                 'lockbox': 'FB3AABF9-D25F-47CC-BF5E-721D1816496B'}

        last_partition = self._last_partition(device)
        log.warning("last partition: {}".format(last_partition))

        index = 1
        for partition_type, size in partitions:
            number = self._increment(last_partition, index)
            if size:
                cmd = "/usr/sbin/sgdisk -n {}:0:+{} -t {}:{} {}".format(number, size, number, types[partition_type], device)
            else:
                cmd = "/usr/sbin/sgdisk -N {} -t {}:{} {}".format(number, number, types[partition_type], device)
            log.info(cmd)
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            proc.wait()
            result = proc.stdout.read()
            log.debug(pprint.pformat(result))
            log.debug(pprint.pformat(proc.stderr.read()))
            index += 1

    def _last_partition(self, device):
        """
        Return the last partition.  NVMe partitions are p1, p2 ...
        """
        nvme = False
        # Valid test?
        if 'nvme' in device:
            nvme = True

        pathnames = glob.glob("{}?*".format(device))
        if pathnames:
            partitions = sorted([ re.sub(r"{}p?".format(device), '', p) for p in pathnames ], key=int)
            last_part = int(partitions[-1].replace(device, ""))

            if nvme:
                last_part = "p{}".format(last_part)

            return last_part

        if nvme:
            return 'p0'
        return 0

    def _increment(self, partition, index):
        """
        Return the sum.  If an NVMe partition, jump through hoops.
        """
        if isinstance(partition, int):
            number = partition + index
            log.warning("increment: {}".format(number))
            return partition + index

        if 'p' in partition:
            number = int(partition.replace('p', '')) + index
            log.warning("increment: p{}".format(number))
            return "p{}".format(int(number) + index)



def partition(device):
    """
    """
    config = OSDConfig(device)
    osdp = OSDPartitions(config)
    return osdp.partition()

class OSDCommands(object):
    """
    Manage the generation of commands and checks for the ceph namespace and
    original namespace.
    """

    def __init__(self, config):
        """
        Initialize settings
        """
        self.osd = config
        self.settings = {}
        self.error = None
        self.settings.update(self._storage())
        log.debug(pprint.pformat(self.settings))

    def _storage(self):
        """
        Original structure vs. extendable structure
        """
        storage = {}
        if 'storage' in __pillar__ and 'osds' in __pillar__['storage']:
            storage['osds'] = {}
            # convert old structure
            for device in __pillar__['storage']['osds']:
                storage['osds'][device] = {}
                storage['osds'][device]['format'] = 'filestore'
                storage['osds'][device]['journal'] = ''
                storage['osds'][device]['journal_size'] = ''
                storage['osds'][device]['encryption'] = ''
            for osdconfig in __pillar__['storage']['data+journals']:
                for device, journal in osdconfig.iteritems():
                    storage['osds'][device] = {}
                    storage['osds'][device]['format'] = 'filestore'
                    storage['osds'][device]['journal'] = journal
                    storage['osds'][device]['journal_size'] = ''
                    storage['osds'][device]['encryption'] = ''
        if 'ceph' in __pillar__ and 'storage' in __pillar__['ceph']:
            storage = __pillar__['ceph']['storage']
        return storage

    def osd_partition(self):
        """
        Find the OSD partition
        """
        device = self.osd.device
        return self._highest_partition(device, 'osd')

    def is_partition(self, partition_type, device, partition):
        """
        Check partition type
        """
        types = {'osd': '4FBD7E29-9D25-41B8-AFD0-062C0CEFF05D',
                 'journal': '45B0969E-9B03-4F30-B4C6-B4B80CEFF106',
                 'wal': '5CE17FCE-4087-4169-B7FF-056CC58473F9',
                 'db': '30CD0809-C2B2-499C-8879-2D6B78529876',
                 'lockbox': 'FB3AABF9-D25F-47CC-BF5E-721D1816496B'}

        cmd = "/usr/sbin/sgdisk -i {} {}".format(partition, device)
        log.info(cmd)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        result = proc.stdout.read()
        log.debug(pprint.pformat(result))
        log.debug(pprint.pformat(proc.stderr.read()))
        id = "Partition GUID code: {}".format(types[partition_type])
        return id in result

    def _highest_partition(self, device, partition_type):
        """
        Return the highest created partition of partition type
        """
        if device:
            prefix = ""
            if 'nvme' in device:
                prefix = 'p'
            log.debug("{} device: {}".format(partition_type, device))
            pathnames = glob.glob("{}?*".format(device))
            partitions = sorted([ re.sub(r"{}p?".format(device), '', p) for p in pathnames ], key=int)
            log.debug("partitions: {}".format(partitions))
            for partition in partitions:
                log.debug("checking {}{}".format(device, partition))
                # Not confusing at all - use digit for NVMe too
                if self.is_partition(partition_type, device, partition):
                    log.debug("found {}{}".format(device, partition))
                    partition = "{}{}".format(prefix, partition)
                    return "{}".format(partition)
        self.error = "Partition type {} not found on {}".format(partition_type, device)
        log.error(self.error)
        return 0

    def _cluster_name(self):
        """
        Return the cluster name from the ceph namespace, original namespace
        or default to 'ceph'
        """
        if 'ceph' in __pillar__ and 'cluster' in __pillar__['ceph']:
            return __pillar__['ceph']['cluster']
        if 'cluster' in __pillar__:
            return __pillar__['cluster']
        return 'ceph'

    def _fsid(self):
        """
        Return the fsid from the ceph namespace, original namespace
        or default to all zeroes
        """
        if 'ceph' in __pillar__ and 'fsid' in __pillar__['ceph']:
            return __pillar__['ceph']['fsid']
        if 'fsid' in __pillar__:
            return __pillar__['fsid']
        return '00000000-0000-0000-0000-000000000000'

    def is_partitioned(self, device):
        """
        Return whether the device is already partitioned
        """
        result = glob.glob("{}?*".format(device))
        log.debug("Found {} partitions on {}".format(result, device))
        return result != []

    def _filestore_args(self):
        """
        Filestore OSDs can take multiple forms
          OSD partition, Journal partition
          OSD device, Journal device
          OSD device
        """
        device = self.osd.device
        if self.is_partitioned(device):
            # Prepartitioned OSD
            if self.osd.journal:
                args = "{}{} {}{}".format(device, self._highest_partition(device, 'osd'), self.osd.journal, self._highest_partition(self.osd.journal, 'journal'))
            else:
                args = "{}{} {}{}".format(device, self._highest_partition(device, 'osd'), device, self._highest_partition(self.osd.device, 'journal'))
        else:
            # Raw
            if self.osd.journal:
                args = "{} {}".format(device, self.osd.journal)
            else:
                args = "{}".format(device)
        return args

    def _bluestore_args(self):
        """
        Bluestore OSDs can support multiple forms
          OSD device
          OSD device, wal device
          OSD device, wal partition
          OSD device, db device
          OSD device, db partition
          OSD device, wal device, db device
          OSD device, wal partition, db device
          OSD device, wal device, db partition
          OSD device, wal partition, db partition
          OSD partition
          OSD partition, wal device
          OSD partition, wal partition
          OSD partition, db device
          OSD partition, db partition
          OSD partition, wal device, db device
          OSD partition, wal partition, db device
          OSD partition, wal device, db partition
          OSD partition, wal partition, db partition

        """
        args = ""
        if self.osd.wal and self.osd.db:
            # redundant check
            if self.osd.wal:
                if self.is_partitioned(self.osd.wal):
                    partition = self._highest_partition(self.osd.wal, 'wal')
                    if partition:
                        args = "--block.wal {}{} ".format(self.osd.wal, partition)
                    else:
                        args = "--block.wal {} ".format(self.osd.wal)
                else:
                    args = "--block.wal {} ".format(self.osd.wal)

            if self.osd.db:
            # redundant check
                if self.is_partitioned(self.osd.db):
                    partition = self._highest_partition(self.osd.db, 'db')
                    if partition:
                        args += "--block.db {}{} ".format(self.osd.db, partition)
                    else:
                        args += "--block.db {} ".format(self.osd.db)
                else:
                    args += "--block.db {} ".format(self.osd.db)
        else:
            if self.osd.wal:
                if self.is_partitioned(self.osd.wal):
                    partition = self._highest_partition(self.osd.wal, 'wal')
                    if partition:
                        args += "--block.wal {}{} ".format(self.osd.wal, partition)
                    else:
                        args += "--block.wal {} ".format(self.osd.wal)

                    partition = self._highest_partition(self.osd.wal, 'db')
                    if partition:
                        args += "--block.db {}{} ".format(self.osd.wal, partition)
                else:
                    args += "--block.wal {} ".format(self.osd.wal)

            if self.osd.db:
                if self.is_partitioned(self.osd.db):
                    partition = self._highest_partition(self.osd.db, 'db')
                    if partition:
                        args += "--block.db {}{} ".format(self.osd.db, partition)
                    else:
                        args += "--block.db {} ".format(self.osd.db)

                    partition = self._highest_partition(self.osd.db, 'wal')
                    if partition:
                        args += "--block.wal {}{} ".format(self.osd.db, partition)
                else:
                    args += "--block.db {} ".format(self.osd.db)

        # if the device is already partitioned
        # but the partitionnumber is not 1
        # this will fail
        if self.is_partitioned(self.osd.device):
            args += "{}1".format(self.osd.device)
        else:
            args += "{}".format(self.osd.device)
        return args


    def prepare(self):
        """
        Generate the correct prepare command.

        The possiblities are
          xfs
            unpartitioned disk
            partitioned disk
            two unpartitioned disks
            two partitioned disks
          bluestore
            unpartitioned disk
            two unpartitioned disks
            three unpartitioned disks
            unpartitioned disk and partitioned disk
            unpartitioned disk and two partitioned disks
            two unpartitioned disks and partitioned disk
        """
        cmd = ""
        args = ""
        if self.osd.device:
            cmd = "ceph-disk -v prepare "

            # Dmcrypt
            if self.osd.encryption == 'dmcrypt':
                cmd += "--dmcrypt "
            # Filestore
            if self.osd.disk_format == 'filestore':
                cmd += "--fs-type xfs "
                args = self._filestore_args()
            # Bluestore
            if self.osd.disk_format == 'bluestore':
                cmd += "--bluestore "
                args = self._bluestore_args()

            if not args:
                log.error("Format is neither filestore nor bluestore.")

            cmd += "--data-dev --journal-dev --cluster {} --cluster-uuid {} ".format(self._cluster_name(), self._fsid())
            cmd += args

        if self.error:
           cmd = "/bin/false # {}".format(self.error)

        log.info("prepare: {}".format(cmd))
        return cmd

    def activate(self):
        """
        Generate the correct activate command.

        Note: dmcrypt activates during the prepare step
        """
        cmd = ""
        if self.osd.device:
            if self.osd.encryption == 'dmcrypt':
                cmd = "/bin/true activated during prepare"
            else:
                cmd = "ceph-disk -v activate --mark-init systemd --mount "
                cmd += "{}{}".format(self.osd.device, self._highest_partition(self.osd.device, 'osd'))

        if self.error:
           cmd = "/bin/false # {}".format(self.error)

        log.info("activate: {}".format(cmd))
        return cmd

    def detect(self, osd_id, pathname="/var/lib/ceph/osd"):
        """
        Return the osd type
        """
        filename = "{}/ceph-{}/type".format(pathname, osd_id)
        if os.path.exists(filename):
            with open(filename, 'r') as osd_type:
                return osd_type.read().rstrip()

class OSDGrains(object):
    """
    """

    def __init__(self):
        """
        Initialize settings
        """
        pass

    def partitions(self, osd_id, pathname="/var/lib/ceph/osd"):
        """
        Returns the partitions of the OSD
        """
        partitions = {}
        mount_dir = "{}/ceph-{}".format(pathname, osd_id)
        log.info("Checking /proc/mounts for {}".format(mount_dir))
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                entry = line.split()
                if entry[1] == mount_dir:
                    log.info("line: {}".format(line))
                    partitions['osd'] = entry[0]

        for device_type in ['journal', 'block', 'block.db', 'block.wal']:
            result = self._real_devices(mount_dir, device_type)
            if result:
                partitions[device_type] = result
        return partitions

    def _real_devices(self, mount_dir, device_type):
        """
        Follow the symlinks for the current device name
        """
        symlink = "{}/{}".format(mount_dir, device_type)
        log.info("Checking for {}".format(symlink))
        if os.path.exists(symlink):
            # find real device
            cmd = "readlink -f {}".format(symlink)
            proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            proc.wait()
            result = proc.stdout.read().rstrip()
            log.debug(pprint.pformat(result))
            log.debug(pprint.pformat(proc.stderr.read()))
            return result


    def retain(self):
        """
        Save the OSD partitions into the grains
        """
        ids = [ path.split('-')[1] for path in glob.glob("/var/lib/ceph/osd/*") if '-' in path ]
        storage = {}
        for osd_id in ids:
            storage[osd_id] = self.partitions(osd_id)
            log.debug("osd {}: {}".format(osd_id, pprint.pformat(storage[osd_id])))
        self._grains(storage)


    def _grains(self, storage, filename="/etc/salt/grains"):
        """
        Load and save grains when changed
        """
        if storage:
            content = {}
            if os.path.exists(filename):
                with open(filename, 'r') as minion_grains:
                    content = yaml.safe_load(minion_grains)
            if 'ceph' in content:
                if content['ceph'] != storage:
                    content['ceph'] = storage
                    self._update_grains(content)
                else:
                    log.debug("No update for {}".format(filename))
            else:
                content['ceph'] = storage
                self._update_grains(content)

    def _update_grains(self, content, filename="/etc/salt/grains"):
        """
        Update the yaml file without destroying other content
        """
        log.info("Updating {}".format(filename))
        # Keep yaml human readable/editable
        friendly_dumper = yaml.SafeDumper
        friendly_dumper.ignore_aliases = lambda self, data: True

        with open(filename, 'w') as minion_grains:
            minion_grains.write(yaml.dump(content,
                                          Dumper=friendly_dumper,
                                          default_flow_style=False))
        log.info("Syncing grains")
        __salt__['saltutil.sync_grains']()

def is_partitioned(device):
    """
    Check if device is partitioned
    """
    osdc = OSDCommands()
    return osdc.is_partitioned(device)

def is_prepared(device):
    """
    Check if the device has already been prepared.  Return shell command.

    Note: the alternate strategy to running is_prepared as part of an unless is
    to create a state module.  However, will the admin be able to debug that
    configuration without reading python?  This task is left for later...
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    partition = osdc.osd_partition()
    if partition == 0:
        log.error("Do not know which partition to check on {}".format(device))
        return "/bin/false"

    if osdc.is_partition('osd', config.device, partition) and _fsck(config.device, partition):
        return "/bin/true"
    else:
        return "/bin/false"

def _fsck(device, partition):
    """
    Check filesystem on partition
    """
    cmd = "/sbin/fsck -n {}{}".format(device, partition)
    log.info(cmd)
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    proc.wait()
    log.debug(pprint.pformat(proc.stdout.read()))
    log.debug(pprint.pformat(proc.stderr.read()))
    log.debug("fsck: {}".format(proc.returncode))
    return proc.returncode == 0

def is_activated(device):
    """
    Check if the device has already been activated.  Return shell command.
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    partition = osdc.osd_partition()
    pathname = "{}{}".format(config.device, partition)
    log.info("Checking /proc/mounts for {}".format(pathname))
    with open("/proc/mounts", "r") as mounts:
        for line in mounts:
            if line.startswith(pathname):
                return True
    return False

def prepare(device):
    """
    Return ceph-disk command to prepare OSD.

    Note: calling the partition command directly from the sls file will not
    give the desired results since the evaluation of the prepare command (and
    the partition check) occurs prior to creating the partitions
    """
    config = OSDConfig(device)
    osdp = OSDPartitions(config)
    osdp.partition()
    osdc = OSDCommands(config)
    return osdc.prepare()

def activate(device):
    """
    Return ceph-disk command to activate OSD.
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    return osdc.activate()

def detect(osd_id):
    """
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    return osdc.detect(osd_id)


def partitions(osd_id):
    """
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    return osdc.partitions(osd_id)

def retain():
    """
    Save the OSD partitions in the local grains
    """
    osdg = OSDGrains()
    return osdg.retain()
