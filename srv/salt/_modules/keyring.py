# -*- coding: utf-8 -*-
"""
Keyring collection of operations
"""

from __future__ import absolute_import
import os
import struct
import base64
import time


def secret(filename):
    """
    Read the filename and return the key value.  If it does not exist,
    generate one.

    Note that if used on a file that contains multiple keys, this will
    always return the first key.
    """
    if os.path.exists(filename):
        with open(filename, 'r') as keyring:
            for line in keyring:
                if 'key' in line and ' = ' in line:
                    key = line.split(' = ')[1].strip()
                    return key

    return gen_secret()


def gen_secret():
    """
    Generate a valid keyring secret for Ceph
    """
    key = os.urandom(16)
    header = struct.pack('<hiih', 1, int(time.time()), 0, len(key))
    return base64.b64encode(header + key)


# pylint: disable=too-many-return-statements
def file_(component, name=None):
    """
    Return the pathname to the cache directory.  This feels cleaner than
    trying to use Jinja across different directories to retrieve a common
    value.
    """
    if component == "osd":
        return "/srv/salt/ceph/osd/cache/bootstrap.keyring"

    elif component == "igw":
        return "/srv/salt/ceph/igw/cache/ceph." +  name + ".keyring"

    elif component == "mds":
        return "/srv/salt/ceph/mds/cache/" + name + ".keyring"

    elif component == "mgr":
        return "/srv/salt/ceph/mgr/cache/" + name + ".keyring"

    elif component == "rgw":
        return "/srv/salt/ceph/rgw/cache/" + name + ".keyring"

    if component == "ganesha":
        return "/srv/salt/ceph/ganesha/cache/" + name + ".keyring"

    elif component == "deepsea_cephfs_bench":
        return "/srv/salt/ceph/cephfs/benchmarks/files/cache/deepsea_cephfs_bench.keyring"

    elif component == "deepsea_cephfs_bench_secret":
        return "/srv/salt/ceph/cephfs/benchmarks/files/cache/deepsea_cephfs_bench.secret"

    elif component == "deepsea_rbd_bench":
        return "/srv/salt/ceph/rbd/benchmarks/files/cache/deepsea_rbd_bench.keyring"

__func_alias__ = {
                 'file_': 'file',
                 }
