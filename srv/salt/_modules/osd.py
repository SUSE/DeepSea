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
                m = re.match(r'([a-z/]+).*', partition)
                device = m.group(1)
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
    if ('ceph' in __pillar__ and 'storage' in __pillar__['ceph']
        and 'osds' in __pillar__['ceph']['storage']):
        devices = __pillar__['ceph']['storage']['osds']
        devices = _filter_devices(devices, **kwargs)
    if 'storage' in __pillar__ and 'osds' in __pillar__['storage']:
        devices = __pillar__['storage']['osds']
        log.debug("devices: {}".format(devices))
        if 'format' in kwargs and kwargs['format'] != 'xfs':
            return []
    log.debug("devices: {}".format(devices))
    for device in devices:
        # find real device
        cmd = "readlink -f {}".format(device)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        result = proc.stdout.read().rstrip()
        osds.append(result)
        log.debug(pprint.pformat(result))
        log.debug(pprint.pformat(proc.stderr.read()))
    return osds

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

def _defined(device, key):
    """
    Check if key exists and has value
    """
    if (device in __pillar__['ceph']['storage']['osds'] and
        key in __pillar__['ceph']['storage']['osds'][device] and
        __pillar__['ceph']['storage']['osds'][device][key]):
        return __pillar__['ceph']['storage']['osds'][device][key]


class OSDPartitions(object):
    """
    Manage the creation/deletion of partitions related to OSDs
    """

    def __init__(self):
        """
        """
        self.disks = __salt__['mine.get'](tgt=__grains__['id'], fun='cephdisks.list')

    def partition(self, device):
        """
        """
        for disk in self.disks[__grains__['id']]:
            if disk['Device File'] == device:
                if 'ceph' in __pillar__ and 'storage' in __pillar__['ceph']:
                    if _defined(device, 'format') == 'xfs':
                        self._xfs_partitions(device, disk['Bytes'])
                    if _defined(device, 'format') == 'bluestore':
                        self._bluestore_partitions(device)
                if ('storage' in __pillar__ and 'osds' in __pillar__['storage'] 
                    and int(disk['Bytes']) < 10000000000000): # 10GB
                    # create percentage partitions if unpartitioned
                    journal_size = "{}K".format(int(int(disk['Bytes']) * 0.0001))
                    self.create(device, [('journal', journal_size),
                                         ('osd', None)])
        return 0

    def _journal_default(self, device):
        """
        Return a default journal size when one is not provided.  Use 5G unless
        the drive is under 10G, then use 10%.
        """
        for disk in self.disks[__grains__['id']]:
            if disk['Device File'] == device:
                if int(disk['Bytes']) < 10000000000000: # 10GB
                    return "{}K".format(int(int(disk['Bytes']) * 0.0001))
                else:
                    return "5242880K"
        return 0

    def _xfs_partitions(self, device, disk_size):
        """
        Create partitions when journal_size is specified, use a default when
        journal_size is not specified and do nothing when neither journal nor 
        journal_size are specified. 
        """
        if _defined(device, 'journal'):
            if _defined(device, 'journal_size'):
                if _defined(device, 'journal') == device:
                    # Create journal of journal_size, data as remainder
                    journal_device = _defined(device, 'journal')
                    journal_size = _defined(device, 'journal_size')
                    self.create(journal_device, [('journal', journal_size), ('osd', None)])
                else:
                    # Create journal of journal_size on journal device
                    # and data partition on whole disk of device
                    journal_device = _defined(device, 'journal')
                    journal_size = _defined(device, 'journal_size')
                    self.create(journal_device, [('journal', journal_size)])
                    self.create(device, [('osd', None)])
            else:
                if _defined(device, 'journal') == device:
                    # Create journal, data as remainder
                    journal_device = _defined(device, 'journal')
                    journal_size = self._journal_default(journal_device)
                    self.create(journal_device, [('journal', journal_size), 
                                                 ('osd', None)])
                else:
                    # Create journal on journal device
                    # and data partition on whole disk of device
                    journal_device = _defined(device, 'journal')
                    journal_size = self._journal_default(journal_device)
                    self.create(journal_device, [('journal', journal_size)])
                    self.create(device, [('osd', None)])
        else:
            if _defined(device, 'journal_size'):
                # Create journal of journal_size, data as remainder
                journal_size = __pillar__['ceph']['storage'][device]['journal_size']
                self.create(device, [('journal', journal_size), ('osd', None)])

    def _double(self, size):
        """
        Double the value of numeral 
        """
        numeral = int(size[0:-1])
        suffix = size[-1]
        return "{}{}".format(numeral * 2, suffix)


    def _halve(self, size):
        """
        Halve the value of numeral
        """
        numeral = int(size[0:-1])
        suffix = size[-1]
        return "{}{}".format(int(numeral / 2), suffix)

    def _bluestore_partitions(self, device):
        """
        Create partitions when wal_size and/or db_size is specified
        """
        if ('wal' in __pillar__['ceph']['storage']['osds'][device] and
            'db' in __pillar__['ceph']['storage']['osds'][device]):
            # Use the configuration provided
            if _defined(device, 'wal'):
                if _defined(device, 'wal_size'):
                    # Create wal of wal_size on wal device
                    wal_device = _defined(device, 'wal')
                    wal_size = _defined(device, 'wal_size')
                    self.create(wal_device, [('wal', wal_size)])
            else:
                if _defined(device, 'wal_size'):
                    # Create wal of wal_size on device
                    wal_size = _defined(device, 'wal_size')
                    self.create(device, [('wal', wal_size)])

            if _defined(device, 'db'):
                if _defined(device, 'db_size'):
                    # Create db of db_size on db device
                    db_device = _defined(device, 'db')
                    db_size = _defined(device, 'db_size')
                    self.create(db_device, [('db', db_size)])
            else:
                if _defined(device, 'db_size'):
                    # Create db of db_size on device
                    db_size = _defined(device, 'db_size')
                    self.create(device, [('db', db_size)])
        else:
            # This situation seems unintentional - use faster media for
            # the wal or db but not the other.  Help newbies out by 
            # putting wal and db on same device
            if _defined(device, 'wal'):
                if _defined(device, 'wal_size'):
                    # Create wal of wal_size on wal device
                    # Create db on wal device
                    wal_device = _defined(device, 'wal')
                    wal_size = _defined(device, 'wal_size')
                    self.create(wal_device, [('wal', wal_size), 
                                             ('db', self._halve(wal_size))])
            else:
                if _defined(device, 'wal_size'):
                    # Create wal of wal_size on device
                    # Create db on device
                    wal_size = _defined(device, 'wal_size')
                    self.create(device, [('wal', wal_size), 
                                         ('db', self._halve(wal_size))])

            if _defined(device, 'db'):
                if _defined(device, 'db_size'):
                    # Create db of db_size on db device
                    # Create wal on db device
                    db_device = _defined(device, 'db')
                    db_size = _defined(device, 'db_size')
                    self.create(db_device, [('wal', self._double(db_size)), 
                                            ('db', db_size)])
            else:
                if _defined(device, 'db_size'):
                    # Create db of db_size on device
                    # Create wal on device
                    db_size = _defined(device, 'db_size')
                    self.create(device, [('wal', self._double(db_size)), 
                                         ('db', db_size)])

    def create(self, device, partitions):
        """
        Create a partition
        """
        types = {'osd': '4FBD7E29-9D25-41B8-AFD0-062C0CEFF05D',
                 'journal': '45B0969E-9B03-4F30-B4C6-B4B80CEFF106',
                 'wal': '5CE17FCE-4087-4169-B7FF-056CC58473F9',
                 'db': '30CD0809-C2B2-499C-8879-2D6B78529876'}

        last_partition = self._last_partition(device)
        index = 1
        for partition_type, size in partitions:
            number = last_partition + index
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
        """
        pathnames = glob.glob("{}?*".format(device))
        if pathnames:
            partitions = sorted([ p.replace(device, "") for p in pathnames ], key=int)
            last_part = int(pathnames[-1].replace(device, ""))
            return last_part
        return 0



def partition(device):
    """
    """
    osdp = OSDPartitions()
    return osdp.partition(device)

class OSDCommands(object):
    """
    Manage the generation of commands and checks for the ceph namespace and
    original namespace.
    """

    def __init__(self):
        """
        Initialize settings
        """
        self.settings = {}
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
                storage['osds'][device]['format'] = 'xfs'
                storage['osds'][device]['journal'] = ''
                storage['osds'][device]['journal_size'] = ''
                storage['osds'][device]['encryption'] = ''
            for device, journal in __pillar__['storage']['data+journals']:
                storage['osds'][device] = {}
                storage['osds'][device]['format'] = 'xfs'
                storage['osds'][device]['journal'] = journal
                storage['osds'][device]['journal_size'] = ''
                storage['osds'][device]['encryption'] = ''
        if 'ceph' in __pillar__ and 'storage' in __pillar__['ceph']:
            storage = __pillar__['ceph']['storage']
        return storage

    def osd_partition(self, device):
        """
        Find the data partition based on settings.

        TODO: dmcrypt
        """
        if 'osds' in self.settings and device in self.settings['osds']:
            if self.settings['osds'][device]['format'] == 'xfs':
                if self.settings['osds'][device]['journal']:
                    # Journal on separate device
                    return 1
                else:
                    # Journal on same device
                    return 2
            if self.settings['osds'][device]['format'] == 'bluestore':
                return 1
        return 0

    def _journal_device(self, device):
        """
        Return the journal from the ceph name space or original name space
        """
        if 'ceph' in __pillar__ and 'storage' in __pillar__['ceph']:
            return __pillar__['ceph']['storage']['osds'][device]['journal']
        if 'storage' in __pillar__['ceph']:
            return __pillar__['storage']['data+journals'][device]

    def is_partition(self, partition_type, device, partition):
        """
        Check partition type
        """
        types = { 'osd': '4FBD7E29-9D25-41B8-AFD0-062C0CEFF05D',
                  'journal': '45B0969E-9B03-4F30-B4C6-B4B80CEFF106',
                  'wal': '5CE17FCE-4087-4169-B7FF-056CC58473F9',
                  'db': '30CD0809-C2B2-499C-8879-2D6B78529876'}
        cmd = "/usr/sbin/sgdisk -i {} {}".format(partition, device)
        log.info(cmd)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        result = proc.stdout.read()
        log.debug(pprint.pformat(result))
        log.debug(pprint.pformat(proc.stderr.read()))
        id = "Partition GUID code: {}".format(types[partition_type])
        return id in result

    def _journal_pathname(self, device):
        """
        Return the highest created Journal pathname
        """
        journal_device = self._journal_device(device)
        if journal_device:
            log.debug("journal device: {}".format(journal_device))
            pathnames = glob.glob("{}?*".format(journal_device))
            partitions = sorted([ p.replace(journal_device, "") for p in pathnames ], key=int, reverse=True)
            log.debug("partitions: {}".format(partitions))
            for partition in partitions:
                log.debug("checking {}{}".format(journal_device, partition))
                if self.is_partition('journal', journal_device, partition):
                    log.debug("found {}{}".format(journal_device, partition))
                    return "{}{}".format(journal_device, partition)
        return "{}0".format(journal_device)

    def _highest_partition(self, device, partition_type):
        """
        Return the highest created partition of partition type
        """
        if device:
            log.debug("{} device: {}".format(partition_type, device))
            pathnames = glob.glob("{}?*".format(device))
            partitions = sorted([ p.replace(device, "") for p in pathnames ], key=int, reverse=True)
            log.debug("partitions: {}".format(partitions))
            for partition in partitions:
                log.debug("checking {}{}".format(device, partition))
                if self.is_partition(partition_type, device, partition):
                    log.debug("found {}{}".format(device, partition))
                    return "{}".format(partition)
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

    def _xfs_args(self, device):
        """
        XFS OSDs can take multiple forms
          OSD partition, Journal partition
          OSD device, Journal device
          OSD device
        """
        if self.is_partitioned(device):
            # Prepartitioned OSD
            if self.settings['osds'][device]['journal']:
                args = "{}{} {}".format(device, self.osd_partition(device), self._journal_pathname(device))
            else:
                args = "{}{} {}{}".format(device, self.osd_partition(device), device, 1)
        else:
            # Raw
            if self.settings['osds'][device]['journal']:
                args = "{} {}".format(device, self.settings['osds'][device]['journal'])
            else:
                args = "{}".format(device)
        return args

    def _bluestore_args(self, device):
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
        wal_device = _defined(device, 'wal')
        db_device = _defined(device, 'db')
        if (wal_device and db_device):
            if wal_device: 
                if self.is_partitioned(wal_device):
                    partition = self._highest_partition(wal_device, 'wal')
                    if partition:
                        args = "--block.wal {}{} ".format(wal_device, partition)
                    else:
                        args = "--block.wal {} ".format(wal_device)
                else:
                    args = "--block.wal {} ".format(wal_device)

            if db_device:
                if self.is_partitioned(db_device):
                    partition = self._highest_partition(db_device, 'db')
                    if partition:
                        args += "--block.db {}{} ".format(db_device, partition)
                    else:
                        args += "--block.db {} ".format(db_device)
                else:
                    args += "--block.db {} ".format(db_device)
        else:
            if wal_device: 
                if self.is_partitioned(wal_device):
                    partition = self._highest_partition(wal_device, 'wal')
                    if partition:
                        args += "--block.wal {}{} ".format(wal_device, partition)
                    else:
                        args += "--block.wal {} ".format(wal_device)

                    partition = self._highest_partition(wal_device, 'db')
                    if partition:
                        args += "--block.db {}{} ".format(wal_device, partition)
                else:
                    args += "--block.wal {} ".format(wal_device)

            if db_device:
                if self.is_partitioned(db_device):
                    partition = self._highest_partition(db_device, 'db')
                    if partition:
                        args += "--block.db {}{} ".format(db_device, partition)
                    else:
                        args += "--block.db {} ".format(db_device)

                    partition = self._highest_partition(db_device, 'wal')
                    if partition:
                        args += "--block.wal {}{} ".format(db_device, partition)
                else:
                    args += "--block.db {} ".format(db_device)

        if self.is_partitioned(device):
            args += "{}1".format(device)
        else:
            args += "{}".format(device)
        return args


    def prepare(self, device):
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
        if 'osds' in self.settings and device in self.settings['osds']:
            cmd = "ceph-disk -v prepare "

            # XFS
            if self.settings['osds'][device]['format'] == 'xfs':
                cmd += "--fs-type xfs "
                args = self._xfs_args(device)
            # Bluestore
            if self.settings['osds'][device]['format'] == 'bluestore':
                cmd += "--bluestore "
                args = self._bluestore_args(device)

            cmd += "--data-dev --journal-dev --cluster {} --cluster-uuid {} ".format(self._cluster_name(), self._fsid())
            cmd += args
        log.info("prepare: {}".format(cmd))
        return cmd

    def activate(self, device):
        """
        Generate the correct activate command.
        """
        cmd = ""
        if 'osds' in self.settings and device in self.settings['osds']:
            cmd = "ceph-disk -v activate --mark-init systemd --mount "
            cmd += "{}{}".format(device, self.osd_partition(device))
        log.info("prepare: {}".format(cmd))
        return cmd

    def detect(self, osd_id, pathname="/var/lib/ceph/osd"):
        """
        Return the osd type
        """
        filename = "{}/ceph-{}/type".format(pathname, osd_id) 
        if os.path.exists(filename): 
            with open(filename, 'r') as osd_type:
                return osd_type.read().rstrip()

    def partitions(self, osd_id, pathname="/var/lib/ceph/osd"):
        """
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

        #journal = "{}/journal".format(mount_dir)
        #log.info("Checking for {}".format(journal))
        #if os.path.exists(journal):
        #    # find real device
        #    cmd = "readlink -f {}".format(journal)
        #    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        #    proc.wait()
        #    result = proc.stdout.read().rstrip()
        #    log.debug(pprint.pformat(result))
        #    log.debug(pprint.pformat(proc.stderr.read()))
        #    partitions['journal'] = result

        return partitions

    def _real_devices(self, mount_dir, device_type):
        """
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
        """
        ids = [ path.split('-')[1] for path in glob.glob("/var/lib/ceph/osd/*") if '-' in path ]
        storage = {}
        for osd_id in ids:
            storage[osd_id] = self.partitions(osd_id)
            log.debug("osd {}: {}".format(osd_id, pprint.pformat(storage[osd_id])))
        self._grains(storage)


    def _grains(self, storage, filename="/etc/salt/grains"):
        """
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
    osdc = OSDCommands()
    partition = osdc.osd_partition(device)
    if partition == 0:
        log.error("Do not know which partition to check on {}".format(device))
        return "/bin/false"

    if osdc.is_partition('osd', device, partition) and _fsck(device, partition):
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
    osdc = OSDCommands()
    partition = osdc.osd_partition(device)
    pathname = "{}{}".format(device, partition)
    log.info("Checking /proc/mounts for {}".format(pathname))
    with open("/proc/mounts", "r") as mounts:
        for line in mounts:
            if line.startswith(pathname):
                return True
    return False

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

    OLD_FORMAT = 'v1'
    NEW_FORMAT = 'v2'
    DEFAULT_FORMAT_FOR_OLD_VERSION = 'xfs'
    DEFAULT_FORMAT_FOR_NEW_VERSION = 'bluestore'

    def __init__(self, device, **kwargs):
        filters = kwargs.get('filters', None)
        # top_level_identifiier
        self.tli = __pillar__['ceph']['storage']['osds']
        self.device = device
        self.capacity = self.set_capacaity()
        self.bytes_c = self.set_bytes()
        self.osd_format = self.set_format()
        self.journal = self.set_journal()
        self.wal_size = self.set_wal_size()
        self.wal = self.set_wal()
        self.db_size = self.set_db_size()
        self.db = self.set_db()
        # default for encryption can be retrieved from the global pillar
        self.encryption = self.set_encryption()

    def set_bytes(self):
        disks = __salt__['mine.get'](tgt=__grains__['id'], fun='cephdisks.list')
        for disk in disks[__grains__['id']]:
            if disk['Device File'] == self.device:
                return disk['Bytes']

    def set_capacity(self):
        disks = __salt__['mine.get'](tgt=__grains__['id'], fun='cephdisks.list')
        for disk in disks[__grains__['id']]:
            if disk['Device File'] == self.device:
                return disk['Capacity']

    def _config_version(self):
        if 'storage' in __pillar__ and 'osds' in __pillar__['storage']:
            return OLD_FORMAT
        if 'ceph' in __pillar__ and 'storage' in __pillar__['ceph']:
            return NEW_FORMAT

    def set_format(self):
        """
        If you have the old version of the config structure
        you will end up with XFS
        If you happen to have the new version
        otherwise with bluestore
        """
        if self._config_version() == OLD_FORMAT:
            # Needs there be checks if the device is actually there?
            # I think that stack.py takes care of removing the old entry..
            # but that also means you can have EITHER the new version
            # OR the old version..
            return DEFAULT_FORMAT_FOR_OLD_VERSION
        if self._config_version() == NEW_FORMAT:
            if 'format' in self.tli[self.device]:
                return __pillar__['ceph']['storage']['osds'][self.device]['format']
            return DEFAULT_FORMAT_FOR_NEW_VERSION

        raise("Probably a parsing Error or something not written to the pillar yet..")

    def set_journal(self, default=False):
        if self._config_version() == OLD_FORMAT:
            struct = __pillar__['storage']['data+journals']
            for device, journal in __pillar__['storage']['data+journals']:
                if device == self.device:
                    return journal
                else:
                    log.info("Couldn't find a jornal for {}".format(device))
                    return default

    def _check_existence(self, key, ident, device, default=None):
        if key in ident[device]:
            return ident[ident][key]
        return default

    def set_wal_size(self, default='200M'):
        if self._config_version() == NEW_FORMAT:
            return self._check_existence('wal_size', self.tli, device, default=default):

    def set_wal(self):
        if self._config_version() == NEW_FORMAT:
            return self._check_existence('wal', self.tli, device):

    def set_db_size(self, default='200M'):
        if self._config_version() == NEW_FORMAT:
            return self._check_existence('db_size', self.tli, device, default=default):

    def set_db(self):
        if self._config_version() == NEW_FORMAT:
            return self._check_existence('db', self.tli, device):

    def set_encryption(self, default=False):
        if self._config_version() == NEW_FORMAT:
            return self._check_existence('db', self.tli, device, default):

def prepare(device):
    """
    Return ceph-disk command to prepare OSD.

    Note: calling the partition command directly from the sls file will not
    give the desired results since the evaluation of the prepare command (and
    the partition check) occurs prior to creating the partitions
    """
    device_o = OSDConfig(device)
    OSDPartitions()partition(device_o)
    return OSDCommands().prepare(device_o)

def activate(device):
    """
    Return ceph-disk command to activate OSD.
    """
    osdc = OSDCommands()
    return osdc.activate(device)

def detect(osd_id):
    """
    """
    osdc = OSDCommands()
    return osdc.detect(osd_id)


def partitions(osd_id):
    """
    """
    osdc = OSDCommands()
    return osdc.partitions(osd_id)

def retain():
    """
    """
    osdc = OSDCommands()
    return osdc.retain()
