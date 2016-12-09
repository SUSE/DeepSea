#!/usr/bin/python

import os
import struct
import base64
import time

def secret(filename):
    """
    Read the filename and return the key value.  If it does not exist,
    generate one.
    """
    if os.path.exists(filename):
        with open(filename, 'r') as keyring:
            for line in keyring:
                if 'key' in line and ' = ' in line:
                    key = line.split(' = ')[1].strip()
                    return key

    return gen_secret()

def gen_secret():
    key = os.urandom(16)
    header = struct.pack('<hiih',1,int(time.time()),0,len(key))
    return base64.b64encode(header + key)

def file(component, name=None):
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

    elif component == "rgw":
        return "/srv/salt/ceph/rgw/cache/" + name + ".keyring"

    elif component == "deepsea_cephfs_bench":
        return "/srv/salt/ceph/cephfs/benchmarks/files/cache/deepsea_cephfs_bench.keyring"

    elif component == "deepsea_cephfs_bench_secret":
        return "/srv/salt/ceph/cephfs/benchmarks/files/cache/deepsea_cephfs_bench.secret"
