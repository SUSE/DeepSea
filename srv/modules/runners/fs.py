# -*- coding: utf-8 -*-
# pylint: skip-file
# pylint: disable=modernize-parse-error,too-few-public-methods
#
# The salt-api calls functions with keywords that are not needed
# pylint: disable=unused-argument
"""
 fs.py

 Runner for performing filesystem operations.
 Current task is to create/migrate /var/lib/ceph to btrfs subvolumes if applicable.
"""

from __future__ import print_function
from __future__ import absolute_import
import os
import logging
import salt.client
import salt.utils.error
# pylint: disable=relative-import
from deepsea_minions import DeepseaMinions
import six

log = logging.getLogger(__name__)


class Mount(object):
    """
    Structure representing the mount information for a given path.
    """
    def __init__(self, mountpoint, opts):
        self.mountpoint = mountpoint
        # List of mount opts in the form [ x, y, ... , {k : v}, ... ]
        self.opts = opts

    def get_opt(self, opt):
        """
        Return 'opt' if found in self.opts.  Since self.opts may contain dictionary entries,
        this may return the value of such an entry, should 'opt' match a dictionary entry key.
        """
        for option in self.opts:
            if option == opt:
                return option
            if isinstance(option, dict) and opt in option:
                return option[opt]

        # Didn't find it.
        return None

    def __str__(self):
        return "{} opts:{}".format(self.mountpoint, self.opts)


class Device(object):
    """
    Structure representing a disk/partition.
    """
    def __init__(self, dev, part_dev, dtype, uuid, fstype):
        # ie. 'vda'
        self.dev = dev
        # ie. 'vda2'
        self.part_dev = part_dev
        # String representing the device type: 'hd', 'ssd', 'unknown'
        self.dtype = dtype
        self.uuid = uuid
        # String representing the underlying fs: 'btrfs', 'xfs', etc
        self.fstype = fstype

    def __str__(self):
        return "uuid:{} (/dev/{}), {}, {}".format(self.uuid, self.part_dev, self.dtype, self.fstype)


class Path(object):
    """
    Structure representing a path on a filesystem.
    """
    def __init__(self, path, attrs, exists, ptype, device, mount):
        # The full path, normalized
        self.path = os.path.normpath(path)
        # lsattr type attributes
        self.attrs = attrs
        self.exists = exists
        # ie. dir or file
        self.ptype = ptype
        # A Device() instance
        self.device = device
        # A Mount() instance
        self.mount = mount

    def __str__(self):
        return ("{} {} {}, mounted on: {}, with device info:"
                " {}".format("Existent" if self.exists else "Nonexsitent",
                             self.ptype if self.ptype else '', self.path,
                             self.mount, self.device))

# ------------------------------------------------------------------------------
# Runner functions.
# ------------------------------------------------------------------------------

# Some fun output
BOLD = '\033[1m'
ENDC = '\033[0m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
RED = '\033[1;31m'
CEPH_STATEDIR = "/var/lib/ceph"


def _analyze_ceph_statedirs(statedirs):
    """
    Based on some elements of statedir, give the admin feedback regarding the
    ceph variable statedir.
    """
    local = salt.client.LocalClient()
    results = {'ok': [], 'to_create': [], 'to_migrate': [],
               'to_correct_cow': [], 'alt_fs': [], 'ceph_down': []}

    # pylint: disable=too-many-nested-blocks
    for minion, statedir in six.iteritems(statedirs):
        if statedir.device.fstype == 'btrfs':
            if statedir.exists:
                # OK, path exists, is there a subvolume mounted on it?
                # We detect this by checking the mountpoint
                if statedir.mount.mountpoint == statedir.path:
                    # subvol = statedir.mount.get_opt('subvol')
                    # Already a subvolume!  Check if CoW
                    if 'C' not in statedir.attrs:
                        results['to_correct_cow'].append(minion)
                    else:
                        # Copy on write disabled, all good!
                        results['ok'].append(minion)
                        # Also check to see if Ceph is running.
                        if not local.cmd(minion, 'cephprocesses.check', [],
                                         expre_form='compound')[minion]:
                            results['ceph_down'].append(minion)
                else:
                    # Path exists, but is not a subovlume
                    results['to_migrate'].append(minion)
            else:
                # Path does not yet exist.
                results['to_create'].append(minion)
        else:
            # Not btrfs.  Nothing to suggest.
            results['alt_fs'].append(minion)
            # Also check to see if Ceph is running
            if not local.cmd(minion, 'cephprocesses.check', [], expre_form='compound')[minion]:
                results['ceph_down'].append(minion)

    return results


def create_var(**kwargs):
    """
    Create /var/lib/ceph as a btrfs subvolume
    """
    local = salt.client.LocalClient()
    path = CEPH_STATEDIR
    ret = True

    statedirs = _inspect_ceph_statedir(path)
    results = _analyze_ceph_statedirs(statedirs)

    if not results['to_create']:
        print("{}No nodes marked for subvolume creation.{}".format(BOLD, ENDC))
        return True

    for _minion in results['to_create']:
        if ret:
            print("{}{}: Beginning creation...{}".format(BOLD, _minion, ENDC))
            for minion, ret in six.iteritems(local.cmd(_minion, 'fs.instantiate_btrfs_subvolume',
                                         ["path={}".format(path), "subvol=@{}".format(path)],
                                         tgt_type='compound')):
                if not ret:
                    print("{}{}: {}Failed to properly create and mount"
                           "@{} onto {}{}.  {}Check the local minion logs for "
                           "further details.{}".format(BOLD, minion, RED, path,
                                                       path, ENDC, BOLD, ENDC))
                else:
                    print("{}{}: {}Successfully created and mounted @{} onto "
                           "{}.{}".format(BOLD, minion, GREEN, path, path, ENDC))
                    ret = _correct_ceph_statedir_attrs(minion)

    if ret:
        print("{}Success.{}".format(GREEN, ENDC))
    else:
        print("{}Failure detected, not proceeding with further creations.{}".format(RED, ENDC))

    return ret


def migrate_var(**kwargs):
    """
    Drive the migration of /var/lib/ceph to a btrfs subvolume.  This needs to
    be done one node at a time.
    """
    local = salt.client.LocalClient()
    path = CEPH_STATEDIR
    ret = True

    statedirs = _inspect_ceph_statedir(path)
    results = _analyze_ceph_statedirs(statedirs)

    if not results['to_migrate']:
        print("{}No nodes marked for subvolume migration.{}".format(BOLD, ENDC))
        return True

    for _minion in results['to_migrate']:
        if ret:
            print("{}{}: Beginning migration...{}".format(BOLD, _minion, ENDC))
            for minion, ret in six.iteritems(local.cmd(_minion, 'fs.migrate_path_to_btrfs_subvolume',
                                         ["path={}".format(path), "subvol=@{}".format(path)],
                                         tgt_type='compound')):
                # Human intervention needed.
                if ret is None:
                    print("{}{}: {}Failure detected while migrating {} to "
                           "btrfs subvolume.  This failure is potentially "
                           "serious and will require manual intervention on "
                           "the node to determine the cause.  Please check "
                           "/var/log/salt/minion, the status of Ceph daemons "
                           "and the state of {}.  You may also run: "
                           "{}{}salt-run fs.inspect_var {}{}to check the "
                           "status.{}".format(BOLD, minion, RED, path, path,
                                              ENDC, BOLD, ENDC, RED, ENDC))
                elif ret is False:
                    print("{}{}: {}Failure detected while migrating {} to "
                           "btrfs subvolume.  We have failed to properly "
                           "migrate {}, however, we have hopefully recoveRED "
                           "to the previous state and Ceph should again be "
                           "running.  Please, however check "
                           "/var/log/salt/minion, the status of Ceph daemons "
                           "and the state of {} to confirm.  You may also run: "
                           "{}{}salt-run fs.inspect_var {}{}to check the "
                           "status.{}".format(BOLD, minion, YELLOW, path, path,
                                              path, ENDC, BOLD, ENDC, YELLOW,
                                              ENDC))
                else:
                    print("{}{}: {}Successfully migrated.{}".format(BOLD, minion, GREEN, ENDC))
                    ret = _correct_ceph_statedir_attrs(_minion)

    if ret:
        print("{}Success.{}".format(GREEN, ENDC))
    else:
        print("{}Failure detected, not proceeding with further migrations.{}".format(RED, ENDC))

    return ret


def _correct_ceph_statedir_attrs(minion=None):
    """
    Helper function to disable the copy-on-write attr on the ceph statedir.
    """
    local = salt.client.LocalClient()
    path = CEPH_STATEDIR
    attrs = "C"
    recursive = True
    ret = True

    if minion:
        # Omit /var/lib/ceph/osd directory, as underneath we may have OSDs mounted.
        for minion, rets in six.iteritems(local.cmd(minion, 'fs.add_attrs',
                                      ["path={}".format(path), "attrs={}".format(attrs),
                                       "rec={}".format(recursive), "omit={}/osd".format(path)],
                                      tgt_type='compound')):
            for _path, ret in six.iteritems(rets):
                if not ret:
                    print("{}{}: {}Failed to recursively disable "
                           "copy-on-write for {}.{}".format(BOLD, minion, RED,
                                                            _path, ENDC))
                    ret = False

        if ret:
            print("{}{}: {}Successfully disabled copy-on-write for {} and "
                   "it's contents.{}".format(BOLD, minion, GREEN, path, ENDC))

    return ret


def correct_var_attrs(**kwargs):
    """
    Recursively set No_COW (ie. disable copy-on-write) flag on /var/lib/ceph.
    """
    path = CEPH_STATEDIR
    ret = True

    all_btrfs_nodes = kwargs['all_btrfs_nodes'] if 'all_btrfs_nodes' in kwargs else False

    statedirs = _inspect_ceph_statedir(path)
    results = _analyze_ceph_statedirs(statedirs)

    if not all_btrfs_nodes and not results['to_correct_cow']:
        print("{}No nodes marked for copy-on-write correction.{}".format(BOLD, ENDC))
        return True

    # If all_btrfs_nodes == True, correct COW on all nodes regardless whether
    # they're in results['to_correct_cow'].
    # Only really useful if the admin manually set No_COW on /var/lib/ceph,
    # but didn't recursively set all files underneath.
    for minion, statedir in six.iteritems(statedirs):
        if not statedir.exists:
            print("{}{}: {} not found.{}".format(BOLD, minion, path, ENDC))

        if statedir.exists and statedir.device.fstype == 'btrfs':
            minion_to_correct = None
            if all_btrfs_nodes:
                minion_to_correct = minion
            else:
                minion_to_correct = minion if minion in results['to_correct_cow'] else None

            # Unlike the creation and migration functions, don't abort on first failure.
            if not _correct_ceph_statedir_attrs(minion_to_correct):
                ret = False

    if ret:
        print("{}Success.{}".format(GREEN, ENDC))
    else:
        print("{}Failure detected disabling copy-on-write for {}.{}".format(RED, path, ENDC))

    return ret


def _inspect_ceph_statedir(path):
    """
    Helper function that collects /var/lib/ceph information from all minions.

    Returns a dictionary of Path objects keyed on minion id.

    """
    target = DeepseaMinions()
    search = target.deepsea_minions
    local = salt.client.LocalClient()

    # A container of Path's keyed on minion id.
    statedirs = {}

    for minion, path_info in six.iteritems(local.cmd(search, 'fs.inspect_path',
                                       ["path={}".format(path)],
                                       tgt_type='compound')):
        statedirs[minion] = Path(path, path_info['attrs'], path_info['exists'],
                                 path_info['type'],
                                 Device(path_info['dev_info']['dev'],
                                 path_info['dev_info']['part_dev'],
                                 path_info['dev_info']['type'],
                                 path_info['dev_info']['uuid'],
                                 path_info['dev_info']['fstype']),
                                 Mount(path_info['mount_info']['mountpoint'],
                                 path_info['mount_info']['opts'])) if path_info['ret'] else None

    return statedirs


def inspect_var(**kwargs):
    """
    Collect /var/lib/ceph information from all minions.
    """
    path = CEPH_STATEDIR

    # Loud by default.
    quiet = kwargs['quiet'] if 'quiet' in kwargs else False

    statedirs = _inspect_ceph_statedir(path)
    results = _analyze_ceph_statedirs(statedirs)

    if not quiet:
        print("{}Inspecting Ceph Statedir ({})...{}".format(BOLD, path, ENDC))
        for minion, statedir in six.iteritems(statedirs):
            print("{}{}:{} {}".format(BOLD, minion, ENDC, statedir))
        print("")

    if not quiet:
        # Offer some suggestions.
        # Migration/Creation/COW adjustment.

        if results['ceph_down']:
            print("{}The following nodes have Ceph processes which are "
                   "currently down:{}".format(RED, ENDC))
            for minion in results['ceph_down']:
                print("{}".format(minion))
            print("{}Determine the nature of the failures before "
                   "proceeding.{}\n".format(RED, ENDC))

        if results['to_migrate']:
            print("{}For the following nodes using btrfs:{}".format(YELLOW, ENDC))
            for minion in results['to_migrate']:
                print("{}".format(minion))
            print("{}{} exists, but no btrfs subvolume is mounted.  "
                   "Run: {}{}salt-run fs.migrate_var{}{} to "
                   "migrate {} to the btrfs subvolume "
                   "@{}{}".format(YELLOW, path, ENDC, BOLD, ENDC, YELLOW, path,
                                  path, ENDC))
            print("{}You may then run: {}{}salt-run fs.inspect_var {}{}to "
                   "check the status.{}\n".format(YELLOW, ENDC, BOLD, ENDC,
                                                  YELLOW, ENDC))
        else:
            # print ("{}No nodes found needing migration of {} to btrfs "
            #        "subvolume @{}.{}\n".format(GREEN, path, path, ENDC))
            pass

        if results['to_create']:
            print("{}For the following nodes using btrfs:{}".format(YELLOW, ENDC))
            for minion in results['to_create']:
                print("{}".format(minion))
            print("{}{} does not yet exist.  "
                   "Run: {}{}salt-run fs.create_var{}{} to create and mount "
                   "the btrfs subvolume @{} onto {}.{}".format(YELLOW, path, ENDC, BOLD,
                                                               ENDC, YELLOW, path, path, ENDC))
            print("{}You may then run: {}{}salt-run fs.inspect_var {}{}to check the "
                   "status.{}\n".format(YELLOW, ENDC, BOLD, ENDC, YELLOW, ENDC))
        else:
            # Migration also creates subvolumes, so let's not confuse the admin.
            if not results['to_migrate']:
                # print ("{}No nodes found needing creation of {} as btrfs "
                #        "subvolume @{}.{}\n".format(GREEN, path, path, ENDC))
                pass

        if results['to_correct_cow']:
            print("{}For the following nodes using btrfs:{}".format(YELLOW, ENDC))
            for minion in results['to_correct_cow']:
                print("{}".format(minion))
            print("{}A btrfs subvolume is mounted on {}{}.  However, "
                   "copy-on-write is enabled.  Run: {}{}salt-run "
                   "fs.correct_var_attrs{}{} to disable "
                   "copy-on-write.".format(YELLOW, path, ENDC, BOLD, ENDC,
                                           YELLOW, ENDC))
            print("{}You may then run: {}{}salt-run fs.inspect_var {}{}to "
                   "check the status.{}\n".format(YELLOW, ENDC, BOLD, ENDC,
                                                  YELLOW, ENDC))
        else:
            # Migration also sets No_COW, so let's not confuse the admin.
            if not results['to_migrate']:
                print("{}No nodes found needing adjustment of copy-on-write "
                       "for {}.{}".format(GREEN, path, ENDC))
                print("{}NOTE: If copy-on-write was disabled manually for "
                       "{}, you may still want to run {}{}salt-run "
                       "fs.correct_var_attrs all_btrfs_nodes=True{}{} to "
                       "correct all relevant files contained within {} on all "
                       "nodes running btrfs.{}\n".format(YELLOW, path, ENDC,
                                                         BOLD, ENDC, YELLOW,
                                                         path, ENDC))

        if results['ok']:
            print("{}The following btrfs nodes have @{} correctly mounted on "
                   "{}, and do not require any subvolume "
                   "manipulation:{}".format(GREEN, path, path, ENDC))
            for minion in results['ok']:
                print("{}".format(minion))
            print("")

        if results['alt_fs']:
            print("{}The following nodes are not using btrfs, and hence no "
                   "action is needed:{}".format(GREEN, ENDC))
            for minion in results['alt_fs']:
                print("{}".format(minion))
            print("")

    return True


def help_():
    """
    Usage.
    """
    usage = ("""salt-run fs.inspect_var
                 Inspects /var/lib/ceph, provides mountpoint and device
                 information along with suggestions regarding migration of 
                 /var/lib/ceph to a btrfs subvolume if applicable.

             salt-run fs.create_var
                 Creates /var/lib/ceph (if not yet present) as a btrfs subvolume.

             salt-run fs.migrate_var
                 Migrates /var/lib/ceph to a btrfs subvolume (@/var/lib/ceph) if applicable.

             salt-run fs.correct_var_attrs [all_btrfs_nodes=True]
                 Disables copy-on-write for /var/lib/ceph on btrfs if applicable
             """)
    print(usage)
    return ""

__func_alias__ = {
                 'help_': 'help',
                 }
