# -*- coding: utf-8 -*-
# pylint: disable=fixme,modernize-parse-error
# pylint: disable=visually-indented-line-with-same-indent-as-next-logical-line

"""
All OSD related functions
"""

from __future__ import absolute_import
from __future__ import print_function
import glob
import os
import json
import logging
import time
import re
import pprint
import yaml
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin


log = logging.getLogger(__name__)

try:
    from salt.ext.six.moves import range
except ImportError:
    log.error("Could not import salt.ext.six.moves")

try:
    import salt.ext.six as six
except ImportError:
    log.error("Could not import salt.ext.six")

try:
    import rados
except ImportError:
    pass

# The first functions are different queries for osds.  These can be combined.
# The two classes should be combined as well.  I thought I would wait for now.

# These first three methods should be combined... saving for later


def paths():
    """
    Return an array of pathnames
    """
    return [pathname for pathname in glob.glob("/var/lib/ceph/osd/*")]


def devices():
    """
    Return an array of devices
    """
    _paths = [pathname for pathname in glob.glob("/var/lib/ceph/osd/*")]
    _devices = []
    with open('/proc/mounts') as mounts:
        for line in mounts:
            device, path = line.split()[:2]
            if path in _paths:
                _devices.append(device)

    return _devices


def pairs():
    """
    Return an array of devices and paths
    """
    _paths = [pathname for pathname in glob.glob("/var/lib/ceph/osd/*")]
    _pairs = []
    with open('/proc/mounts') as mounts:
        for line in mounts:
            _partition, path = line.split()[:2]
            if path in _paths:
                match = re.match(r'^(.+)\d+$', _partition)
                device = match.group(1)
                if device.endswith('p'):
                    device = device[:-1]
                _pairs.append([device, path])

    return _pairs


def part_pairs():
    """
    Return an array of partitions and paths
    """
    _paths = [pathname for pathname in glob.glob("/var/lib/ceph/osd/*")]
    _pairs = []
    with open('/proc/mounts') as mounts:
        for line in mounts:
            _partition, path = line.split()[:2]
            if path in _paths:
                match = re.match(r'^(.+)\d+$', _partition)
                part = match.group(0)
                _pairs.append([part, path])
    return _pairs


def _filter_devices(_devices, **kwargs):
    """
    Filter devices if provided.

    Only supporting format currently.
    """
    if 'format' in kwargs:
        _devices = [device for device in _devices
                    if _devices[device]['format'] == kwargs['format']]

    return _devices


def configured(**kwargs):
    """
    Return the osds from the ceph namespace or original namespace, optionally
    filtered by attributes.
    """
    _devices = []
    # That doesn't allow mixed configurations
    # storage[osds] OR storage[data+journals]
    # TODO: append devices from one config version
    if ('ceph' in __pillar__ and 'storage' in __pillar__['ceph']
        and 'osds' in __pillar__['ceph']['storage']):
        _devices = __pillar__['ceph']['storage']['osds']
        log.debug("devices from pillar: {}".format(_devices))
        _devices = _filter_devices(_devices, **kwargs)
    if ('storage' in __pillar__ and
        'osds' in __pillar__['storage'] and
        isinstance(__pillar__['storage']['osds'], list)):
        _devices = __pillar__['storage']['osds']
        log.debug("devices: {}".format(_devices))
        if 'format' in kwargs and kwargs['format'] != 'filestore':
            return []
    if ('storage' in __pillar__ and
        'data+journals' in __pillar__['storage'] and
        isinstance(__pillar__['storage']['data+journals'], list)):
        for entry in __pillar__['storage']['data+journals']:
            _devices.append(list(entry.keys())[0])
    log.debug("devices: {}".format(_devices))

    return _devices


def list_():
    """
    Return the array of ids.
    """
    mounted = [path.split('-')[1][:-5]
               for path in glob.glob("/var/lib/ceph/osd/*/fsid") if '-' in path]
    log.info("mounted osds {}".format(mounted))
    if 'ceph' in __grains__:
        grains = list(__grains__['ceph'].keys())
    else:
        grains = []
    return list(set(mounted + grains))


def rescinded():
    """
    Return the array of ids that are no longer mounted.
    """
    mounted = [int(path.split('-')[1][:-5])
               for path in glob.glob("/var/lib/ceph/osd/*/fsid") if '-' in path]
    log.info("mounted osds {}".format(mounted))
    # ids = __grains__['ceph'].keys() if 'ceph' in __grains__ else []
    _ids = _children()
    log.debug("ids: {}".format(_ids))
    for osd in mounted:
        log.debug("osd: {}".format(osd))
        if osd in _ids:
            _ids.remove(osd)
    return _ids


def _children():
    """
    Returns the OSDs assigned to this node according to Ceph
    """
    result = tree_from_any()
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


def _tree(**kwargs):
    """
    Return osd tree
    """
    cluster = rados.Rados(**kwargs)
    cluster.connect()
    cmd = json.dumps({"prefix": "osd tree", "format": "json"})
    _, output, _ = cluster.mon_command(cmd, b'', timeout=6)
    osd_tree = json.loads(output)
    log.debug(json.dumps(osd_tree, indent=4))
    return osd_tree


def tree_from_master():
    """
    Return osd tree; use if running on master node
    """
    kwargs = {
        'conffile': "/etc/ceph/ceph.conf",
    }
    return _tree(**kwargs)


def tree_from_any():
    """
    Return osd tree; can be run on any storage node (needs bootstrap-osd keyring)
    """
    kwargs = {
        'conffile': "/etc/ceph/ceph.conf",
        'conf': {
            'keyring': '/var/lib/ceph/bootstrap-osd/ceph.keyring',
        },
        'name': 'client.bootstrap-osd'
    }
    return _tree(**kwargs)


class OSDWeight(object):
    """
    Manage the setting and restoring of OSD crush weights
    """

    def __init__(self, _id, **kwargs):
        """
        Initialize settings, connect to Ceph cluster
        """
        self.osd_id = _id
        self.settings = {
            'conf': "/etc/ceph/ceph.conf",
            'filename': '/var/run/ceph/osd.{}-weight'.format(_id),
            'timeout': 60,
            'keyring': '/etc/ceph/ceph.client.admin.keyring',
            'client': 'client.admin',
            'delay': 6
        }
        self.settings.update(kwargs)
        log.debug("settings: {}".format(pprint.pformat(self.settings)))
        # self.cluster = rados.Rados(conffile=self.settings['conf'])
        self.cluster = rados.Rados(conffile=self.settings['conf'],
                                   conf=dict(keyring=self.settings['keyring']),
                                   name=self.settings['client'])
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
                log.info("Restoring weight {} to osd.{}".format(saved_weight, self.osd_id))
                self.reweight(saved_weight)

    def reweight(self, weight):
        """
        Set the weight for the OSD
        Note: haven't found the equivalent api call for reweight
        """
        cmd = ("ceph --keyring={} --name={} osd crush reweight osd.{} "
               "{}".format(self.settings['keyring'], self.settings['client'],
                           self.osd_id, weight))
        return __salt__['helper.run'](cmd)

    def osd_df(self):
        """
        Retrieve df entry for an osd
        """
        cmd = json.dumps({"prefix": "osd df", "format": "json"})
        _, output, _ = self.cluster.mon_command(cmd, b'', timeout=6)
        # log.debug(json.dumps((json.loads(output)['nodes']), indent=4))
        for entry in json.loads(output)['nodes']:
            if entry['id'] == int(self.osd_id):
                log.debug(pprint.pformat(entry))
                return entry
        log.warning("ID {} not found".format(self.osd_id))
        return {}

    # pylint: disable=invalid-name
    def osd_safe_to_destroy(self):
        """
        Returns safe-to-destroy output, does not return JSON
        """
        cmd = json.dumps({"prefix": "osd safe-to-destroy",
                          "ids": ["{}".format(self.osd_id)]})
        rc, _, output = self.cluster.mon_command(cmd, b'', timeout=6)
        return rc, output

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
            rc, msg = self.osd_safe_to_destroy()
            if rc == 0:
                log.info("osd.{} is safe to destroy".format(self.osd_id))
                return ""
            entry = self.osd_df()
            if 'pgs' in entry:
                if entry['pgs'] == 0:
                    log.warning("osd.{} has {} PGs remaining but {}".
                                format(self.osd_id, entry['pgs'], msg))
                else:
                    log.warning("osd.{} has {} PGs remaining".format(self.osd_id, entry['pgs']))
                    if last_pgs != entry['pgs']:
                        # Making progress, reset countdown
                        i = 0
                        last_pgs = entry['pgs']
            else:
                msg = "osd.{} does not exist {}".format(self.osd_id, msg)
                log.warning(msg)
            i += 1
            time.sleep(self.settings['delay'])

        msg = "Timeout expired - OSD {} has {} PGs remaining".format(self.osd_id, last_pgs)
        log.error(msg)
        return msg


class CephPGs(object):
    """
    Query PG states and pause until all are active+clean
    """

    def __init__(self, **kwargs):
        """
        Initialize settings, connect to Ceph cluster
        """
        self.settings = {
            'conf': "/etc/ceph/ceph.conf",
            'timeout': 120,
            'keyring': '/etc/ceph/ceph.client.admin.keyring',
            'client': 'client.admin',
            'delay': 12
        }
        self.settings.update(kwargs)
        log.debug("settings: {}".format(pprint.pformat(self.settings)))
        self.cluster = rados.Rados(conffile=self.settings['conf'],
                                   conf=dict(keyring=self.settings['keyring']),
                                   name=self.settings['client'])
        try:
            self.cluster.connect()
        except Exception as error:
            raise RuntimeError("connection error: {}".format(error))

    def quiescent(self):
        """
        Wait until PGs are active+clean or timeout is reached.  Default is a
        2 minute sliding window.  Return if no PGs are present.
        """
        i = 0
        last = []
        if self.settings['delay'] == 0:
            raise ValueError("The delay cannot be 0")
        while i < self.settings['timeout']/self.settings['delay']:
            current = self.pg_states()
            if not current:
                log.warning("PGs are not present")
                return
            if len(current) == 1 and current[0]['name'] == 'active+clean':
                log.warning("PGs are active+clean")
                return
            log.warning("Waiting on active+clean {}".format(pprint.pformat(current)))
            if self._pg_value(last) != self._pg_value(current):
                # Making progress - reset counter
                log.debug("Resetting active+clean counter")
                i = 0
                last = current

            i += 1
            log.debug("iteration: {} last: {} current: {}".
                      format(i, self._pg_value(last), self._pg_value(current)))
            time.sleep(self.settings['delay'])

        log.error("Timeout expired waiting on active+clean")
        raise RuntimeError("Timeout expired waiting on active+clean")

    # pylint: disable=no-self-use
    def _pg_value(self, entries):
        """
        Return the value for the active+clean entry
        """
        for entry in entries:
            if 'name' in entry and entry['name'] == 'active+clean':
                return entry['num']
        return 0

    def pg_states(self):
        """
        Retrieve pg status from Ceph
        """
        cmd = json.dumps({"prefix": "pg stat", "format": "json"})
        _, output, _ = self.cluster.mon_command(cmd, b'', timeout=6)
        # log.debug(json.dumps((json.loads(output)['nodes']), indent=4))
        return json.loads(output)['num_pg_by_state']


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


def ceph_quiescent(**kwargs):
    """
    Check that PGs are active+clean
    """
    settings = _settings(**kwargs)

    ceph_pgs = CephPGs(**settings)
    ceph_pgs.quiescent()


def zero_weight(osd_id, wait=True, **kwargs):
    """
    Set weight to zero and wait until PGs are moved
    """
    settings = _settings(**kwargs)

    osdweight = OSDWeight(osd_id, **settings)
    osdweight.save()
    _rc, _stdout, _stderr = osdweight.reweight('0.0')
    if _rc != 0:
        return "Reweight failed"
    if wait:
        return osdweight.wait()
    return ""


def restore_weight(osd_id, **kwargs):
    """
    Restore the previous setting for an OSD if possible
    """
    settings = _settings(**kwargs)

    osdweight = OSDWeight(osd_id, **settings)
    osdweight.restore()
    return True


def _find_paths(device):
    """
    Return matching pathnames, special case devices ending with digits
    """
    if re.match(r'.*\d$', device):
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
    _, stdout, _ = __salt__['helper.run'](cmd)
    return stdout


# pylint: disable=too-many-instance-attributes
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

    # pylint: disable=invalid-name
    V1 = 'v1'
    # pylint: disable=invalid-name
    V2 = 'v2'
    DEFAULT_FORMAT_FOR_V1 = 'filestore'
    DEFAULT_FORMAT_FOR_V2 = 'bluestore'

    # pylint: disable=unused-argument
    def __init__(self, device, **kwargs):
        """
        Set attributes for an OSD
        """
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
        # pylint: disable=invalid-name
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

    # pylint: disable=no-self-use
    def _convert_tli(self, osds):
        """
        Simplify names to short devices
        """
        result = {}
        for osd in osds:
            short_osd = readlink(osd)
            result[short_osd] = {}
            for attr in osds[osd]:
                if attr == 'journal' or attr == 'wal' or attr == 'db':
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

        error = "Missing device {} in the Salt mine for cephdisks.list".format(self.device)
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
            return None
        else:
            error = "Mine on {} for cephdisks.list".format(__grains__['id'])
            log.error(error)
            raise RuntimeError(error)

    def _set_small(self):
        """
        Check disk is less than 10GB, useful in VM environments
        """
        return self.size < 10000000000  # 10GB

    def _config_version(self):
        """
        Return version based on structure
        """
        version = None
        if 'storage' in __pillar__ and 'osds' in __pillar__['storage']:
            version = OSDConfig.V1
        elif 'ceph' in __pillar__ and 'storage' in __pillar__['ceph']:
            version = OSDConfig.V2
        return version

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

    # pylint: disable=no-self-use
    def _convert_data_journals(self, struct):
        """
        Create new structure with short device names
        """
        result = {}
        for pair in struct:
            for osd, journal in six.iteritems(pair):
                result[readlink(osd)] = readlink(journal)
        return result

    # pylint: disable=no-self-use
    def _check_existence(self, key, ident, device, default=None):
        """
        Check that key exists and return value
        """
        if key in ident[device]:
            return ident[device][key]
        return default

    # pylint: disable=no-self-use,no-else-return
    def set_journal_size(self, default=None):
        """
        Return journal size if defined.  Otherwise, return a size that is
        10% of the corresponding disk if the disk is under 10GB.  For larger
        disks, return 5G.
        """
        if self._config_version() == OSDConfig.V1:
            return self._journal_default()
        elif self._config_version() == OSDConfig.V2:
            return self._check_existence('journal_size', self.tli, self.device,
                                         default=self._journal_default())
        else:
            return None

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
                        if int(disk['Bytes']) < 10000000000:  # 10GB
                            return "{}K".format(int(int(disk['Bytes']) * 0.0001))
                        return "5242880K"
                log.error("Journal {} not found in cephdisks.list mine".format(self.journal))
            return None
        else:
            # Journal is same as OSD
            if self.small:
                if self.size:
                    return "{}K".format(int(int(self.size) * 0.0001))
                log.error("Size for {} not found in cephdisks.list mine".format(self.device))
                return None
            else:
                return "5242880K"

    def set_wal_size(self, default=None):
        """
        Return the size of the wal, if defined
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('wal_size', self.tli, self.device, default=default)
        return None

    def set_wal(self):
        """
        Return the device of the wal, if defined
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('wal', self.tli, self.device)
        return None

    def set_db_size(self, default=None):
        """
        Return the size of the db, if defined
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('db_size', self.tli, self.device, default=default)
        return None

    def set_db(self):
        """
        Return the device of the db, if defined
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('db', self.tli, self.device)
        return None

    def set_encryption(self, default=False):
        """
        Return the type of encryption
        """
        if self._config_version() == OSDConfig.V2:
            return self._check_existence('encryption', self.tli, self.device, default=default)
        return None

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
        # self.disks = __salt__['mine.get'](tgt=__grains__['id'], fun='cephdisks.list')

    def clean(self):
        """
        Remove existing partitions from OSD.  Addresses issue of
        damaged filesystems.

        Note: expected to only run inside of "not is_prepared"
        """
        if (self.osd.disk_format != 'filestore' and
            self.osd.disk_format != 'bluestore'):
            log.warning(("Skipping clean of device {} with format "
                         "{}").format(self.osd.device, self.osd.disk_format))
            return

        pathnames = _find_paths(self.osd.device)
        if pathnames:
            cmd = "sgdisk -Z --clear -g {}".format(self.osd.device)
            _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
            if _rc != 0:
                raise RuntimeError("{} failed".format(cmd))

    def partition(self):
        """
        Create partitions for supported formats
        """
        if self.osd.disk_format == 'filestore':
            self._xfs_partitions(self.osd.device, self.osd.size)
        if self.osd.disk_format == 'bluestore':
            self._bluestore_partitions()
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
                    self.create(self.osd.journal, [('journal',
                                                   self.osd.journal_size),
                                                   ('osd', None)])
                else:
                    # Create journal of journal_size on journal device
                    # and data partition on whole disk of device
                    self.create(self.osd.journal, [('journal',
                                                   self.osd.journal_size)])
                    self.create(self.osd.device, [('osd', None)])
            else:
                if self.osd.journal == self.osd.device:
                    # Create journal, data as remainder
                    self.create(self.osd.device, [('journal',
                                                  self.osd.journal_size),
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
                # FIXME: The calls in the conditionals are the same.

    def _bluestore_partitions(self):
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

        if (self.osd.wal or self.osd.db) and self.osd.encryption:
            log.warning(("You deploy encrypted WAL and/or DB on a dedicated "
                         "device. Specifying sizes is now handled via your ceph.conf"))
            return

        if self.osd.wal and self.osd.db:
            if self.osd.wal_size:
                if self.osd.wal == self.osd.device:
                    log.warning(("WAL size is unsupported for same device of "
                                 "{}".format(self.osd.device)))
                else:
                    # Create wal of wal_size on wal device
                    self.create(self.osd.wal, [('wal', self.osd.wal_size)])
            else:
                # pylint: disable=line-too-long
                log.warning("No size specified for wal {}. Using default sizes.".format(self.osd.wal))

            if self.osd.db_size:
                if self.osd.wal == self.osd.device:
                    # pylint: disable=line-too-long
                    log.warning("DB size is unsupported for same device of {}".format(self.osd.device))
                else:
                    # Create db of db_size on db device
                    self.create(self.osd.db, [('db', self.osd.db_size)])
            else:
                log.warning("No size specified for db {}. Using default sizes".format(self.osd.db))
        else:
            if self.osd.wal:
                if self.osd.wal_size:
                    if self.osd.wal == self.osd.device:
                        log.warning(("WAL size is unsupported for same device of "
                                     "{}".format(self.osd.device)))
                    else:
                        # Create wal of wal_size on wal device
                        self.create(self.osd.wal, [('wal', self.osd.wal_size)])
            else:
                if self.osd.wal_size:
                    log.warning(("WAL size is unsupported for same device of "
                                 "{}".format(self.osd.device)))

            if self.osd.db:
                if self.osd.db_size:
                    if self.osd.db == self.osd.device:
                        log.warning(("DB size is unsupported for same device of "
                                     "{}".format(self.osd.device)))
                    else:
                        # Create db of db_size on db device
                        self.create(self.osd.db, [('db', self.osd.db_size)])
            else:
                if self.osd.db_size:
                    log.warning(("DB size is unsupported for same device of "
                                 "{}".format(self.osd.device)))

    def create(self, device, _partitions):
        """
        Create a partition
        """
        last_partition = self._last_partition(device)
        log.debug("last partition: {}".format(last_partition))

        index = 1
        for partition_type, size in _partitions:
            number = last_partition + index
            if size:
                cmd = ("/usr/sbin/sgdisk -n {}:0:+{} -t {}:{} "
                       "{}".format(number, size, number,
                                   self.osd.types[partition_type], device))
            else:
                cmd = ("/usr/sbin/sgdisk -N {} -t {}:{} "
                       "{}".format(number, number,
                                   self.osd.types[partition_type], device))
            _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
            if _rc != 0:
                log.debug("Stdout of {}: {}".format(cmd, _stdout))
                log.debug("Stderr of {}: {}".format(cmd, _stderr))
                raise RuntimeError("{} failed".format(cmd))
            log.info("partprobing disk {}".format(device))
            self._part_probe(device)
            # Seems odd to wipe a just created partition ; however, ghost
            # filesystems on reused disks seem to be an issue
            if os.path.exists("{}{}".format(device, number)):
                prefix = ''
                if device.startswith('/dev/nvme'):
                    prefix = 'p'
                wipe_cmd = ("dd if=/dev/zero of={}{}{} bs=4096 count=1 "
                            "oflag=direct".format(device, prefix, number))
                __salt__['helper.run'](wipe_cmd)
            index += 1

    # pylint: disable=no-self-use
    def _part_probe(self, device):
        """
        Run partprobe until successful or timeout is reached
        """
        wait_time = 1
        retries = 5
        cmd = "/usr/sbin/partprobe {}".format(device)
        for _ in range(1, retries + 1):
            _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
            if _rc == 0:
                return
            time.sleep(wait_time)
        raise RuntimeError("{} failed".format(cmd))

    # pylint: disable=no-self-use
    def _last_partition(self, device):
        """
        Return the last partition. Only the number is needed for the sgdisk
        command.
        """
        pathnames = _find_paths(device)
        if pathnames:
            _partitions = sorted([re.sub(r"{}p?".format(device), '', p)
                                  for p in pathnames], key=int)
            log.debug("partitions: {}".format(_partitions))
            last_part = _partitions[-1]
            return int(last_part)
        return 0


def partition(device):
    """
    Create necessary partitions for defined sizes
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
                # Journal on same device
                return 2
            if self.osd.disk_format == 'bluestore':
                return 1
        return self.highest_partition(self.osd.device, 'osd')

    def is_partition(self, partition_type, device, _partition):
        """
        Check partition type
        """
        cmd = "/usr/sbin/sgdisk -i {} {}".format(_partition, device)
        _, result, _ = __salt__['helper.run'](cmd)
        _id = "Partition GUID code: {}".format(self.osd.types[partition_type])
        return _id in result

    def highest_partition(self, device, partition_type, nvme_partition=True):
        """
        Return the highest created partition of partition type

        For NVMe devices, the partition name is 'p' + digit with one
        exception if the result will be used by the sgdisk command.  Then,
        the raw number is needed.
        """
        if device:
            log.debug("{} device: {}".format(partition_type, device))
            pathnames = _find_paths(device)
            # the to int -> key=int conversion fails here
            _partitions = sorted([re.sub(r"{}p?".format(device), '', p)
                                  for p in pathnames], key=int, reverse=True)
            # best strategy? remove key=int and do checks before conversion ourselves?
            log.debug("partitions: {}".format(_partitions))
            for _partition in _partitions:
                log.debug("checking partition {} on device {}".format(_partition, device))
                # Not confusing at all - use digit for NVMe too
                if self.is_partition(partition_type, device, _partition):
                    log.debug("found partition {} on device {}".format(_partition, device))
                    if re.match(r'.*\d$', device) and nvme_partition:
                        _partition = "p{}".format(_partition)
                    return _partition
        self.error = "Partition type {} not found on {}".format(partition_type, device)
        log.error(self.error)
        return 0

    # pylint: disable=no-self-use
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

    # pylint: disable=no-self-use
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

    # pylint: disable=no-self-use
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
                args = "{}{} {}{}".format(device,
                                          self.highest_partition(device, 'osd'),
                                          self.osd.journal,
                                          self.highest_partition(self.osd.journal,
                                                                 'journal'))
            else:
                args = "{}{} {}{}".format(device,
                                          self.highest_partition(device, 'osd'),
                                          device,
                                          self.highest_partition(self.osd.device,
                                                                 'journal'))
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
                _partition = self.highest_partition(self.osd.wal, 'wal')
                if _partition:
                    args += "--block.wal {}{} ".format(self.osd.wal, _partition)
                else:
                    args += "--block.wal {} ".format(self.osd.wal)

            # DB cornercase with sizes
            if self.osd.db and self.osd.db_size and self.osd.db != self.osd.device:
                _partition = self.highest_partition(self.osd.db, 'db')
                if _partition:
                    args += "--block.db {}{} ".format(self.osd.db, _partition)
                else:
                    args += "--block.db {} ".format(self.osd.db)

            # Generic case withouth sizes
            if self.osd.wal and not (self.osd.wal_size or self.osd.db_size):
                args += "--block.wal {} ".format(self.osd.wal)
            if self.osd.db and not (self.osd.wal_size or self.osd.db_size):
                args += "--block.db {} ".format(self.osd.db)

        if self.osd.encryption and (self.osd.wal_size or self.osd.db_size):
            log.warning(""" The --wal-size and --db-size options are not supported
                         for encrypted OSDs, so the values you specified will
                         be ignored. Please specify the WAL and DB sizes
                         via ceph.conf with:
                                            bluestore block db size = size
                                            bluestore block wal size = size """)

        if self.osd.encryption:
            if self.osd.db:
                args += "--block.db {} ".format(self.osd.db)
            if self.osd.wal:
                args += "--block.wal {} ".format(self.osd.wal)

        # fails if the device is already partitioned but the partitionnumber
        # is not 1 should never be partitioned..
        if self.is_partitioned(self.osd.device):
            if re.match(r'.*\d$', self.osd.device):
                args += "{}p1".format(self.osd.device)
            else:
                args += "{}1".format(self.osd.device)
        else:
            args += "{}".format(self.osd.device)
        return args

    def prepare(self, osd_id=None):
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
            cmd = "PYTHONWARNINGS=ignore ceph-disk -v prepare "

            # specify OSD ID when replacing
            if osd_id:
                cmd += "--osd-id {} ".format(osd_id)
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

            cmd += ("--data-dev --journal-dev --cluster {} --cluster-uuid "
                    "{} ".format(self._cluster_name(), self._fsid()))
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
                if re.match(r'.*\d$', self.osd.device):
                    prefix = 'p'
                cmd = "PYTHONWARNINGS=ignore ceph-disk -v activate --mark-init systemd --mount "
                cmd += "{}{}{}".format(self.osd.device, prefix, self.osd_partition())

        log.info("activate: {}".format(cmd))
        return cmd

    # pylint: disable=too-many-return-statements
    def is_incorrect(self):
        """
        Check that an OSD is configured properly.  Compare formats, separate
        partitions and size of partitions.
        """
        if self.osd.encryption:
            log.warning("Encrypted OSDs not supported")
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
                    log.info(("OSD {} does not match format "
                              "{}".format(pathname, self.osd.disk_format)))
                    return True

            if self.osd.disk_format == 'filestore' and self.osd.journal:
                result = self._check_device(pathname, 'journal',
                                            self.osd.journal,
                                            self.osd.journal_size)
                if result:
                    return True

            if self.osd.disk_format == 'bluestore':
                if self.osd.wal:
                    if os.path.exists("{}/block.wal".format(pathname)):
                        result = self._check_device(pathname, 'block.wal',
                                                    self.osd.wal,
                                                    self.osd.wal_size)
                        if result:
                            return True
                    else:
                        # Missing WAL
                        return True
                else:
                    if os.path.exists("{}/block.wal".format(pathname)):
                        # WAL present but not configured
                        return True
                if self.osd.db:
                    if os.path.exists("{}/block.db".format(pathname)):
                        result = self._check_device(pathname, 'block.db',
                                                    self.osd.db,
                                                    self.osd.db_size)
                        if result:
                            return True
                    else:
                        # Missing DB
                        return True
                else:
                    if os.path.exists("{}/block.db".format(pathname)):
                        # DB present but not configured
                        return True

        return False

    def _check_device(self, pathname, attr, device, size):
        """
        Check that the device and size match the configuration
        """
        devicename = readlink("{}/{}".format(pathname, attr))
        if device and not devicename.startswith(device):
            log.info("OSD {} {} does not match {}".format(attr, devicename, device))
            return True
        if size:
            cmd = "blockdev --getsize64 {}".format(devicename)
            _, _stdout, _stderr = __salt__['helper.run'](cmd)
            bsize = int(_stdout)
            _bytes = self._convert(size)
            if _bytes != bsize:
                log.info("OSD {} size {} does not match {} ({})".format(attr, bsize, size, _bytes))
                return True
        return None

    def _convert(self, size):
        """
        Expand size to bytes
        """
        suffixes = {'K': 2**10, 'M': 2**20, 'G': 2**30, 'T': 2**40}
        suffix = size[-1:].upper()
        bsize = int(size[:-1]) * suffixes[suffix]
        log.debug("suffix: {} bsize: {}".format(suffix, bsize))
        return bsize


def _detect(osd_id, pathname="/var/lib/ceph/osd"):
    """
    Return the osd type
    """
    filename = "{}/ceph-{}/type".format(pathname, osd_id)
    if os.path.exists(filename):
        with open(filename, 'r') as osd_type:
            return osd_type.read().rstrip()
    return None


def split_partition(_partition):
    """
    Return the device and partition
    """
    part = readlink(_partition)
    # if os.path.exists(part):
    log.debug("splitting partition {}".format(part))
    match = re.match(r"(.+\D)(\d+)", part)
    if not match:
        return None, None
    disk = match.group(1)
    if disk.endswith('p'):
        disk = disk[:-1]
        log.debug("Truncating p {}".format(disk))
    return disk, match.group(2)
    # return None, None


class OSDRemove(object):
    """
    Manage the graceful removal of an OSD
    """

    # pylint: disable=unused-argument
    def __init__(self, osd_id, device, weight, grains, force=False, human=True, **kwargs):
        """
        Initialize settings
        """
        self.osd_id = osd_id
        self.osd_fsid = device.osd_fsid
        self.device = device
        self.partitions = self.set_partitions()
        self._weight = weight
        self._grains = grains
        self.force = force
        self.human = human
        self.keyring = kwargs.get('keyring', None)
        self.client = kwargs.get('client', None)

    def set_partitions(self):
        """
        Return queried partitions or fallback to grains
        """
        _partitions = self.device.partitions(self.osd_id)
        if not _partitions:
            log.debug("grains: \n{}".format(pprint.pformat(__grains__['ceph'])))
            if str(self.osd_id) in __grains__['ceph']:
                _partitions = __grains__['ceph'][str(self.osd_id)]['partitions']
            else:
                log.error("Id {} missing from grains".format(self.osd_id))
                return None
        log.debug("partitions: \n{}".format(pprint.pformat(_partitions)))
        return _partitions

    # pylint: disable=too-many-return-statements
    def remove(self):
        """
        Wrapper for removing an OSD
        """
        if not self.partitions:
            msg = "OSD {} is not present on minion {}".format(self.osd_id, __grains__['id'])
            log.error(msg)
            return msg

        if self.force:
            log.warning("Forcing OSD removal")

            # Terminate
            self.terminate()

            # Best effort depending on the reason for the forced removal
            self.mark_destroyed()
            update_destroyed(self._osd_disk(), self.osd_id)
        else:
            for func in [self.empty, self.terminate]:
                msg = func()
                if self.human and msg:
                    log.error(msg)
                    return msg

            # Inform Ceph
            #
            # Consider this a hard requirement for graceful removal. If the
            # OSD cannot be marked and recorded, stop the process.
            if self.mark_destroyed():
                msg = update_destroyed(self._osd_disk(), self.osd_id)
                if msg:
                    log.error(msg)
                    return msg
                log.info("OSD {} marked and recorded".format(self.osd_id))
            else:
                msg = "Failed to mark OSD {} as destroyed".format(self.osd_id)
                log.error(msg)
                return msg

        for func in [self.unmount, self.wipe, self.destroy]:
            msg = func()
            if msg:
                log.error(msg)
                return msg

        # Remove grain
        self._grains.delete(self.osd_id)

        return ""

    def empty(self):
        """
        Wait until all PGs evacuate an OSD
        """
        self._weight.save()
        _rc, _stdout, _stderr = self._weight.reweight('0.0')
        if _rc != 0:
            msg = "Reweight failed"
            log.error(msg)
            return msg
        return self._weight.wait()

    def terminate(self):
        """
        Stop the ceph-osd without error
        """
        cmd = "systemctl disable ceph-osd@{}".format(self.osd_id)
        __salt__['helper.run'](cmd)
        # How long will this hang on a broken OSD
        cmd = "systemctl stop ceph-osd@{}".format(self.osd_id)
        __salt__['helper.run'](cmd)
        cmd = r"pkill -f ceph-osd.*id\ {}\ --".format(self.osd_id)
        __salt__['helper.run'](cmd)
        time.sleep(1)
        cmd = r"pkill -9 -f ceph-osd.*id\ {}\ --".format(self.osd_id)
        __salt__['helper.run'](cmd)
        time.sleep(1)
        cmd = r"pgrep -f ceph-osd.*id\ {}\ --".format(self.osd_id)
        _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
        if _rc == 0:
            return "Failed to terminate OSD {} - pid {}".format(self.osd_id, _stdout)
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
                    _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
                    log.debug("returncode: {}".format(_rc))
                    if _rc != 0:
                        msg = "Unmount failed - check for processes on {}".format(entry[0])
                        log.error(msg)
                        return msg
                    os.rmdir(entry[1])

        if '/dev/dm' in self.partitions['osd']:
            cmd = "dmsetup remove {}".format(self.partitions['osd'])
            __salt__['helper.run'](cmd)
        return ""

    def _mounted(self):
        """
        Find the mount points for the OSD and lockbox.
        """
        _devices = []
        for attr in ['osd', 'lockbox']:
            if attr in self.partitions:
                _devices.append(readlink(self.partitions[attr]))
        log.debug("mounted: {}".format(_devices))
        return _devices

    def wipe(self):
        """
        Erase the beginning of any filesystems
        """
        if self.partitions:
            for _, _partition in six.iteritems(self.partitions):
                if os.path.exists(_partition):
                    cmd = "dd if=/dev/zero of={} bs=4M count=1 oflag=direct".format(_partition)
                    _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
                    if _rc != 0:
                        return "Failed to wipe partition {}".format(_partition)
        else:
            msg = "Nothing to wipe - no partitions available"
            log.warning(msg)
        return ""

    def destroy(self):
        """
        Destroy the osd disk and any partitions on other disks
        """
        # pylint: disable=attribute-defined-outside-init
        self.osd_disk = self._osd_disk()
        msg = self._delete_partitions()
        if msg:
            return msg
        self._wipe_gpt_backups()

        msg = self._delete_osd()
        if msg:
            return msg

        self._settle()
        return ""

    def _osd_disk(self):
        """
        Determine the data disk of an OSD
        """
        if 'lockbox' in self.partitions:
            _partition = self.partitions['lockbox']
        else:
            _partition = self.partitions['osd']
        disk, _ = split_partition(_partition)
        return disk

    def _delete_partitions(self):
        """
        Delete the partitions
        """
        for attr in self.partitions:
            log.debug("Checking attr {}".format(attr))
            if '/dev/dm' in self.partitions[attr]:
                cmd = "dmsetup remove {}".format(self.partitions[attr])
                __salt__['helper.run'](cmd)
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
                    disk, _partition = split_partition(self.partitions[attr])
                    if disk:
                        log.debug("disk: {} partition: {}".format(disk, _partition))
                        cmd = "sgdisk -d {} {}".format(_partition, disk)
                        _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
                        if _rc != 0:
                            return "Failed to delete partition {} on {}".format(_partition, disk)
            else:
                log.error("Partition {} does not exist".format(short_name))
        return ""

    def _wipe_gpt_backups(self):
        """
        Wipe the backup GPT partitions
        """
        if self.osd_disk and os.path.exists(self.osd_disk):
            cmd = "blockdev --getsz {}".format(self.osd_disk)
            _, _stdout, _stderr = __salt__['helper.run'](cmd)
            end_of_disk = int(_stdout)
            seek_position = int(end_of_disk/4096 - 33)
            cmd = ("dd if=/dev/zero of={} bs=4096 count=33 seek={} "
                   "oflag=direct".format(self.osd_disk, seek_position))
            __salt__['helper.run'](cmd)
        return ""

    def _delete_osd(self):
        """
        Erase the data disk
        """
        if self.osd_disk and os.path.exists(self.osd_disk):
            cmd = "sgdisk -Z --clear -g {}".format(self.osd_disk)
            _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
            if _rc != 0:
                msg = "Failed to delete OSD {}".format(self.osd_disk)
                log.error(msg)
                return msg
        return ""

    # pylint: disable=no-self-use
    def _settle(self):
        """
        Wait for the OS to update
        """
        for cmd in ['udevadm settle --timeout=20',
                    'partprobe',
                    'udevadm settle --timeout=20']:
            __salt__['helper.run'](cmd)

    def mark_destroyed(self):
        """
        Mark the ID as destroyed in Ceph
        """
        auth = ""
        if self.keyring and self.client:
            auth = "--keyring={} --name={}".format(self.keyring, self.client)
        cmd = "ceph {} osd destroy {} --yes-i-really-mean-it".format(auth, self.osd_id)
        _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
        return _rc == 0


def remove(osd_id, **kwargs):
    """
    Remove an OSD
    """
    settings = _settings(**kwargs)

    if 'force' in kwargs and kwargs['force']:
        osdw = None
    else:
        osdw = OSDWeight(osd_id, **settings)
    osdd = OSDDevices()
    osdg = OSDGrains(osdd)

    osdr = OSDRemove(osd_id, osdd, osdw, osdg, **settings)
    return osdr.remove()


def is_empty(osd_id, **kwargs):
    """
    Check whether an OSD has an PGs
    """
    settings = _settings(**kwargs)
    OSDDevices()  # verify that this call is needed
    osdw = OSDWeight(osd_id, **settings)
    return osdw.is_empty()


def terminate(osd_id):
    """
    Stop OSD process
    """
    osdd = OSDDevices()
    osdr = OSDRemove(osd_id, osdd, None, None)
    return osdr.terminate()


def unmount(osd_id):
    """
    Unmount OSD filesystems
    """
    osdd = OSDDevices()
    osdg = OSDGrains(osdd)
    osdr = OSDRemove(osd_id, osdd, None, osdg)
    return osdr.unmount()


def wipe(osd_id):
    """
    Wipe the data on the partitions
    """
    osdd = OSDDevices()
    osdg = OSDGrains(osdd)
    osdr = OSDRemove(osd_id, osdd, None, osdg)
    return osdr.wipe()


def destroy(osd_id):
    """
    Remove the OSD partitions
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
        # pylint: disable=attribute-defined-outside-init
        self.osd_id = osd_id
        _partitions = {}
        mount_dir = "{}/ceph-{}".format(self.pathname, self.osd_id)
        lockbox_dir = self._lockbox_dir()
        log.info("Checking /proc/mounts for {}".format(mount_dir))
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                entry = line.split()
                if entry[1] == mount_dir:
                    log.info("osd: {}".format(line))
                    _partitions['osd'] = self._uuid_device(entry[0])
                if entry[1] == lockbox_dir:
                    log.info("lockbox: {}".format(line))
                    _partitions['lockbox'] = self._uuid_device(entry[0])

        for device_type in ['journal', 'block', 'block.db', 'block.wal', 'block_dmcrypt']:
            result = self._uuid_device("{}/{}".format(mount_dir, device_type))
            if result:
                _partitions[device_type] = result
        return _partitions

    def _lockbox_dir(self):
        """
        Returns lockbox pathname
        """
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
            return None

    # pylint: disable=no-self-use, no-else-return
    def _uuid_device(self, device):
        """
        Return the uuid device, prefer the most descriptive
        """
        if os.path.exists(device):
            devicename = __salt__['cephdisks.device'](device)
            # if the devicename and device are the same, cephdisks.device did not find any symlinks
            if devicename != device:
                return devicename
            else:
                return readlink(device)
        return None


class OSDDestroyed(object):
    """
    Maintain a key value store for destroyed OSDs.

    The workflow can get complicated.  The first case is the normal case.  The
    use cases are

    1) Device has a by-path equivalent.  Save the by-path name and ID
    2) Device has no by-path equivalent.  Save the current device name as an
       indication to future runs that this device can safely be skipped. On
       the first attempt, return as failed with instructions.
    3) Admin is saving actual device name of new device.
    """

    def __init__(self):
        """
        Set the default filename.
        """
        self.filename = "/etc/ceph/destroyedOSDs.yml"

        # Keep yaml human readable/editable
        self.friendly_dumper = yaml.SafeDumper
        self.friendly_dumper.ignore_aliases = lambda self, data: True

    def update(self, device, osd_id, force=False):
        """
        Add the by-path version of device and osd_id.  If by-path does not
        exist, record current device and issue exception with instructions.
        If forced, record current device.
        """
        content = {}
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as destroyed:
                content = yaml.safe_load(destroyed)
                log.debug("content: {} {}".format(type(content), content))

        if device in content:
            # Exit early, no by-path equivalent from previous run
            return ""

        by_path = self._by_path(device)
        if by_path and not force:
            content[by_path] = osd_id
        else:
            # by-path device is missing, save current device to allow
            # the OSD to be removed and rely on admin following instructions
            # below OR admin is overriding the save manually with the new
            # device name.  In either case, save the device name with the ID.
            content[device] = osd_id

        with open(self.filename, 'w') as destroyed:
            destroyed.write(yaml.dump(content, Dumper=self.friendly_dumper,
                            default_flow_style=False))

        if by_path or force:
            return ""

        # Hard enough to read without the else indent
        example = '/dev/disk/by-id/new_device_name'
        msg = ("Device {} is missing a /dev/disk/by-path symlink.\n"
               "Device cannot be replaced automatically.\n\n"
               "Replace the device, find the new device name and run\n\n"
               "salt {} osd.update_destroyed {} {}"
               ).format(device, __grains__['id'], example, osd_id)
        log.error(msg)
        return msg

    def get(self, device):
        """
        Return ID
        """
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as destroyed:
                content = yaml.safe_load(destroyed)
            by_path = self._by_path(device)
            if by_path and by_path in content:
                return content[by_path]
            if device in content:
                return content[device]

        return ""

    # pylint: disable=no-self-use
    def _by_path(self, device):
        """
        Return the equivalent by-path device name
        """
        cmd = (r"find -L /dev/disk/by-path -samefile {}".format(device))
        _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
        if _stdout:
            _devices = _stdout.split()
            if _devices:
                return _devices[0]
        return ""

    def remove(self, device):
        """
        Remove entry
        """
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as destroyed:
                content = yaml.safe_load(destroyed)
            by_path = self._by_path(device)
            if by_path and by_path in content:
                del content[by_path]
            # Normally absent
            if device in content:
                del content[device]
            with open(self.filename, 'w') as destroyed:
                destroyed.write(yaml.dump(content, Dumper=self.friendly_dumper,
                                default_flow_style=False))

    def dump(self):
        """
        Display all devices, IDs
        """
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as destroyed:
                content = yaml.safe_load(destroyed)
            return content
        return ""


def update_destroyed(device, osd_id):
    """
    Save the ID
    """
    osd_d = OSDDestroyed()
    return osd_d.update(device, osd_id)


def find_destroyed(device):
    """
    Return the ID for a device
    """
    osd_d = OSDDestroyed()
    return osd_d.get(str(device))


def remove_destroyed(device):
    """
    Remove the device
    """
    osd_d = OSDDestroyed()
    osd_d.remove(device)
    return ""


def dump_destroyed():
    """
    Display all devices, IDs
    """
    osd_d = OSDDestroyed()
    return osd_d.dump()


# pylint: disable=too-few-public-methods
class OSDGrains(object):
    """
    Manage caching the device names for all OSDs.

    Note: Some logistics problems to work through.  When should retain be
    rerun and when should it not run.  In case of a failed disk, this may
    be the only source of the related partitions.  Rerunning retain will
    remove this entry.
    """

    def __init__(self, device, pathname="/var/lib/ceph/osd", filename="/etc/salt/grains"):
        """
        Initialize settings
        """
        self.pathname = pathname
        self.filename = filename
        self.partitions = device.partitions
        self.osd_fsid = device.osd_fsid

    def retain(self):
        """
        Save the OSD partitions into the grains
        """
        _ids = [path.split('-')[1] for path in glob.glob("/var/lib/ceph/osd/*") if '-' in path]
        storage = {}
        for osd_id in _ids:
            if self.partitions(osd_id):
                storage[osd_id] = {}
                storage[osd_id]['partitions'] = self.partitions(osd_id)
                storage[osd_id]['fsid'] = self.osd_fsid(osd_id)
                log.debug("osd {}: {}".format(osd_id, pprint.pformat(storage[osd_id])))
        self._grains(storage)

    def delete(self, osd_id):
        """
        Delete an OSD entry
        """
        content = {}
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as minion_grains:
                content = yaml.safe_load(minion_grains)
                # pylint: disable=bare-except
                try:
                    del content['ceph'][str(osd_id)]
                except:
                    log.error("Cannot delete osd {} from grains".format(osd_id))
            if content:
                self._update_grains(content)

    def _grains(self, storage):
        """
        Load and save grains when changed
        """
        content = {}
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as minion_grains:
                content = yaml.safe_load(minion_grains)
        if 'ceph' in content and content['ceph'] == storage:
            log.debug("No update for {}".format(self.filename))
        else:
            content['ceph'] = storage
            self._update_grains(content)

    # pylint: disable=no-self-use
    def _update_grains(self, content):
        """
        Update the yaml file without destroying other content
        """
        log.info("Updating {}".format(self.filename))

        # Keep yaml human readable/editable
        friendly_dumper = yaml.SafeDumper
        friendly_dumper.ignore_aliases = lambda self, data: True

        with open(self.filename, 'w') as minion_grains:
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


def deploy_lvm():
    """
    Dummy implementation to deplioy a ceph-volume OSD on an existing lv
    """
    for device in configured():
        _rc, _out, _err = __salt__['helper.run'](
            ['ceph-volume',
             'lvm',
             'prepare',
             '--bluestore',
             '--data',
             '{}1'.format(device)]
        )
    _rc, _out, _err = __salt__['helper.run'](['ceph-volume',
                                              'lvm',
                                              'activate',
                                              '--all'])


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
            previous_id = find_destroyed(device)
            __salt__['helper.run'](osdc.prepare(previous_id))
            __salt__['helper.run'](osdc.activate())
            remove_destroyed(device)
            if previous_id:
                restore_weight(previous_id)


def redeploy(simultaneous=False, **kwargs):
    """
    Empty all PGs in parallel initially if necessary.  Then remove and
    recreate each OSD that does not match its configuration.
    """
    if simultaneous:
        for _id in __grains__['ceph']:
            _part = _partition(_id)
            log.info("Partition: {}".format(_part))
            disk, _ = split_partition(_part)
            log.info("ID: {}".format(_id))
            log.info("Disk: {}".format(disk))
            if is_incorrect(disk):
                zero_weight(_id, wait=False)

    settings = _settings(**kwargs)
    for _id in __grains__['ceph']:
        _part = _partition(_id)
        log.info("Partition: {}".format(_part))
        disk, _ = split_partition(_part)
        log.info("ID: {}".format(_id))
        log.info("Disk: {}".format(disk))
        if not os.path.exists(_part) or is_incorrect(disk):
            pgs = CephPGs(**settings)
            pgs.quiescent()
            remove(_id, **settings)
            config = OSDConfig(disk)
            osdp = OSDPartitions(config)
            osdp.partition()
            osdc = OSDCommands(config)
            __salt__['helper.run'](osdc.prepare(_id))
            restore_weight(_id)
            __salt__['helper.run'](osdc.activate())
            remove_destroyed(disk)


def _partition(osd_id):
    """
    Return the recorded partitions from the grains
    """
    if 'lockbox' in __grains__['ceph'][osd_id]['partitions']:
        return __grains__['ceph'][osd_id]['partitions']['lockbox']
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
    _partition = osdc.highest_partition(readlink(device), 'osd', nvme_partition=False)
    if _partition == 0:
        log.debug("Do not know which partition to check on {}".format(device))
        return False
    log.debug("Checking partition {} on device {}".format(_partition, device))
    return osdc.is_partition('osd', config.device, _partition) and _fsck(config.device, _partition)


def _fsck(device, _partition):
    """
    Check filesystem on partition

    Note: xfs_repair returns immediately on success, but takes 3m39s to fail
    on some broken filesystems.  Not good for automation.
    """
    prefix = ''
    if re.match(r'.*\d$', device):
        prefix = 'p'
    # cmd = "/sbin/fsck -t xfs -n {}{}{}".format(device, prefix, partition)
    cmd = "/usr/sbin/xfs_admin -u {}{}{}".format(device, prefix, _partition)
    _rc, _stdout, _stderr = __salt__['helper.run'](cmd)
    return _rc == 0


def is_activated(device):
    """
    Check if the device has already been activated.  Return shell command.
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    _partition = osdc.highest_partition(readlink(device), 'osd')
    pathname = "{}{}".format(config.device, _partition)
    log.info("Checking /proc/mounts for {}".format(pathname))
    with open("/proc/mounts", "r") as mounts:
        for line in mounts:
            if line.startswith(pathname):
                return "/bin/true"
    return "/bin/false"


def prepare(device, osd_id=None):
    """
    Return ceph-disk command to prepare OSD.

    Note: calling the partition command directly from the sls file will not
    give the desired results since the evaluation of the prepare command (and
    the partition check) occurs prior to creating the partitions
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    return osdc.prepare(osd_id)


def activate(device):
    """
    Return ceph-disk command to activate OSD.
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    return osdc.activate()


def detect(osd_id):
    """
    Returns OSD type (e.g. Bluestore or Filestore)
    """
    return _detect(osd_id)


def is_incorrect(device):
    """
    Returns if the OSD does not match the desired configuration
    """
    config = OSDConfig(device)
    osdc = OSDCommands(config)
    return osdc.is_incorrect()


def partitions(osd_id):
    """
    List the related partitions to an OSD
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


def delete_grain(osd_id):
    """
    Delete an individual OSD grain
    """
    osdd = OSDDevices()
    osdg = OSDGrains(osdd)
    return osdg.delete(osd_id)


def report(human=True):
    """
    Display the difference between the pillar and grains for the OSDs
    """
    active, unmounted = _report_grains()
    un1, ch1 = _report_pillar(active)
    un2, ch2 = _report_original_pillar(active)

    unconfigured = un1 + un2
    changed = ch1 + ch2

    if human:
        if unconfigured or changed or unmounted:
            msg = ""
            if unconfigured:
                msg += "No OSD configured for \n{}\n".format("\n".join(unconfigured))
            if changed:
                msg += "Different configuration for \n{}\n".format("\n".join(changed))
            if unmounted:
                msg += "No OSD mounted for \n{}\n".format("\n".join(unmounted))
            return msg
        else:
            return "All configured OSDs are active"
    else:
        return {'unconfigured': unconfigured,
                'changed': changed,
                'unmounted': unmounted}


def _report_grains():
    """
    Return the active and unmounted lists
    """
    active = []
    unmounted = []
    if 'ceph' in __grains__:
        for _id in __grains__['ceph']:
            _partition = readlink(__grains__['ceph'][_id]['partitions']['osd'])
            disk, _ = split_partition(_partition)
            if disk:
                active.append(disk)
            log.debug("checking /var/lib/ceph/osd/ceph-{}/fsid".format(_id))
            if not os.path.exists("/var/lib/ceph/osd/ceph-{}/fsid".format(_id)):
                unmounted.append(disk)
            if 'lockbox' in __grains__['ceph'][_id]['partitions']:
                _partition = readlink(__grains__['ceph'][_id]['partitions']['lockbox'])
                disk, _ = split_partition(_partition)
                if disk:
                    active.append(disk)
    return active, unmounted


def _report_pillar(active):
    """
    Return the unconfigured and changed lists
    """
    log.debug("active: {}".format(active))

    unconfigured = []
    changed = []
    if 'ceph' in __pillar__:
        unconfigured = list(__pillar__['ceph']['storage']['osds'].keys())
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
    return unconfigured, changed


def _report_original_pillar(active):
    """
    Return the unconfigured and changed lists from the original pillar
    structure
    """
    unconfigured = []
    changed = []
    if 'storage' in __pillar__:
        unconfigured = __pillar__['storage']['osds']
        for _dj in __pillar__['storage']['data+journals']:
            unconfigured.append(*_dj.keys())
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
    return unconfigured, changed


__func_alias__ = {
                'list_': 'list',
                'empty': 'zero_weight',
                }
