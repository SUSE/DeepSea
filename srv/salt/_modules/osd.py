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
    # the 'ceph' grain will disappear over time.
    # the 'remove osd' operation will remove the grain
    # but the osd.deploy function will not add new a new one
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
            'rfilename': '/var/run/ceph/osd.{}-reweight'.format(_id),
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
        Capture the current weight and reweight allowing the admin to undo
        simple mistakes.

        The weight file defaults to the /var/run directory and will not
        survive a reboot.
        """
        entry = self.osd_df()
        log.debug("osd df: {}".format(pprint.pformat(entry)))
        if 'crush_weight' in entry and entry['crush_weight'] != 0:
            with open(self.settings['filename'], 'w') as weightfile:
                weightfile.write("{}\n".format(entry['crush_weight']))

        if 'reweight' in entry and entry['reweight'] != 1.0:
            with open(self.settings['rfilename'], 'w') as reweightfile:
                reweightfile.write("{}\n".format(entry['reweight']))

    def restore(self):
        """
        Set weight to previous setting
        """
        if os.path.isfile(self.settings['filename']):
            with open(self.settings['filename']) as weightfile:
                saved_weight = weightfile.read().rstrip('\n')
                log.info("Restoring weight {} to osd.{}".format(saved_weight, self.osd_id))
                self.update_weight(saved_weight)

        if os.path.isfile(self.settings['rfilename']):
            with open(self.settings['rfilename']) as reweightfile:
                saved_reweight = reweightfile.read().rstrip('\n')
                log.info("Restoring reweight {} to osd.{}".format(saved_reweight, self.osd_id))
                self.update_reweight(saved_reweight)

    def update_weight(self, weight):
        """
        Set the weight for the OSD
        Note: haven't found the equivalent api call for reweight
        """
        cmd = ("ceph --keyring={} --name={} osd crush reweight osd.{} "
               "{}".format(self.settings['keyring'], self.settings['client'],
                           self.osd_id, weight))
        return __salt__['helper.run'](cmd)

    def update_reweight(self, reweight):
        """
        Set the reweight for the OSD
        """
        cmd = ("ceph --keyring={} --name={} osd reweight osd.{} "
               "{}".format(self.settings['keyring'], self.settings['client'],
                           self.osd_id, reweight))
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
        return json.loads(output)['pg_summary']['num_pg_by_state']


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
    _rc, _stdout, _stderr = osdweight.update_weight('0.0')
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
    Return the short name for a symlink device.  On some systems, readlink
    fails to return the short name intermittently.  Retry as necessary, but
    ultimately return the result.
    """
    option = ''
    if follow:
        option = '-f'
    cmd = "readlink {} {}".format(option, device)
    log.info(cmd)
    for attempt in range(1, 11):
        if attempt > 1:
            log.info("retry {}".format(attempt))
        _, stdout, _ = __salt__['helper.run'](cmd)
        if not stdout.startswith("/dev/disk"):
            # Short name returned
            break
        time.sleep(0.1)
    return stdout


# pylint: disable=too-many-instance-attributes

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
    if re.match(r".+\dp$", disk):
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
        _rc, _stdout, _stderr = self._weight.update_weight('0.0')
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


def _partition(osd_id):
    """
    Return the recorded partitions from the grains
    """
    if 'lockbox' in __grains__['ceph'][osd_id]['partitions']:
        return __grains__['ceph'][osd_id]['partitions']['lockbox']
    return __grains__['ceph'][osd_id]['partitions']['osd']


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


def detect(osd_id):
    """
    Returns OSD type (e.g. Bluestore or Filestore)
    """
    return _detect(osd_id)


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


def takeover():
    """ This is horrible and should be implemented in ceph-volume """
    # picking osd.list here as it lists osd_ids by looking at mountpoints
    for osd_id in __salt__['osd.list']():
        # Use the mountpoint to identify the disk
        # another option is to use the partition but
        # if a osd is not mounted there might be a bigger problem
        cmd = "ceph-volume simple scan /var/lib/ceph/osd/ceph-{} --force".format(
            osd_id)
        return_code, _, stderr = __salt__['helper.run'](cmd)
        if int(return_code) != 0:
            log.error(stderr)
            return False  # rc? or raise?
    osd_ident_path = "/etc/ceph/osd/"
    osd_files = list()
    if os.path.exists(osd_ident_path):
        osd_files = [
            f for f in os.listdir(osd_ident_path)
            if os.path.isfile(os.path.join(osd_ident_path, f))
        ]
    for osd_file in osd_files:
        cmd = "ceph-volume simple activate --file {}".format(osd_ident_path +
                                                             osd_file)
        return_code, _, stderr = __salt__['helper.run'](cmd)
        if int(return_code) != 0:
            log.error(stderr)
            return False  # rc? or raise?
    return True


__func_alias__ = {
                'list_': 'list',
                'empty': 'zero_weight',
                }
