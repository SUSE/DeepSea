# -*- coding: utf-8 -*-

import glob
import os
import json
import logging
import time
import re
import pprint
import yaml
import salt.client
from subprocess import call, Popen, PIPE

log = logging.getLogger(__name__)

try:
    import rados
except ImportError:
    pass

"""
The first functions are different queries for osds.  These can be combined.

The two classes should be combined as well.  I thought I would wait for now.
"""


def _run(cmd):
    """
    """
    log.info(cmd)
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    proc.wait()
    _stdout = proc.stdout.read().rstrip()
    _stderr = proc.stdout.read().rstrip()
    log.debug("return code: {}".format(proc.returncode))
    log.debug(_stdout)
    log.debug(_stderr)
    log.debug(pprint.pformat(proc.stdout.read()))
    log.debug(pprint.pformat(proc.stderr.read()))
    #return proc.returncode, _stdout, _stderr
    return proc.returncode, _stdout, _stderr

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

def part_pairs():
    """
    Return an array of partitions and paths
    """
    paths = [ pathname for pathname in glob.glob("/var/lib/ceph/osd/*") ]
    pairs = []
    with open('/proc/mounts') as mounts:
	for line in mounts:
	    partition, path = line.split()[:2]
	    if path in paths:
		m = re.match(r'^(.+)\d+$', partition)
		part = m.group(0)
		pairs.append([ part, path ])
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
    if ('storage' in __pillar__ and
        'osds' in __pillar__['storage'] and
        type(__pillar__['storage']['osds']) is list):
        devices = __pillar__['storage']['osds']
        log.debug("devices: {}".format(devices))
        if 'format' in kwargs and kwargs['format'] != 'filestore':
            return []
    if ('storage' in __pillar__ and
        'data+journals' in __pillar__['storage'] and
        type(__pillar__['storage']['data+journals']) is list):
        [devices.append(x.keys()[0]) for x in __pillar__['storage']['data+journals']]
    log.debug("devices: {}".format(devices))

    return devices

def list_():
    """
    Return the array of ids.
    """
    mounted = [ path.split('-')[1][:-5] for path in glob.glob("/var/lib/ceph/osd/*/fsid") if '-' in path ]
    log.info("mounted osds {}".format(mounted))
    if 'ceph' in __grains__:
        grains = __grains__['ceph'].keys()
    else:
        grains = []
    return list(set(mounted + grains))

def rescinded():
    """
    Return the array of ids that are no longer mounted.
    """
    mounted = [ int(path.split('-')[1][:-5]) for path in glob.glob("/var/lib/ceph/osd/*/fsid") if '-' in path ]
    log.info("mounted osds {}".format(mounted))
    #ids = __grains__['ceph'].keys() if 'ceph' in __grains__ else []
    ids = _children()
    log.debug("ids: {}".format(ids))
    for osd in mounted:
        log.debug("osd: {}".format(osd))
        if osd in ids:
            ids.remove(osd)
    return ids

def _children():
    """
    """
    result = json.loads(tree())
    entries = []
    for entry in result['nodes']:
        if entry['name'] == __grains__['host']:
            entries.extend(entry['children'])
    for entry in result['stray']:
        entries.append(entry['id'])
    return entries


def ids():
    """
    Synonym for list
    """
    return list()

def tree():
    """
    Return osd tree

    Note: Currently hardcoded to the bootstrap keyring.  This should work on
    the master with the admin keyring.  This should also be refactored since
    overriding the keyring is happening in three places.
    """
    settings = {
        'conf': "/etc/ceph/ceph.conf" ,
        'keyring': '/var/lib/ceph/bootstrap-osd/ceph.keyring',
        'client': 'client.bootstrap-osd'
    }
    #cluster=rados.Rados(conffile=settings['conf'])
    cluster=rados.Rados(conffile=settings['conf'], conf=dict(keyring=settings['keyring']), name=settings['client'])
    cluster.connect()
    cmd = json.dumps({"prefix":"osd tree", "format":"json" })
    ret,output,err = cluster.mon_command(cmd, b'', timeout=6)
    log.debug(json.dumps(json.loads(output), indent=4))
    return json.dumps(json.loads(output), indent=4)


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
                    if entry['crush_weight'] != '0.0':
                        msg = "Weight is not 0.0"
                        log.error(msg)
                        return msg
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
            'timeout': 60,
            'keyring': '/etc/ceph/ceph.client.admin.keyring',
            'client': 'client.admin',
            'delay': 6
        }
        self.settings.update(kwargs)
        log.debug("settings: {}".format(pprint.pformat(self.settings)))
        #self.cluster=rados.Rados(conffile=self.settings['conf'])
        self.cluster=rados.Rados(conffile=self.settings['conf'], conf=dict(keyring=self.settings['keyring']), name=self.settings['client'])
        try:
            self.cluster.connect()
        except Exception as error:
            raise RuntimeError("connection error: {}".format(error))


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
        cmd = "ceph --keyring={} --name={} osd crush reweight osd.{} {}".format(self.settings['keyring'], self.settings['client'], self.id, weight)
        return _run(cmd)

    def osd_df(self):
        """
        Retrieve df entry for an osd
        """
        cmd = json.dumps({"prefix":"osd df", "format":"json" })
        ret,output,err = self.cluster.mon_command(cmd, b'', timeout=6)
        #log.debug(json.dumps((json.loads(output)['nodes']), indent=4))
        for entry in json.loads(output)['nodes']:
            if entry['id'] == self.id:
                log.debug(pprint.pformat(entry))
                return entry
        log.warn("ID {} not found".format(self.id))
        return {}

    def is_empty(self):
        """
        Check if OSD is empty
        """
        entry = self.osd_df()
        return entry['pgs'] == 0

    def wait(self):
        """
        Wait until PGs reach 0 or timeout expires
        """
        i = 0
        last_pgs = 0
        while i < self.settings['timeout']/self.settings['delay']:
            entry = self.osd_df()
            if 'pgs' in entry:
                if entry['pgs'] == 0:
                    log.info("osd.{} has no PGs".format(self.id))
                    return ""
                else:
                    log.warn("osd.{} has {} PGs remaining".format(self.id, entry['pgs']))
                    if last_pgs != entry['pgs']:
                        # Making progress, reset countdown
                        i = 0
                        last_pgs = entry['pgs']
            else:
                msg = "osd.{} does not exist".format(self.id)
                log.warn(msg)
                return msg
            i += 1
            time.sleep(self.settings['delay'])

        log.debug("Timeout expired")
        raise RuntimeError("Timeout expired")

def _settings(**kwargs):
    """
    Initialize settings to use the client.storage name and keyring
    if the keyring is available (Only exists on storage nodes.)

    Otherwise, rely on the default which is client.admin. See
    rados.Rados.
    """
    settings = {}
    storage_keyring = '/etc/ceph/ceph.client.storage.keyring'
    if os.path.exists(storage_keyring):
        settings = {
            'keyring': storage_keyring,
            'client': 'client.storage'
        }
        settings.update(kwargs)
    return settings


def zero_weight(id, wait=True, **kwargs):
    """
    Set weight to zero and wait until PGs are moved
    """
    settings = _settings(**kwargs)

    o = OSDWeight(id, **settings)
    o.save()
    rc, _stdout, _stderr = o.reweight('0.0')
    if rc != 0:
        return "Reweight failed"
    if wait:
        return o.wait()
    else:
        return ""

empty = salt.utils.alias_function(zero_weight, 'empty')

def restore_weight(id, **kwargs):
    """
    Restore the previous setting for an OSD if possible
    """
    settings = _settings(**kwargs)

    o = OSDWeight(id, **settings)
    o.restore()
    return True

def _find_paths(device):
    if 'nvme' in device:
        pathnames = glob.glob("{}p[0-9]*".format(device))
    else:
        pathnames = glob.glob("{}[0-9]*".format(device))
    return pathnames


def readlink(device, follow=True):
    """
    Return the short name for a symlink device
    """
    option = ''
    if follow:
        option = '-f'
    cmd = "readlink {} {}".format(option, device)
    log.info(cmd)
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    proc.wait()
    result = proc.stdout.read().rstrip()
    log.debug(pprint.pformat(result))
    log.debug(pprint.pformat(proc.stderr.read()))
    return result

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
        self.device = readlink(device)
        # top_level_identifiier
        self.tli = self._set_tli()
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
        self.types = self.set_types()
        log.debug("OSD config: \n{}".format(pprint.pformat(vars(self))))

    def _set_tli(self):
        """
        Return the dictionary below ceph:storage:osds, if available
        """
        if ('ceph' in __pillar__ and
           'storage' in __pillar__['ceph'] and
           'osds' in __pillar__['ceph']['storage']):

            return self._convert_tli(__pillar__['ceph']['storage']['osds'])
        return None

    def _convert_tli(self, osds):
        """
        Simplify names to short devices
        """
        result = {}
        for osd in osds:
            short_osd = readlink(osd)
            result[short_osd] = {}
            for attr in osds[osd]:
                if (attr == 'journal' or attr == 'wal' or attr == 'db'):
                    result[short_osd][attr] = readlink(osds[osd][attr])
                else:
                    result[short_osd][attr] = osds[osd][attr]
        return result

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
            if self.device not in self.tli:
                raise RuntimeError("Device {} is not defined in pillar".format(self.device))
            if 'format' in self.tli[self.device]:
                return self.tli[self.device]['format']
            return OSDConfig.DEFAULT_FORMAT_FOR_V2

        raise RuntimeError("Probably a parsing Error or something not written to the pillar yet..")

    def set_journal(self, default=False):
        """
        Return the journal device, if defined
        """
        if self._config_version() == OSDConfig.V1:
            struct = self._convert_data_journals(__pillar__['storage']['data+journals'])
            log.debug("struct: \n{}".format(pprint.pformat(struct)))
            if self.device in struct:
                return struct[self.device]
            else:
                log.info("No journal specified for {}".format(self.device))
        if self._config_version() == OSDConfig.V2:
            if (self.device in self.tli and
               'journal' in self.tli[self.device]):
                return self.tli[self.device]['journal']
            else:
                log.info("No journal specified for {}".format(self.device))
        return default

    def _convert_data_journals(self, struct):
        """
        Create new structure with short device names
        """
        result = {}
        for pair in struct:
            for osd, journal in pair.iteritems():
                result[readlink(osd)] = readlink(journal)
        return result

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
        Return the size of the journal.  Account for small disks.
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

    def set_types(self):
        """
        Return the Ceph disk type mapping to partition UUID
        """
        types = {'osd': '4FBD7E29-9D25-41B8-AFD0-062C0CEFF05D',
                 'journal': '45B0969E-9B03-4F30-B4C6-B4B80CEFF106',
                 'wal': '5CE17FCE-4087-4169-B7FF-056CC58473F9',
                 'db': '30CD0809-C2B2-499C-8879-2D6B78529876',
                 'lockbox': 'FB3AABF9-D25F-47CC-BF5E-721D1816496B'}
        return types

class OSDPartitions(object):
    """
    Manage the creation/deletion of partitions related to OSDs

    Generally, partitions are created on devices other than the OSD.  Not
    creating partitions is fine.
    """

    def __init__(self, config):
        """
        Initialize configuration, disks from mine
        """
        self.osd = config
        #self.disks = __salt__['mine.get'](tgt=__grains__['id'], fun='cephdisks.list')

    def clean(self):
        """
        Remove existing partitions from OSD.  Addresses issue of
        damaged filesystems.

        Note: expected to only run inside of "not is_prepared"
        """
        pathnames = _find_paths(self.osd.device)
        if pathnames:
            cmd = "sgdisk -Z --clear -g {}".format(self.osd.device)
            rc, _stdout, _stderr = _run(cmd)
            if rc != 0:
                raise RuntimeError("{} failed".format(cmd))

    def partition(self):
        """
        Create partitions for supported formats
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
                self.create(self.osd.device, [('journal', self.osd.journal_size), ('osd', None)])
                #FIXME: The calls in the conditionals are the same.


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

        Note: The unsupported combinations fallback to creating an OSD as
        though the size or device had not been specified. The current issue
        is

        - ceph-disk does not support a --block option
        - ceph-disk creates an additional partition when --block.wal is the
          same as the OSD

        When these get resolved, change the logic
        """

        if ((self.osd.wal or self.osd.db) and self.osd.encryption):
            log.warn("You deploy encrypted WAL and/or DB on a dedicated device. Specifying sizes is now handled via your ceph.conf")
            return

        if self.osd.wal and self.osd.db:
            if self.osd.wal_size:
                if self.osd.wal == self.osd.device:
                    log.warn("WAL size is unsupported for same device of {}".format(self.osd.device))
                else:
                    # Create wal of wal_size on wal device
                    self.create(self.osd.wal, [('wal', self.osd.wal_size)])
            else:
                log.warn("No size specified for wal {}. Using default sizes.".format(self.osd.wal))

            if self.osd.db_size:
                if self.osd.wal == self.osd.device:
                    log.warn("DB size is unsupported for same device of {}".format(self.osd.device))
                else:
                    # Create db of db_size on db device
                    self.create(self.osd.db, [('db', self.osd.db_size)])
            else:
                log.warn("No size specified for db {}. Using default sizes".format(self.osd.db))
        else:
            # This situation seems unintentional - use faster media for
            # the wal or db but not the other.  Help newbies out by
            # putting wal and db on same device
            if self.osd.wal:
                if self.osd.wal_size:
                    if self.osd.wal == self.osd.device:
                        log.warn("WAL size is unsupported for same device of {}".format(self.osd.device))
                    else:
                        log.warn("Setting db to same device {} as wal".format(self.osd.wal))
                        # Create wal of wal_size on wal device
                        # Create db on wal device
                        self.create(self.osd.wal, [('wal', self.osd.wal_size),
                                                 ('db', self._halve(self.osd.wal_size))])
            else:
                if self.osd.wal_size:
                    log.warn("WAL size is unsupported for same device of {}".format(self.osd.device))

            if self.osd.db:
                if self.osd.db_size:
                    if self.osd.db == self.osd.device:
                        log.warn("DB size is unsupported for same device of {}".format(self.osd.device))
                    else:
                        log.warn("Setting wal to same device {} as db".format(self.osd.db))
                        # Create db of db_size on db device
                        # Create wal on db device
                        self.create(self.osd.db, [('wal', self._double(self.osd.db_size)),
                                                ('db', self.osd.db_size)])
            else:
                if self.osd.db_size:
                    log.warn("DB size is unsupported for same device of {}".format(self.osd.device))

    def create(self, device, partitions):
        """
        Create a partition
        """
        last_partition = self._last_partition(device)
        log.debug("last partition: {}".format(last_partition))

        index = 1
        for partition_type, size in partitions:
            number = last_partition + index
            if size:
                cmd = "/usr/sbin/sgdisk -n {}:0:+{} -t {}:{} {}".format(number, size, number, self.osd.types[partition_type], device)
            else:
                cmd = "/usr/sbin/sgdisk -N {} -t {}:{} {}".format(number, number, self.osd.types[partition_type], device)
            rc, _stdout, _stderr = _run(cmd)
            if rc != 0:
                raise RuntimeError("{} failed".format(cmd))
            log.info("partprobe disk")
            self._part_probe(device)
            log.info("partprobe partition")
            if 'nvme' in device:
                self._part_probe("{}p{}".format(device, number))
            else:
                self._part_probe("{}{}".format(device, number))
            # Seems odd to wipe a just created partition ; however, ghost
            # filesystems on reused disks seem to be an issue
            if os.path.exists("{}{}".format(device, number)):
                wipe_cmd = "dd if=/dev/zero of={}{} bs=4096 count=1 oflag=direct".format(device, number)
                _run(wipe_cmd)
            index += 1

    def _part_probe(self, device):
        """
        """
        wait_time = 1
        retries = 5
        cmd = "/usr/sbin/partprobe {}".format(device)
        for attempt in range(1, retries + 1):
            rc, _stdout, _stderr = _run(cmd)
            if rc == 0:
                return
            time.sleep(wait_time)
        raise RuntimeError("{} failed".format(cmd))

    def _last_partition(self, device):
        """
        Return the last partition. Only the number is needed for the sgdisk
        command.
        """
        pathnames = _find_paths(device)
        if pathnames:
            partitions = sorted([re.sub(r"{}p?".format(device), '', p) for p in pathnames ], key=int)
            log.debug("partitions: {}".format(partitions))
            last_part = partitions[-1]
            return int(last_part)
        return 0

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

    def osd_partition(self):
        """
        Return the OSD partition.  For new devices without any sizes,
        partition creation is left to ceph-disk.  This means that there
        is no partition to find and we rely on convention.

        The final call only applies for some device that is neither
        filestore nor bluestore which is more of a best effort try.
        """
        log.debug("format: {}".format(self.osd.disk_format))
        if self.osd.disk_format:
              if self.osd.disk_format == 'filestore':
                  if self.osd.journal and self.osd.journal != self.osd.device:
                      # Journal on separate device
                      return 1
                  else:
                      # Journal on same device
                      return 2
              if self.osd.disk_format == 'bluestore':
                  return 1
        return self.highest_partition(self.osd.device, 'osd')

    def is_partition(self, partition_type, device, partition):
        """
        Check partition type
        """
        cmd = "/usr/sbin/sgdisk -i {} {}".format(partition, device)
        rc, result, stderr = _run(cmd)
        id = "Partition GUID code: {}".format(self.osd.types[partition_type])
        return id in result

    def highest_partition(self, device, partition_type):
        """
        Return the highest created partition of partition type
        """
        if device:
            log.debug("{} device: {}".format(partition_type, device))
            pathnames = _find_paths(device)
            # the to int -> key=int conversion fails here
            partitions = sorted([ re.sub(r"{}p?".format(device), '', p) for p in pathnames ], key=int, reverse=True)
            # best strategy? remove key=int and do checks before conversion ourselves?
            log.debug("partitions: {}".format(partitions))
            for partition in partitions:
                log.debug("checking partition {} on device {}".format(partition, device))
                # Not confusing at all - use digit for NVMe too
                if self.is_partition(partition_type, device, partition):
                    log.debug("found partition {} on device {}".format(partition, device))
                    if 'nvme' in device:
                        partition = "p{}".format(partition)
                    return partition
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
        result = _find_paths(device)
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
                args = "{}{} {}{}".format(device, self.highest_partition(device, 'osd'), self.osd.journal, self.highest_partition(self.osd.journal, 'journal'))
            else:
                args = "{}{} {}{}".format(device, self.highest_partition(device, 'osd'), device, self.highest_partition(self.osd.device, 'journal'))
        else:
            # Raw
            if self.osd.journal:
                args = "{} {}".format(device, self.osd.journal)
            else:
                args = "{}".format(device)
        return args

    def _bluestore_args(self):
        """
        if wal_size or db_size and wal and or db and no encryption:
          create partitions and specify /dev/wal_or_db<part_id>
        elif encryption and db/wal_size:
          you can only set the sizes via the ceph.conf (limitation)
          (we can't create partitions ahead of time (we could -- not implemented))
        else:
          let ceph-disk create partitions
        """
        args = ""
        if not self.osd.encryption:

            # WAL cornercase with sizes
            if self.osd.wal and self.osd.wal_size and self.osd.wal != self.osd.device:
                partition = self.highest_partition(self.osd.wal, 'wal')
                if partition:
                    args += "--block.wal {}{} ".format(self.osd.wal, partition)
                else:
                    args += "--block.wal {} ".format(self.osd.wal)

            # DB cornercase with sizes
            if self.osd.db and self.osd.db_size and self.osd.db != self.osd.device:
                partition = self.highest_partition(self.osd.db, 'db')
                if partition:
                    args += "--block.db {}{} ".format(self.osd.db, partition)
                else:
                    args += "--block.db {} ".format(self.osd.db)

            # Generic case withouth sizes 
            if self.osd.wal and not (self.osd.wal_size or self.osd.db_size):
                args += "--block.wal {} ".format(self.osd.wal)
            if self.osd.db and not (self.osd.wal_size or self.osd.db_size):
                args += "--block.db {} ".format(self.osd.db)

        if self.osd.encryption and (self.osd.wal_size or self.osd.db_size):
            log.warn("""Your specified wal/db_sizes will not be respected. 
                           Configure the default sizes via the ceph.conf with
                           bluestore block db size = size
                           bluestore block wal size = size""")

        if self.osd.encryption:
            if self.osd.db:
                args += "--block.db {} ".format(self.osd.db)
            if self.osd.wal:
                args += "--block.wal {} ".format(self.osd.wal)

        # fails if the device is already partitioned but the partitionnumber is not 1
        # should never be partitioned..
        if self.is_partitioned(self.osd.device):
            if 'nvme' in self.osd.device:
                args += "{}p1".format(self.osd.device)
            else:
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
                cmd += "--fs-type xfs --filestore "
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
                prefix = ''
                if 'nvme' in self.osd.device:
                    prefix = 'p'
                cmd = "ceph-disk -v activate --mark-init systemd --mount "
                cmd += "{}{}{}".format(self.osd.device, prefix, self.osd_partition())

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

    def is_incorrect(self):
        """
        Check that an OSD is configured properly.  Compare formats, separate
        partitions and size of partitions.
        """
        if self.osd.encryption:
            log.warn("Encrypted OSDs not supported")
            return False

        pathname = None
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                entry = line.split()
                if entry[0].startswith(self.osd.device):
                    pathname = entry[1]
                    break

        if pathname:
            filename = "{}/type".format(pathname)
            if os.path.exists(filename):
                with open(filename, 'r') as osd_type:
                    osd_format = osd_type.read().rstrip()
                if osd_format != self.osd.disk_format:
                    log.info("OSD {} does not match format {}".format(pathname, self.osd.disk_format))
                    return True

            if self.osd.disk_format == 'filestore' and self.osd.journal:
                result = self._check_device(pathname, 'journal', self.osd.journal, self.osd.journal_size)
                if result:
                    return True

            if self.osd.disk_format == 'bluestore':
                if self.osd.wal:
                    if os.path.exists("{}/block.wal".format(pathname)):
                        result = self._check_device(pathname, 'block.wal', self.osd.wal, self.osd.wal_size)
                        if result:
                            return True
                if self.osd.db:
                    if os.path.exists("{}/block.db".format(pathname)):
                        result = self._check_device(pathname, 'block.db', self.osd.db, self.osd.db_size)
                        if result:
                            return True

        return False

    def _check_device(self, pathname, attr, device, size):
        """
        """
        devicename = readlink("{}/{}".format(pathname, attr))
        if device and  not devicename.startswith(device):
            log.info("OSD {} {} does not match {}".format(attr, devicename, device))
            return True
        if size:
            cmd = "blockdev --getsize64 {}".format(devicename)
            rc, _stdout, _stderr = _run(cmd)
            bsize = int(_stdout)
            _bytes = self._convert(size)
            if _bytes != bsize:
                log.info("OSD {} size {} does not match {} ({})".format(attr, bsize, size, _bytes))
                return True

    def _convert(self, size):
        """
        """
        suffixes = { 'K': 2**10, 'M': 2**20, 'G': 2**30, 'T': 2**40 }
        suffix = size[-1:].upper()
        bsize = int(size[:-1]) * suffixes[suffix]
        log.debug("suffix: {} bsize: {}".format(suffix, bsize))
        return bsize

def split_partition(partition):
    """
    Return the device and partition
    """
    part = readlink(partition)
    #if os.path.exists(part):
    log.debug("splitting partition {}".format(part))
    m = re.match("(.+\D)(\d+)", part)
    disk = m.group(1)
    if 'nvme' in disk:
        disk = disk[:-1]
        log.debug("Truncating p {}".format(disk))
    return disk, m.group(2)
    #return None, None

class OSDRemove(object):
    """
    Manage the graceful removal of an OSD
    """

    def __init__(self, osd_id, device, weight, grains, force=False, **kwargs):
        """
        Initialize settings
        """
        self.osd_id = osd_id
        self.osd_fsid = device.osd_fsid
        self.partitions = self.set_partitions(device)
        self._weight = weight
        self._grains = grains
        self.force = force

    def set_partitions(self, device):
        """
        Return queried partitions or fallback to grains
        """
        partitions = device.partitions(self.osd_id)
        if not partitions:
            log.debug("grains: \n{}".format(pprint.pformat(__grains__['ceph'])))
            if str(self.osd_id) in __grains__['ceph']:
                partitions = __grains__['ceph'][str(self.osd_id)]['partitions']
            else:
                log.error("Id {} missing from grains".format(self.osd_id))
                return None
        log.debug("partitions: \n{}".format(pprint.pformat(partitions)))
        return partitions

    def remove(self):
        """
        """
        if not self.partitions:
            msg = "OSD {} is not present on minion {}".format(self.osd_id, __grains__['id'])
            log.error(msg)
            return msg

        if self.force:
            log.warn("Forcing OSD removal")
        else:
            self.empty()

        #Terminate
        self.terminate()

        #Unmount filesystems
        result = self.unmount()
        if result:
            return result

        #Wipe partitions
        self.wipe()

        #Destroy partitions
        self.destroy()
        return ""

    def empty(self):
        """
        """
        self._weight.save()
        rc, _stdout, _stderr = self._weight.reweight('0.0')
        if rc != 0:
            msg = "Reweight failed"
            log.error(msg)
            return msg
        self._weight.wait()
        return ""

    def terminate(self):
        """
        Stop the ceph-osd without error
        """
        # Check weight is zero
        cmd = "systemctl disable ceph-osd@{}".format(self.osd_id)
        _run(cmd)
        # How long with this hang on a broken OSD
        cmd = "systemctl stop ceph-osd@{}".format(self.osd_id)
        _run(cmd)
        cmd = "pkill -f ceph-osd.*{}\ --".format(self.osd_id)
        _run(cmd)
        time.sleep(1)
        cmd = "pkill -9 -f ceph-osd.*{}\ --".format(self.osd_id)
        _run(cmd)
        time.sleep(1)
        return ""

    def unmount(self):
        """
        Unmount any related filesystems
        """
        mounted = self._mounted()
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                entry = line.split()
                if '/dev/mapper' in entry[0]:
                    mount = readlink(entry[0])
                else:
                    mount = entry[0]
                if mount in mounted:
                    cmd = "umount {}".format(mount)
                    rc, _stdout, _stderr = _run(cmd)
                    log.debug("returncode: {}".format(rc))
                    if rc != 0:
                        msg = "Unmount failed - check for processes on {}".format(entry[0])
                        log.error(msg)
                        return msg
                    os.rmdir(entry[1])

        if '/dev/dm' in self.partitions['osd']:
            cmd = "dmsetup remove {}".format(self.partitions['osd'])
            _run(cmd)
        return ""

    def _mounted(self):
        """
        Find the mount points for the OSD and lockbox.
        """
        devices = []
        for attr in ['osd', 'lockbox']:
            if attr in self.partitions:
                devices.append(readlink(self.partitions[attr]))
        log.debug("mounted: {}".format(devices))
        return devices

    def wipe(self):
        """
        Erase the beginning of any filesystems
        """
        if self.partitions:
            for osd_type, partition in self.partitions.iteritems():
                if os.path.exists(partition):
                    cmd = "dd if=/dev/zero of={} bs=4096 count=1 oflag=direct".format(partition)
                    _run(cmd)
        else:
            msg = "Nothing to wipe - no partitions available"
            log.error(msg)
            return msg
        return ""

    def destroy(self):
        """
        Destroy the osd disk and any partitions on other disks
        """
        self.osd_disk = self._osd_disk()
        self._delete_partitions()
        self._wipe_gpt_backups()
        self._delete_osd()
        self._settle()
        return ""

    def _osd_disk(self):
        """
        """
        if 'lockbox' in self.partitions:
            partition = self.partitions['lockbox']
        else:
            partition = self.partitions['osd']
        disk, partition = split_partition(partition)
        return disk

    def _delete_partitions(self):
        """
        """
        for attr in self.partitions:
            log.debug("Checking attr {}".format(attr))
            if '/dev/dm' in self.partitions[attr]:
                cmd = "dmsetup remove {}".format(self.partitions[attr])
                _run(cmd)
                continue

            short_name = readlink(self.partitions[attr])
            exists = os.path.exists(short_name)
            if not exists and 'nvme' in short_name:
                time.sleep(1)
                # NVMe devices just might not be there the first time
                log.info("Check {} once more".format(short_name))
                exists = os.path.exists(short_name)

            if exists:
                if self.osd_disk and self.osd_disk in short_name:
                    log.info("No need to delete {}".format(short_name))
                else:
                    disk, partition = split_partition(self.partitions[attr])
                    if disk:
                        log.debug("disk: {} partition: {}".format(disk, partition))
                        cmd = "sgdisk -d {} {}".format(partition, disk)
                        _run(cmd)
            else:
                log.error("Partition {} does not exist".format(short_name))

    def _wipe_gpt_backups(self):
        """
        """
        if self.osd_disk and os.path.exists(self.osd_disk):
            cmd = "blockdev --getsz {}".format(self.osd_disk)
            rc, _stdout, _stderr = _run(cmd)
            end_of_disk = int(_stdout)
            seek_position = int(end_of_disk/4096 - 33)
            cmd = "dd if=/dev/zero of={} bs=4096 count=33 seek={} oflag=direct".format(self.osd_disk, seek_position)
            _run(cmd)
            return ""

    def _delete_osd(self):
        """
        """
        if self.osd_disk and os.path.exists(self.osd_disk):
            cmd = "sgdisk -Z --clear -g {}".format(self.osd_disk)
            rc, _stdout, _stderr = _run(cmd)
            if rc != 0:
                raise RuntimeError("{} failed".format(cmd))

    def _settle(self):
        """
        """
        for cmd in ['udevadm settle --timeout=20',
                    'partprobe',
                    'udevadm settle --timeout=20']:
            _run(cmd)

def remove(osd_id, **kwargs):
    """
    """
    settings = _settings(**kwargs)

    if 'force' in kwargs and kwargs['force']:
        osdw = None
    else:
        osdw = OSDWeight(osd_id, **settings)
    osdd = OSDDevices()
    osdg = OSDGrains(osdd)

    osdr = OSDRemove(osd_id, osdd, osdw, osdg, **kwargs)
    return osdr.remove()

def is_empty(osd_id, **kwargs):
    """
    """
    settings = _settings(**kwargs)
    osdd = OSDDevices()
    osdw = OSDWeight(osd_id, **settings)
    return osdw.is_empty()

def terminate(osd_id):
    """
    """
    osdd = OSDDevices()
    osdr = OSDRemove(osd_id, osdd, None, None)
    return osdr.terminate()

def unmount(osd_id):
    """
    """
    osdd = OSDDevices()
    osdg = OSDGrains(osdd)
    osdr = OSDRemove(osd_id, osdd, None, osdg)
    return osdr.unmount()

def wipe(osd_id):
    """
    """
    osdd = OSDDevices()
    osdg = OSDGrains(osdd)
    osdr = OSDRemove(osd_id, osdd, None, osdg)
    return osdr.wipe()

def destroy(osd_id):
    """
    """
    osdd = OSDDevices()
    osdg = OSDGrains(osdd)
    osdr = OSDRemove(osd_id, osdd, None, osdg)
    return osdr.destroy()

class OSDDevices(object):
    """
    Gather the partitions for an OSD
    """

    def __init__(self, pathname="/var/lib/ceph/osd"):
        """
        Initialize settings
        """
        self.pathname = pathname

    def partitions(self, osd_id):
        """
        Returns the partitions of the OSD
        """
        self.osd_id = osd_id
        partitions = {}
        mount_dir = "{}/ceph-{}".format(self.pathname, self.osd_id)
        lockbox_dir = self._lockbox_dir()
        log.info("Checking /proc/mounts for {}".format(mount_dir))
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                entry = line.split()
                if entry[1] == mount_dir:
                    log.info("osd: {}".format(line))
                    partitions['osd'] = self._uuid_device(entry[0])
                if entry[1] == lockbox_dir:
                    log.info("lockbox: {}".format(line))
                    partitions['lockbox'] = self._uuid_device(entry[0])

        for device_type in ['journal', 'block', 'block.db', 'block.wal', 'block_dmcrypt']:
            result = self._uuid_device("{}/{}".format(mount_dir, device_type))
            if result:
                partitions[device_type] = result
        return partitions

    def _lockbox_dir(self):
        return "{}-lockbox/{}".format(self.pathname, self.osd_fsid(self.osd_id))

    def osd_fsid(self, osd_id):
        """
        Read the fsid (not the Ceph fsid) and return the lockbox directory
        name.
        """
        filename = "{}/ceph-{}/fsid".format(self.pathname, osd_id)
        if os.path.exists(filename):
            with open(filename, 'r') as fsid:
                return fsid.read().rstrip()
        else:
            log.error("file {} is missing".format(filename))

    def _uuid_device(self, device, pathname="/dev/disk/by-id"):
        """
        Return the uuid device, last one if multiple are matched
        """
        if os.path.exists(device):
            if os.path.exists(pathname):
                cmd = "find -L {} -samefile {} \( -name ata* -o -name nvme* \)".format(pathname, device)
                rc, _stdout, _stderr = _run(cmd)
                if _stdout:
                    return _stdout.split()[-1]
                else:
                    return readlink(device)
            else:
                return readlink(device)

class OSDGrains(object):
    """
    Manage caching the device names for all OSDs.

    Note: Some logistics problems to work through.  When should retain be
    rerun and when should it not run.  In case of a failed disk, this may
    be the only source of the related partitions.  Rerunning retain will
    remove this entry.
    """

    def __init__(self, device, pathname="/var/lib/ceph/osd"):
        """
        Initialize settings
        """
        self.pathname = pathname
        self.partitions = device.partitions
        self.osd_fsid = device.osd_fsid

    def retain(self):
        """
        Save the OSD partitions into the grains
        """
        ids = [ path.split('-')[1] for path in glob.glob("/var/lib/ceph/osd/*") if '-' in path ]
        storage = {}
        for osd_id in ids:
            if self.partitions(osd_id):
                storage[osd_id] = {}
                storage[osd_id]['partitions'] = self.partitions(osd_id)
                storage[osd_id]['fsid'] = self.osd_fsid(osd_id)
                log.debug("osd {}: {}".format(osd_id, pprint.pformat(storage[osd_id])))
        self._grains(storage)


    def _grains(self, storage, filename="/etc/salt/grains"):
        """
        Load and save grains when changed
        """
        content = {}
        if os.path.exists(filename):
            with open(filename, 'r') as minion_grains:
                content = yaml.safe_load(minion_grains)
        if 'ceph' in content and content['ceph'] == storage:
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
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    return osdc.is_partitioned(device)

def deploy():
    """
    Partition, prepare and activate an OSD.

    Note: This cannot be done in a single state file.  This cannot be done in
    multiple state files through orchestration.

    In a single state file, the prepare and activate commands are evaluated
    prior to the running a partition module command.

    Calling the partition command as part of the prepare causes a bug of
    creating additional partitions since re-evaluations of the prepare command
    cause the partitions to be created.

    Separating the steps into two state files requires two for loops.  This
    breaks the current logic since the prepare and activate commands find the
    last partitions created.  No mapping exists between an OSD and partitions
    until the partition is created.

    Another strategy could be converting the prepare and activate to a module
    but that serves little purpose.  The admin will still not see the commands.

    The last idea is converting all of this into a state module that returns
    all the commands in the comment.
    """
    for device in configured():
        if not is_prepared(device):
            config = OSDConfig(device)
            osdp = OSDPartitions(config)
            osdp.clean()
            osdp.partition()
            osdc = OSDCommands(config)
            _run(osdc.prepare())
            _run(osdc.activate())

def redeploy(simultaneous=False):
    """
    """
    if simultaneous:
        for _id in __grains__['ceph']:
            partition = _partition(_id)
            log.info("Partition: {}".format(partition))
            disk, part = split_partition(partition)
            log.info("ID: {}".format(_id))
            log.info("Disk: {}".format(disk))
            if is_incorrect(disk):
                zero_weight(_id, wait=False)

    for _id in __grains__['ceph']:
        partition = _partition(_id)
        #if 'lockbox' in __grains__['ceph'][_id]['partitions']:
        #    partition = __grains__['ceph'][_id]['partitions']['lockbox']
        #else:
        #    partition = __grains__['ceph'][_id]['partitions']['osd']
        log.info("Partition: {}".format(partition))
        disk, part = split_partition(partition)
        log.info("ID: {}".format(_id))
        log.info("Disk: {}".format(disk))
        if not os.path.exists(partition) or is_incorrect(disk):
            remove(_id)
            config = OSDConfig(disk)
            osdp = OSDPartitions(config)
            osdp.partition()
            osdc = OSDCommands(config)
            _run(osdc.prepare())
            _run(osdc.activate())
          # not is_prepared(disk)):

def _partition(osd_id):
    """
    """
    if 'lockbox' in __grains__['ceph'][osd_id]['partitions']:
        return __grains__['ceph'][osd_id]['partitions']['lockbox']
    else:
        return __grains__['ceph'][osd_id]['partitions']['osd']

def is_prepared(device):
    """
    Check if the device has already been prepared.  Return shell command.

    Note: the alternate strategy to running is_prepared as part of an unless in
    an sls file is to create a state module.  However, will the admin be able
    to debug that configuration without reading python?  This task is left for
    later...
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    if osdc.highest_partition(readlink(device), 'lockbox') != 0:
        log.debug("Found encrypted OSD {}".format(device))
        return True
    partition = osdc.highest_partition(readlink(device), 'osd')
    if partition == 0:
        log.debug("Do not know which partition to check on {}".format(device))
        return False
    log.debug("Checking partition {} on device {}".format(partition, device))
    if osdc.is_partition('osd', config.device, partition) and _fsck(config.device, partition):
        return True
    else:
        return False

def _fsck(device, partition):
    """
    Check filesystem on partition

    Note: xfs_repair returns immediately on success, but takes 3m39s to fail
    on some broken filesystems.  Not good for automation.
    """
    prefix = ''
    if 'nvme' in device:
        prefix = 'p'
    #cmd = "/sbin/fsck -t xfs -n {}{}{}".format(device, prefix, partition)
    cmd = "/usr/sbin/xfs_admin -u {}{}{}".format(device, prefix, partition)
    log.info(cmd)
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    proc.wait()
    log.debug(pprint.pformat(proc.stdout.read()))
    log.debug(pprint.pformat(proc.stderr.read()))
    log.debug("xfs_admin: {}".format(proc.returncode))
    return proc.returncode == 0

def is_activated(device):
    """
    Check if the device has already been activated.  Return shell command.
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    partition = osdc.highest_partition(readlink(device), 'osd')
    pathname = "{}{}".format(config.device, partition)
    log.info("Checking /proc/mounts for {}".format(pathname))
    with open("/proc/mounts", "r") as mounts:
        for line in mounts:
            if line.startswith(pathname):
                return "/bin/true"
    return "/bin/false"

def prepare(device):
    """
    Return ceph-disk command to prepare OSD.

    Note: calling the partition command directly from the sls file will not
    give the desired results since the evaluation of the prepare command (and
    the partition check) occurs prior to creating the partitions
    """
    config = OSDConfig(device)
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

def is_incorrect(device):
    """
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    return osdc.is_incorrect()

def partitions(osd_id):
    """
    """
    osdd = OSDDevices()
    return osdd.partitions(osd_id)

def retain():
    """
    Save the OSD partitions in the local grains
    """
    osdd = OSDDevices()
    osdg = OSDGrains(osdd)
    return osdg.retain()

def report(failhard=False):
    """
    Display the difference between the pillar and grains for the OSDs

    Note: this needs more bullet proofing
    """
    if 'ceph' not in __grains__:
        return "No ceph grain available.  Run osd.retain"
    active = []
    unmounted = []
    for _id in __grains__['ceph']:
        partition = readlink(__grains__['ceph'][_id]['partitions']['osd'])
        disk, part = split_partition(partition)
        active.append(disk)
        log.debug("checking /var/lib/ceph/osd/ceph-{}/fsid".format(_id))
        if not os.path.exists("/var/lib/ceph/osd/ceph-{}/fsid".format(_id)):
            unmounted.append(disk)
        if 'lockbox' in __grains__['ceph'][_id]['partitions']:
            partition = readlink(__grains__['ceph'][_id]['partitions']['lockbox'])
            disk, part = split_partition(partition)
            active.append(disk)

    log.debug("active: {}".format(active))


    if 'ceph' in __pillar__:
        unconfigured = __pillar__['ceph']['storage']['osds'].keys()
        changed = list(unconfigured)
        for osd in __pillar__['ceph']['storage']['osds'].keys():
            if readlink(osd) in active:
                unconfigured.remove(osd)
                if not is_incorrect(readlink(osd)):
                    log.debug("Removed from changed {}".format(osd))
                    changed.remove(osd)
            else:
                log.debug("Removed from changed {}".format(osd))
                changed.remove(osd)

    log.debug("changed: {}".format(active))

    if 'storage' in __pillar__:
        unconfigured = __pillar__['storage']['osds']
        for dj in __pillar__['storage']['data+journals']:
            unconfigured.append(*dj.keys())
        log.info("unconfigured: {}".format(unconfigured))
        changed = list(unconfigured)
        osds = list(unconfigured)
        for osd in osds:
            if readlink(osd) in active:
                unconfigured.remove(osd)
                if not is_incorrect(readlink(osd)):
                    log.debug("Removed from changed {}".format(osd))
                    changed.remove(osd)
            else:
                log.debug("Removed from changed {}".format(osd))
                changed.remove(osd)

    if unconfigured or changed or unmounted:
        msg = ""
        if unconfigured:
            msg += "No OSD configured for \n{}\n".format("\n".join(unconfigured))
        if changed:
            msg += "Different configuration for \n{}\n".format("\n".join(changed))
        if unmounted:
            msg += "No OSD mounted for \n{}\n".format("\n".join(unmounted))
        if failhard:
            raise RuntimeError(msg)
        else:
            return msg
    else:
        return "All configured OSDs are active"


__func_alias__ = {
                'list_': 'list',
                }

