# -*- coding: utf-8 -*-
# pylint: disable=fixme
"""
------------------------------------------------------------------------------
fs.py

Module for performing filesystem operations.

------------------------------------------------------------------------------
"""

from __future__ import absolute_import
import logging
import os
import tempfile
import shutil
import pprint
import uuid
import time
from subprocess import Popen, PIPE
# pylint: disable=import-error,3rd-party-module-not-gated
import psutil

log = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Utility functions.
# ------------------------------------------------------------------------------


def _run(cmd):
    """
    NOTE: Taken from osd.py module.
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
    # return proc.returncode, _stdout, _stderr
    return proc.returncode, _stdout, _stderr


def _systemctl_cmd_target(cmd, target):
    """
    Run a systemctl cmd on a target.  Returns True/False.
    """
    retries = 5
    delay = 2

    # TODO: warn that target is null?
    if not target:
        return False

    cmd = "systemctl {} {}".format(cmd, target)

    # Try a _few_ times, with a small sleep.
    _rc, _stdout, _stderr = _run(cmd)
    while retries and _rc != 0:
        _rc, _stdout, _stderr = _run(cmd)
        retries -= 1
        time.sleep(delay)

    if _rc != 0:
        log.error("Failed to {} target {}.".format(cmd, target))
        return False

    return True


def _systemctl_stop_target(target):
    """
    systemctl stop target.
    """
    return _systemctl_cmd_target('stop', target)


def _systemctl_start_target(target):
    """
    systemctl start target.
    """
    return _systemctl_cmd_target('start', target)


def _systemctl_restart_target(target):
    """
    systemctl restart target.
    """
    return _systemctl_cmd_target('restart', target)


def _teardown_ceph():
    """
    Kill Ceph and return the status obtained from _ceph_is_down()
    """
    # TODO: ganesha and others!?
    # NOTE: yes, this will trigger an error in the log for nodes that don't run
    # _all_ of these targets.
    for target in ['ceph-mon.target', 'ceph-osd.target', 'ceph-mds.target',
                   'ceph-radosgw.target', 'ceph-mgr.target', 'ceph.target']:
        _systemctl_stop_target(target)

    return _ceph_is_down()


def _startup_ceph():
    """
    Start Ceph, check status of Ceph processes, and return True/False
    """
    ret = _systemctl_start_target('ceph.target')

    # We 'succeeded'... but that doesn't mean Ceph isn't still running.
    if ret:
        # Let things settle.
        time.sleep(5)
        return _ceph_is_up()
    return False


def _ceph_is_down():
    """
    Queries whether all Ceph processes meant to be running on this node have been shut down.

    Returns True/False.
    """
    retries = 6
    delay = 2
    down = False
    # Processes that don't impede migration (httpd-prefork == openattic, rest are ganesha related).
    omit_list = ['httpd-prefork', 'ganesha.nfsd', 'rpcbind', 'rpc.statd']

    while retries and not down:
        running_procs = __salt__['cephprocesses.check'](results=True, quiet=True)['up'].keys()
        if not running_procs:
            down = True
        else:
            # Compute processes which are running, but not in the omit_list.
            waiting_for = [proc for proc in running_procs if proc not in omit_list]
            if not waiting_for:
                down = True
            else:
                log.warn(("Waiting for the following Ceph processes to stop: "
                          "{}.".format(waiting_for)))
                retries -= 1
                time.sleep(delay)
                delay *= 2

    return down


def _ceph_is_up():
    """
    Queries whether all Ceph processes meant to be running on this node are up.

    Returns True/False.
    """
    retries = 6
    delay = 2

    while retries and not __salt__['cephprocesses.check']():
        log.warn("Waiting for Ceph processes to start.")
        retries -= 1
        time.sleep(delay)
        delay *= 2

    return __salt__['cephprocesses.check']()


def _get_unique_path(path):
    """
    Tries to return a unique path, else None on error.
    """
    retries = 100
    tmp_path = "{}.{}".format(path, str(uuid.uuid4()))

    while os.path.exists(tmp_path) and retries:
        tmp_path = "{}.{}".format(path, str(uuid.uuid4()))
        retries -= 1

    # Couldn't find a unique path.
    if not retries and os.path.exists(tmp_path):
        return None

    return tmp_path


def _get_uid_gid(path):
    """
    For a given path, return {'uid': uid, 'gid': gid} or None if path does not exist.
    """
    if not os.path.exists(path):
        return None
    stats = os.stat(path)
    return {'uid': stats.st_uid, 'gid': stats.st_gid}


def _mv_contents(path, new_path):
    """
    Try to move the contents of path to tmp_path.  Return True/False.

    NOTE: Invoking `mv` as shutil.move() was not preserving ownership metadata.
    """
    for entry in os.listdir(path):
        cmd = "mv {}/{} {}".format(path, entry, new_path)
        _rc, _stdout, _stderr = _run(cmd)
        if _rc != 0:
            return False

    return True


# pylint: disable=too-many-return-statements
def _add_fstab_entry(_uuid, path, fstype, subvol):
    """
    Append entry to /etc/fstab if it does not already exist.

    Return True/False.
    """
    fstab_entries = None

    if not _uuid or not path or not fstype or not subvol:
        log.error("Refusing to modify /etc/fstab: Unable to form proper fstab entry.")
        return False

    entry = "UUID={} {} {} subvol={} 0 0".format(_uuid, path, fstype, subvol)

    try:
        with open('/etc/fstab', 'r') as _fstab:
            fstab_entries = [line.rstrip('\n') for line in _fstab]
    # pylint: disable=bare-except
    except:
        log.error("Failed to read /etc/fstab.")
        return False

    # Process entries.
    if entry in fstab_entries:
        log.warn("'{}' already exists in /etc/fstab".format(entry))
        return True
    if path in fstab_entries:
        log.error("Refusing to modify /etc/fstab: existing path entry for '{}' found.".format(path))
        return False
    elif subvol in fstab_entries:
        log.error(("Refusing to modify /etc/fstab: existing subvol entry for "
                   "'{}' found.".format(subvol)))
        return False

    # Append entry to /etc/fstab.
    try:
        with open('/etc/fstab', 'a') as _fstab:
            _fstab.write("{}\n".format(entry))
    # pylint: disable=bare-except
    except:
        log.error("Failed to append '{}' to /etc/fstab.".format(entry))
        return False

    log.warn("Successfully appended '{}' to /etc/fstab.".format(entry))
    return True

# ------------------------------------------------------------------------------
# BTRFS related functions.
#
# Note that there appears to be a python btrfs module, but does not appear to
# exist in OBS/IBS.
# ------------------------------------------------------------------------------


def _btrfs_path_as_subvol(path):
    """
    Returns '@' concatinated with path => @/foo/bar.
    """
    return "@{}".format(path)


# pylint: disable=unused-argument
def btrfs_get_mountpoints_of_subvol(subvol='', **kwargs):
    """
    Determine the list of mountpoints for a given subvol (of the form @/foo/bar).

    Returns a list of mountpoint(s), or an empty list.
    """
    mountpoints = []
    if not subvol:
        return []

    # Seems the easiest way to do this is to walk the disk partitions, extract the opts
    # string and see if subvol is present.  Remember the leading '/'.
    for part in psutil.disk_partitions():
        if "subvol=/{}".format(subvol) in part.opts:
            mountpoints.append(part.mountpoint)

    return mountpoints


# pylint: disable=unused-argument
def btrfs_get_default_subvol(path='', **kwargs):
    """
    Returns the default subvolume (in the form @/foo/bar) of a given path or None on error.
    """
    cmd = "btrfs subvolume get-default {}".format(path)
    _rc, _stdout, _stderr = _run(cmd)

    if _rc == 0 and _stdout:
        # _stdout example: ID 259 gen 35248 top level 258 path @/.snapshots/1/snapshot
        # Return only the subvol
        return _stdout.split()[-1]

    return None


# pylint: disable=unused-argument
def btrfs_subvol_exists(subvol='', **kwargs):
    """
    Determine if subvol, of the form @/foo/bar exists as a btrfs subvolume.  The
    subvolume need not be mounted.

    Returns True/False.  Returns False for empty subvolumes.
    """
    if not subvol:
        return False

    # If the subvol is mounted somewhere, it obviously exists.
    if btrfs_get_mountpoints_of_subvol(subvol):
        return True

    # If it isn't mounted, we have no idea the mountpoint to use in the below
    # list, so just default to /
    cmd = "btrfs subvolume list /"
    _rc, _stdout, _stderr = _run(cmd)

    if _rc == 0 and _stdout:
        subvols = _stdout.split('\n')
        for subvol in subvols:
            if subvol.endswith("path {}".format(subvol)):
                return True

    # Haven't found it.
    return False


def btrfs_create_subvol(subvol='', dev_info=None, **kwargs):
    """
    Create a btrfs subvolume for the given subvol.  Expected subvol to be of the
    form @/foo/bar.  dev_info is either passed (when called directly) or queried
    by stripping off the '@' from the subvol in order to query the path.

    Return True/False.
    """
    ret = True
    tmp_dir = None

    if not subvol:
        log.error("Unable to create subvolume '{}'.".format(subvol))
        return False

    # Check if subvol already exists.
    if btrfs_subvol_exists(subvol):
        log.warn("Subvolume '{}' already exists.".format(subvol))
        return True

    # If we didn't get dev_info (because we're being called directly from the command
    # line), we _assume_ that the subvol path will ultimately be mounted onto a matching
    # path, so _try_ to get the device information by converting subvol to it's corresponding
    # path (ie. by stripping the leading '@').
    if not dev_info:
        dev_info = get_device_info(get_mountpoint(subvol[1:]))

    if not dev_info:
        log.error(("Unable to create subvolume '{}': failed to get device "
                   "information for '{}'".format(subvol, subvol[1:])))
        return False

    if dev_info['fstype'] != 'btrfs':
        log.error(("Unable to create subvolume '{}': invalid filesystem type "
                  "({}).".format(subvol, dev_info['fstype'])))
        return False

    # Get the partition of the mountpoint of the path.
    part_path = "/dev/{}".format(dev_info['part_dev'])

    # Create a unique tmp directory.
    try:
        tmp_dir = tempfile.mkdtemp()
    # pylint: disable=bare-except
    except:
        log.error(("Unable to create subvolume '{}': failed to create "
                   "temporary directory.".format(subvol)))
        return False

    # Mount tmpdir.
    cmd = "mount -t btrfs -o subvolid=0 '{}' '{}'".format(part_path, tmp_dir)
    _rc, _stdout, _stderr = _run(cmd)
    if _rc != 0:
        log.error("Failed to mount '{}' with subvolid=0 on '{}'.".format(part_path, tmp_dir))
        ret = False

    if ret:
        # Create the subvol.
        cmd = "btrfs subvolume create '{}/{}'".format(tmp_dir, subvol)
        _rc, _stdout, _stderr = _run(cmd)
        if _rc != 0:
            log.error("Failed to create subvolume '{}' on '{}'.".format(subvol, part_path))
            ret = False

    # Cleanup tmp_dir.  Don't touch ret here, just log any errors.
    if os.path.exists(tmp_dir):
        cmd = "umount '{}'".format(tmp_dir)
        _rc, _stdout, _stderr = _run(cmd)
        if _rc != 0:
            log.error("Failed to unmount '{}'.".format(tmp_dir))
        try:
            shutil.rmtree(tmp_dir)
        # pylint: disable=bare-except
        except:
            log.error("Failed to remove '{}'.".format(tmp_dir))

    if not ret:
        # We failed somewhere, so take care of removing the subvolume, etc.
        # TODO: there is a bug with subvolume deletes
        # (https://bugzilla.opensuse.org/show_bug.cgi?id=957198)
        # so no more cleanup can be dont at this point.
        log.error("Failed to create subvolume '{}'.".format(subvol))
    else:
        log.warn("Successfully created subvolume '{}'.".format(subvol))

    return ret


def btrfs_mount_subvol(subvol='', path='', **kwargs):
    """
    Given a subvolume in the form "@/path/to/subvol", mount it atop of path.  If
    path does not exist, log an error and abort.  If path is already a mountpoint
    for for subvol, skip.  If path is a mountpoint for something other than path,
    abort.  Refuse to mount a subvol with a differing path (ie. refuse to mount
    @/var/lib/foo atop of /var/lib/bar).

    CAUTION: No checks are performed whether path contains existing data!
    NOTE: Does not touch /etc/fstab, for that, _add_fstab_entry().

    Returns True/False.
    """
    if not subvol or not path:
        log.error("Unable to mount subvolume '{}' onto '{}'.".format(subvol, path))
        return False

    # Grab the mount info for path.
    mount_info = get_mount_info(path)
    if not mount_info:
        log.error(("Unable to mount subvolume '{}' onto '{}': no mount "
                   "information obtained.".format(subvol, path)))
        return False

    # Grab device info to confirm this is a btrfs filesystem.
    dev_info = get_device_info(mount_info['mountpoint'])
    if not dev_info:
        log.error(("Unable to mount subvolume '{}' onto '{}': no filesystem "
                   "information obtained.".format(subvol, path)))
        return False
    if dev_info['fstype'] != 'btrfs':
        log.error("Unable to mount subvolume '{}' onto '{}': invalid filesystem type ({}).".format(
            subvol, path, dev_info['fstype']))
        return False

    # Subvol should exist!
    if not btrfs_subvol_exists(subvol):
        log.error(("Unable to mount subvolume '{}' onto '{}': '{}' does not "
                   "exist.".format(subvol, path, subvol)))
        return False

    # Path should exist!
    if not os.path.exists(path):
        log.error(("Unable to mount subvolume '{}' onto '{}': '{}' does not "
                   "exist.".format(subvol, path, path)))
        return False

    # Begin mounting process.

    # If path == mountpoint, then we already have a subvolume mounted on this path.
    if path == mount_info['mountpoint']:
        # our path is a mountpoint, run some basic checks
        if path in btrfs_get_mountpoints_of_subvol(subvol):
            log.warn(("Subvolume '{}' is already mounted onto "
                      "'{}'.".format(subvol, path)))
            return True
        else:
            # Another subvolume is mounted on path, output which
            log.error(("Unable to mount subvolume '{}' onto '{}': a different "
                       "subvolume ({}) is already "
                       "mounted.".format(subvol, path,
                                         _get_mount_opt('subvol',
                                                        mount_info['opts']))))
            return False
    else:
        # TODO: Should we prevent the same subvolume being mounted on multiple
        # different directories?  btrfs is happy to mount the same subvolume
        # onto multiple directories, so let's not limit  this behaviour.  If
        # needed, we can always check the current subvol of the path, and if
        # it isn't the default subvol (via btrfs_get_default_subvol()), we
        # could assume a subvol is already mounted and log an error/return
        # False.
        pass

    # Finally mount!
    cmd = "mount '/dev/{}' '{}' -t btrfs -o subvol={}".format(dev_info['part_dev'], path, subvol)
    _rc, _stdout, _stderr = _run(cmd)
    if _rc != 0:
        log.error(("Failed to mount subvolume '{}' onto '{}': stderr: "
                   "'{}'.".format(subvol, path, _stderr)))
        return False

    log.warn(("Successfully mounted subvolume '{}' onto "
              "'{}'.".format(subvol, path)))
    return True

# ------------------------------------------------------------------------------
# General FS related functions.
# ------------------------------------------------------------------------------


def _get_mount_opt(opt, mount_opts):
    """
    Search for the opt string argument in mount_opts (ie. mount_info['opts']).
    Entries within the mount_info['opts'] list are either strings, or single k:v
    dictionaries.

    Returns the opt (or it's value if it's a {k:v}) if found, otherwise None.
    """
    if not mount_opts:
        return None

    for _opt in mount_opts:
        if _opt == opt:
            return _opt
        if isinstance(_opt, dict) and opt in _opt:
            return _opt[opt]

    # Didn't find opt it.
    return None


def get_attrs(path='', **kwargs):
    """
    Obtains the raw output of `lsattr` on a given path.

    Returns the attrs string after having stripped off the path, or None on error
    or if path is empty.  If path is a directory, it does not recursively follow
    all child paths.

    # TODO: Any use in adding a recursive flag and dumping output into a list?
    """
    # TODO: Should we warn if the path doesn't exist, or quietly return None?
    if not os.path.exists(path):
        return None

    cmd = ("lsattr -d {}".format(path) if os.path.isdir(path)
           else "lsattr {}".format(path))
    _rc, _stdout, _stderr = _run(cmd)

    if _rc == 0 and _stdout:
        return _stdout.split()[0]
    else:
        log.error("Failed to determine attrs for '{}': stderr: '{}'".format(path, _stderr))
        return None


# pylint: disable=invalid-name
def _rchattr(op, path, attrs, rec, omit, rets):
    """
    Yet another helper for the whole chattr story.  Recursively applies op and
    attrs to paths which are not present in the omit list.

    Returns a dictionary of { path: True/False, ... } entries representing the
    succesful/not successful application of op and attrs.
    """
    # Basic non recursive case.  Set attrs for a given path, if it's not in the omit list.
    if not rec:
        if path not in omit:
            cmd = "chattr {} {}{} {}".format('-d' if os.path.isdir(path) else '', op, attrs, path)
            _rc, _stdout, _stderr = _run(cmd)
            rets[path] = _rc == 0
            return _rc == 0
        else:
            log.warn(("Refusing to apply '{}' attrs to '{}' which is also in"
                      "the omit list {}.".format(attrs, path, omit)))
            rets[path] = False
            return False
    # The fun case.
    else:
        # If our path is a directory, compute it's contents in an absolute form.
        if os.path.isdir(path):
            path_contents = ["{}/{}".format(path, e) for e in os.listdir(path)]
            # Leaf directory with no contents, and not to be omitted.
            if not path_contents and path not in omit:
                dir_opt = '-d' if os.path.isdir(path) else ''
                cmd = "chattr {} {}{} {}".format(dir_opt, op, attrs, path)
                _rc, _stdout, _stderr = _run(cmd)
                rets[path] = _rc == 0
            # There are paths present in path_contents, process those.
            else:
                # For each path that is not in the omit list, recurse.
                for _pathname in path_contents:
                    if _pathname not in omit:
                        _rchattr(op, _pathname, attrs, rec, omit, rets)
                # Now process our non-leaf directory.
                # TODO: I have a feeling we should check this after the isdir()
                # and not process it or it's children.
                if path not in omit:
                    # Finally add the path
                    dir_opt = '-d' if os.path.isdir(path) else ''
                    cmd = "chattr {} {}{} {}".format(dir_opt, op, attrs, path)
                    _rc, _stdout, _stderr = _run(cmd)
                    rets[path] = _rc == 0
        # Path is a file.
        else:
            if path not in omit:
                dir_opt = '-d' if os.path.isdir(path) else ''
                cmd = "chattr {} {}{} {}".format(dir_opt, op, attrs, path)
                _rc, _stdout, _stderr = _run(cmd)
                rets[path] = _rc == 0


# pylint: disable=invalid-name
def _chattr(op, path, attrs, rec, omit):
    """
    {add,remove,set}_attrs helper function.  op should be one of '+', '-', or '=' per `man chatter`.
    Ultimately invokes the recursive _rchatter and collects results.
    """
    supported_ops = {'-': 'remove', '+': 'add', '=': 'set'}
    rets = {}

    # Convert omit string to list.
    omit = omit.split(',') if omit else []

    # Verify op.
    if op not in supported_ops.keys():
        log.error(("Unable to manipulate attrs for '{}': unsuppurted chattr op:"
                   "{}.".format(path, op)))
        rets[path] = False
        return rets

    # Hopefully it's obvious why we're unable to proceed.  Maybe an error is a bit much.
    if not path or not attrs:
        log.error("Unable to {} attrs '{}' for path '{}'.".format(supported_ops[op], attrs, path))
        rets[path] = False
        return rets

    # Make sure path exists.
    if not os.path.exists(path):
        log.error("Unable to {} attrs '{}' for '{}': '{}' does not exist.".format(
            supported_ops[op], attrs, path, path))
        rets[path] = False
        return rets

    _rchattr(op, path, attrs, rec, omit, rets)
    return rets


def add_attrs(path='', attrs='', rec=False, omit='', **kwargs):
    """
    Add attrs to existing attrs for path.  If path is a directory, and rec is True, will attempt
    to add attrs recursively to path and it's contents.  Omits paths found in omit.

    attrs should be a string of attributes to add.  For example, "CA" would add attributes
    'C' and 'A' to path.  Please refer to `man chattr` for valid attrs.

    Returns a dictionary (see _rchattr).
    """
    rets = _chattr('+', path, attrs, rec, omit)
    return rets


def remove_attrs(path='', attrs='', rec=False, omit='', **kwargs):
    """
    Remove attrs from existing attrs for path.  If path is a directory, and
    rec is True, will attempt to remove attrs recursively from path and it's
    contents.  Omits paths found in omit.

    attrs should be a string of attributes to remove.  For example, "CA" would
    remove attributes 'C' and 'A' from path.  Please refer to `man chattr` for
    valid attrs.

    Returns a dictionary (see _rchattr).
    """
    rets = _chattr('-', path, attrs, rec, omit)
    return rets


def set_attrs(path='', attrs='', rec=False, omit='', **kwargs):
    """
    Set attrs for path.  If path is a directory, and rec is True, will attempt
    to set attrs recursively for path and it's contents.  Omits paths found in
    omit.

    attrs should be a string of attributes to set.  For example, "CA" would
    set attributes 'C' and 'A' for path.  Please refer to `man chattr` for
    valid attrs.

    Returns a dictionary (see _rchattr).
    """
    rets = _chattr('=', path, attrs, rec, omit)
    return rets


def get_mountpoint_opts(mountpoint='', **kwargs):
    """
    Determine the mount options set for a given mountpoint.

    Returns a list of mount opts or None on error.  For opts in the form 'key=val',
    convert the opt into dictionary.  Thus, our return structure may look
    something like:
      [ 'rw', 'relatime', ..., { 'subvolid': '259' }, ... ]'
    """
    opts = None

    for part in psutil.disk_partitions():
        if part.mountpoint == mountpoint:
            opts = part.opts.split(',')

    # Convert foo=bar to dictionary entries if opts is not None or not an empty list.
    opts = [o if '=' not in o else {k: v for (k, v) in [tuple(o.split('='))]}
            for o in opts] if opts else None

    if not opts:
        log.error("Failed to determine mount opts for '{}'.".format(mountpoint))

    return opts


def _get_mountpoint(path):
    """
    Check if path is a mount point.  If not, split the path until either a mount
    point is found, or path is empty.  Returns a mount point path or None.
    """
    if not path or os.path.ismount(path):
        return path

    return _get_mountpoint(os.path.split(path)[0])


def get_mountpoint(path='', **kwargs):
    """
    Recursively finds the mount point for a given path.  If a path does not exist,
    returns the mount point of the path _if_ it were to be created.

    Returns the mount point or an empty path if mount point was not found.

    For cases where, for example, path=="var", we make no special assumptions
    about the parent, nor do we take an abspath().  This example would simply
    return ''.
    """
    mountpoint = _get_mountpoint(path)
    if not mountpoint:
        log.error("Failed to determine mountpoint of '{}'.".format(path))

    return mountpoint


def get_mount_info(path='', **kwargs):
    """
    Determine the mount point and mount options for a given path.

    Returns { 'mountpoint': String, 'opts': [ String | {k:v} ] } or None on error.
      - 'opts' may contain a { 'subvol': String } list entry indicating the btrfs
        subvolume mounted atop the 'mount_point'.

    TODO: Should a lack of mountpoint opts trigger a None return and error?
    """
    mount_info = {'mountpoint': '', 'opts': []}

    mountpoint = get_mountpoint(path)
    if not mountpoint:
        log.error("Failed to obtain mount information for '{}'.".format(path))
        return None
    mount_info['mountpoint'] = mountpoint

    opts = get_mountpoint_opts(mountpoint)
    if not opts:
        log.error("Failed to obtain mount information for '{}'.".format(path))
        return None
    mount_info['opts'] = opts

    return mount_info


def get_uuid(dev_path='', **kwargs):
    """
    Determine the UUID of a given dev_path (ie. /dev/sdb2).

    Returns the UUID of dev, or None on error.

    NOTE: Simplified form of original found in osd.py
    """
    pathname = "/dev/disk/by-uuid"

    cmd = "find -L {} -samefile {}".format(pathname, dev_path)
    _rc, _stdout, _stderr = _run(cmd)

    if _rc == 0 and _stdout:
        return os.path.basename(_stdout)
    else:
        log.error("Failed to determine uuid of '{}'.".format(dev_path))
        return None


def get_device_info(mountpoint='', **kwargs):
    """
    Determine the device, uuid, type and fs type for a given mountpoint.

    Returns { 'dev': String, 'part_dev': String, 'uuid': String,
              'type': String (ssd|hd|unknown),
              'fstype': String (btrfs|xfs|extX|unknown) }
    or None on error.
    """
    dev_info = {'dev': None, 'part_dev': None, 'uuid': None, 'type': None, 'fstype': None}
    dev_path = None
    dev = None
    part_dev = None
    fstype = None

    if not mountpoint:
        log.error("Unable to determine the device of mountponit '{}'.".format(mountpoint))
        return None

    # Grab device path and fs type in one shot.
    for part in psutil.disk_partitions():
        if part.mountpoint == mountpoint:
            dev_path = part.device
            fstype = part.fstype

    if not dev_path:
        log.error("Failed to determine the device of mountpoint '{}'.".format(mountpoint))
        return None

    part_dev = os.path.basename(dev_path)

    # From part_dev (ie. sdb2), grab the underlying device
    dev = part_dev.rstrip("1234567890")
    # For nvme, strip the trailing 'p' as well.
    if "nvme" in dev:
        dev = dev[:-1]

    dev_info['part_dev'] = part_dev
    dev_info['dev'] = dev

    if not fstype:
        log.error("Failed to determine the filesystem type of mountpoint '{}'.".format(mountpoint))
        return None
    dev_info['fstype'] = fstype

    # Check if we're on an SSD or not.
    try:
        with open("/sys/block/{}/queue/rotational".format(dev), 'r') as _file:
            line = _file.readline().rstrip()
            if line == '0':
                dev_info['type'] = 'ssd'
            elif line == '1':
                dev_info['type'] = 'hd'
            else:
                dev_info['type'] = 'unknown'
    # pylint: disable=bare-except
    except:
        # For some reason, the file doesn't exist or we can't open it.
        log.error("Failed to determine if '{}' is a solid state device.".format(dev_path))
        return None

    _uuid = get_uuid(dev_path)
    if not _uuid:
        return None
    dev_info['uuid'] = _uuid

    return dev_info

# ------------------------------------------------------------------------------
# Driver functions.
# ------------------------------------------------------------------------------


def instantiate_btrfs_subvolume(subvol='', path='', **kwargs):
    """
    Drive creation and mounting of btrfs subvolumes. Expects subvol in the form @/foo/bar.

    Returns True/False.
    """
    uid_gid = None

    if not path or not subvol:
        log.error("Unable to create subvolume '{}' and mount onto '{}'.".format(subvol, path))
        return False

    # Grab device info to confirm this is a btrfs filesystem.
    dev_info = get_device_info(get_mountpoint(path))
    if not dev_info:
        log.error("Unable to create subvolume '{}' without filesystem information.".format(subvol))
        return False
    if dev_info['fstype'] != 'btrfs':
        log.error("Unable to create subvolume on '{}' filesystem.".format(dev_info['fstype']))
        return False

    # Logs error already.
    ret = btrfs_create_subvol(subvol, dev_info)

    # Create the mount path if it does not yet exist.  If it does, grab it's
    # uid and gid so we can set it back after mount (root:root otherwise).
    if ret:
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            # pylint: disable=bare-except
            except:
                log.error("Failed to create '{}' for mounting of '{}'.".format(path, subvol))
                return False
        else:
            uid_gid = _get_uid_gid(path)

    # Try to mount the subvolume.
    ret = btrfs_mount_subvol(subvol, path)

    if ret and uid_gid:
        # Make sure path has correct uid/gid.
        try:
            os.chown(path, uid_gid['uid'], uid_gid['gid'])
        # pylint: disable=bare-except
        except:
            log.error(("Failed to set {}:{} ownership of existing '{}' after"
                       "mounting subvolume '{}'.".format(uid_gid['uid'],
                                                         uid_gid['gid'],
                                                         path, subvol)))
            # NOTE: I'd rather proceed with /etc/fstab in spite of this
            # failure, not setting ret to False.

    if ret:
        # Create an /etc/fstab entry as well, so mount survives reboots.  Logs
        # it's own errors.
        ret = _add_fstab_entry(dev_info['uuid'], path, dev_info['fstype'], subvol)

    return ret


def _unmount_osd(osd_mountpoint):
    """
    Unmount the OSD defined by osd_mountpoint.  Returns True/False.
    """
    _rc = 0
    if get_mountpoint(osd_mountpoint) == osd_mountpoint:
        cmd = "umount {}".format(osd_mountpoint)
        _rc, _stdout, _stderr = _run(cmd)

    return _rc == 0


def _mount_osd(osd_dev, osd_mountpoint):
    """
    Activate the OSD defined by osd_dev.  Returns True/False
    """
    _rc = 0
    if get_mountpoint(osd_mountpoint) != osd_mountpoint:
        cmd = "mount {} {}".format(osd_dev, osd_mountpoint)
        _rc, _stdout, _stderr = _run(cmd)

    return _rc == 0


def migrate_path_to_btrfs_subvolume(path='', subvol='', **kwargs):
    """
    Migrate an existing path to a btrfs subvolume.  This should be done one
    node at a time (controlled from the fs runner), as Ceph services need to
    be stopped and OSD's unmounted.

    Returns True/False or None.  None indicates a servere, unrecoverable error.
    """
    ret = True

    if not path or not subvol:
        log.error("Unable to migrate path '{}' to subvolume '{}'.".format(path, subvol))
        return False

    # If path doesn't exist, there's nothing to migrate.
    if not os.path.exists(path):
        log.error(("Unable to migrate '{}' to subvolume '{}': '{}' does not "
                   "exist.".format(path, subvol, path)))
        return False

    # Inspect the path, we could do this piecewise.
    # TODO: The ret check is a bit harsh.  We could also check the specific
    # parts of path_info.
    path_info = inspect_path(path)
    if not path_info or not path_info['ret']:
        log.error(("Unable to migrate '{}' to subvolume '{}': unable to obtain "
                   "path information.".format(path, subvol)))
        return False

    # Let's make sure (paranoia) that fstype is correct.
    if path_info['dev_info']['fstype'] != 'btrfs':
        log.error("Unable to migrate '{}' to subvolume '{}': invalid filesystem type ({}).".format(
            path, subvol, path_info['dev_info']['fstype']))
        return False

    # Check if path is already a mount point.  For a btrfs path to be a
    # mountpoint implies that a subvolume is mounted.
    if path_info['mount_info']['mountpoint'] == path:
        # Check if subvol matches the mounted subvol... this mainly for
        # thoroughness and information.
        # Remember to strip off the leading '/' when getting the subvol opt.
        subvol_opt = _get_mount_opt('subvol', path_info['mount_info']['opts'])[1:]
        if subvol == subvol_opt:
            log.warn(("No need to migrate '{}': '{}' is already a mountpoint "
                      "for subvolume '{}'.".format(path, path, subvol)))
            return True
        else:
            log.error("Unable to migrate '{}' to subvolume '{}': a different subvolume ({}) "
                      "is mounted.".format(path, subvol, subvol_opt))
            return False

    # At this point, we've determined that path is not a mount point for the
    # requested subvol.  Check if path is empty.  If it is, we don't really
    # need to do a full migration.
    # TODO: possible race if a rogue issues zypper install ceph...
    if not os.listdir(path):
        log.warn(("No need to migrate empty '{}'. Creating '{}' to be mounted "
                  "onto '{}'.".format(path, subvol, path)))
        return instantiate_btrfs_subvolume(subvol, path)

    # path is not empty, thus begin with migration...

    # Determine a unique tmp path.
    tmp_path = _get_unique_path(path)
    if not tmp_path:
        log.error(("Unable to migrate '{}' to subvolume '{}': failed to obtain "
                   "unique temporary path.".format(path, subvol)))
        return False

    # Try to create tmp_path.
    try:
        os.mkdir(tmp_path)
    # pylint: disable=bare-except
    except:
        log.error(("Unable to migrate '{}' to subvolume '{}': failed to create "
                   "'{}'.".format(path, subvol, tmp_path)))
        return False

    # Grab uid/gid of path.
    uid_gid = _get_uid_gid(path)

    # From here, some intelligent recovery/cleanup may be needed.

    # Grab osd device pairs needed for unmounting and re-activating.
    osd_pairs = __salt__['osd.part_pairs']()

    # Stop all Ceph processes on this node.  If unable to stop Ceph, we can't
    # proceed and bail out.  Note that just because systemctl call succeeded,
    # doesn't mean the services have actually been stopped, hence the additional
    # check.
    if not _teardown_ceph():
        log.error(("Unable to migrate '{}' to subvolume '{}': unable to stop "
                   "Ceph daemons.".format(path, subvol)))
        ret = False

    # Unmount all OSDs on this node.  If we fail to do so, we can't proceed
    # further.  Cleanup will remount OSDs and restart Ceph.
    if ret:
        for osd_pair in osd_pairs:
            if ret:
                if not _unmount_osd(osd_pair[1]):
                    log.error(("Unable to migrate '{}' to subvolume '{}': "
                               "failed to unmount OSD at '{}'"
                               ".".format(path, subvol, osd_pair[1])))
                    ret = False

    if ret:
        # Try to move contents of path to tmp_path.
        if not _mv_contents(path, tmp_path):
            log.error(("Unable to migrate '{}' to subvolume '{}': failed to "
                       "move contents of '{}' to '{}'"
                       ".".format(path, subvol, path, tmp_path)))
            ret = False

    if ret:
        # Try to create and mount the subvolume (including modifying /etc/fstab).
        if not instantiate_btrfs_subvolume(subvol, path):
            # Failed to have instiated btrfs subvol, either:
            #   i. Failed to have created subvol
            #   ii. Failed to have mounted subvol onto path
            #   iii. Failed to have modified /etc/fstab
            if not btrfs_subvol_exists(subvol) or btrfs_get_mountpoints_of_subvol(subvol) != path:
                log.error("Unable to migrate '{}' to subvolume '{}': failed "
                          "to create/mount '{}'.".format(path, subvol, subvol))
                ret = False
            else:
                # We created/mounted the subvolume, but just couldn't write
                # /etc/fstab.  This is so close, and while if we reboot this
                # node, subvol will no longer be mounted on path, we hope the
                # admin will be able to resolve this on seeing the error log.
                log.error(("Migration of '{}' to subvolume '{}' succeeded, but "
                           "/etc/fstab could not be written. "
                           "Manual intervention needed.".format(path, subvol)))
                ret = False

    # Cleanup...

    # Make sure path has correct uid/gid.
    try:
        os.chown(path, uid_gid['uid'], uid_gid['gid'])
    # pylint: disable=bare-except
    except:
        log.error("Failed to set {}:{} ownership of '{}' after migration to subvolume '{}'.".format(
            uid_gid['uid'], uid_gid['gid'], path, subvol))
        # Not worth an abrupt failure at this point, but do log it and alert at the runner.
        ret = False

    # Move contents of tmp_path back to path, if tmp_path is not empty.  If
    # it's empty, we failed to move contents of path.
    if os.listdir(tmp_path) and not _mv_contents(tmp_path, path):
        # Unrecoverable, don't delete either paths as we may lose data.
        # Return immediately with None indicating manual intervention.
        log.error(("Unable to migrate '{}' to subvolume '{}': failed to "
                   "move contents of '{}' back to path '{}'. Manual "
                   "intervention needed!".format(path, subvol, tmp_path, path)))
        return None

    # At this point, it's safe to remove tmp_path.
    try:
        os.rmdir(tmp_path)
    # pylint: disable=bare-except
    except:
        # shutil.move() would have failed above if we failed to move
        # everything from tmp_path to path, treating this as a cleanup error.
        log.error(("Failed to cleanup from migration of '{}' to subvolume "
                   "'{}': failed to remove '{}'".format(path, subvol, tmp_path)))

    # Try to remount as many OSDs as possible.  If we fail on any one, return
    # None at the end.
    mount_ret = True
    for osd_pair in osd_pairs:
        if not _mount_osd(osd_pair[0], osd_pair[1]):
            log.error(("Failed to re-mount OSD onto '{}' after migration of "
                       "'{}' to subvolume '{}'.  Manual intervention "
                       "needed!".format(osd_pair[1], path, subvol)))
            mount_ret = False
    if not mount_ret:
        return None

    # Finally, restart Ceph
    if not _startup_ceph():
        log.error("Failed to restart Ceph after migration of '{}' to subvolume '{}'.  "
                  "Manual intervention needed".format(path, subvol))
        return None

    if not ret:
        log.error("Failed to successfully migrate '{}' to subvolume '{}'.".format(path, subvol))
    else:
        log.warn("Succesfully migrated '{}' to subvolume '{}'.".format(path, subvol))

    return ret


def inspect_path(path='', **kwargs):
    """
    Determine some intersting information for a given path.

    Returns { 'ret': Bool, 'exists': exists(path), 'type': String ('directory', 'file'),
              'attrs': get_attrs(path),
              'mount_info': { get_mount_info(path) },
              'dev_info': { get_device_info(mountpoint) }
    or None if path not supplied.  On an error return from any of the composite
    functions, set 'ret' = False.
    """
    path_info = {'ret': True, 'exists': None, 'type': None, 'attrs': None,
                 'mount_info': None, 'dev_info': None}

    if not path:
        log.error("Unable to inspect '{}'.".format(path))
        return None

    path_info['exists'] = os.path.exists(path)

    # Keeping it simple: 'directory' or 'file'.  If it doesn't exist, None.
    if path_info['exists']:
        path_info['type'] = 'directory' if os.path.isdir(path) else 'file'

    path_info['attrs'] = get_attrs(path)
    if path_info['exists'] and not path_info['attrs']:
        # Only set a fail flag when collecting attrs for existing paths.
        path_info['ret'] = False

    path_info = get_mount_info(path)
    if not path_info['mount_info']:
        path_info['ret'] = False

    path_info['dev_info'] = get_device_info(path_info['mount_info']['mountpoint'])
    if not path_info['dev_info']:
        path_info['ret'] = False

    return path_info
