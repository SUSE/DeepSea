# -*- coding: utf-8 -*-
"""
Check btrfs subvolume
"""

from __future__ import absolute_import


def check():
    """
    Return bool and message about the subvolume state of /var/lib/ceph
    """
    btrfs, mounted = _btrfs()
    if mounted:
        return True, "/var/lib/ceph subvolume mounted"

    if not btrfs:
        return True, "/ is not btrfs"

    created = _subvol()

    if created:
        return False, "/var/lib/ceph not mounted"

    return False, "/var/lib/ceph subvolume missing"


def _btrfs():
    """
    Scan /proc/mounts. Return whether / is btrfs and /var/lib/ceph is mounted.
    """
    btrfs = False
    mounted = False
    with open('/proc/mounts') as mounts:
        for line in mounts:
            _device, path, fstype, options = line.split()[:4]
            if path == "/" and fstype == "btrfs":
                btrfs = True
            if path == "/var/lib/ceph" and "subvol" in options:
                mounted = True
    return btrfs, mounted


def _subvol():
    """
    Check if /var/lib/ceph subvolume exists
    """
    cmd = "btrfs subvolume list /"
    _rc, stdout, _stderr = __salt__['helper.run'](cmd)

    found = False
    for line in stdout:
        if line.endswith("/var/lib/ceph"):
            found = True
    return found


def device():
    """
    Print the device (i.e. first column) of the root filesystem for btrfs
    """
    with open('/etc/fstab') as fstab:
        for line in fstab:
            _device, path, fstype, _ = line.split()[:4]
            if path == "/" and fstype == "btrfs":
                return _device

    return ""
