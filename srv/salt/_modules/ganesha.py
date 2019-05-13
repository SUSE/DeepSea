# -*- coding: utf-8 -*-

"""
Ganesha configuration and exports
"""
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
# pylint: disable=missing-docstring,no-name-in-module
from __future__ import absolute_import

import logging
import os
from grp import getgrgid
from pwd import getpwuid
import shutil
import rados


log = logging.getLogger(__name__)


def configurations():
    """
    Return the ganesha configurations.  The three answers are

    ganesha_configurations as defined in the pillar
    ganesha if defined
    [] for no ganesha
    """
    if 'roles' in __pillar__:
        if 'ganesha_configurations' in __pillar__:
            return list(set(__pillar__['ganesha_configurations']) &
                        set(__pillar__['roles']))
        if 'ganesha' in __pillar__['roles']:
            return ['ganesha']
    return []


class RadosConn(object):
    def __init__(self, pool, namespace):
        self.pool = pool
        self.namespace = namespace
        self.rados = rados.Rados(conffile="/etc/ceph/ceph.conf", name="client.admin")
        self.rados.connect()

    def object_exists(self, obj):
        with self.rados.open_ioctx(self.pool) as ioctx:
            ioctx.set_namespace(self.namespace)
            try:
                ioctx.stat(obj)
            except rados.ObjectNotFound:
                return False
        return True

    def write(self, obj, content):
        with self.rados.open_ioctx(self.pool) as ioctx:
            ioctx.set_namespace(self.namespace)
            ioctx.write(obj, content)

    def read(self, obj):
        with self.rados.open_ioctx(self.pool) as ioctx:
            ioctx.set_namespace(self.namespace)
            return ioctx.read(obj)

    def check_read_write_perms(self):
        with self.rados.open_ioctx(self.pool) as ioctx:
            ioctx.set_namespace(self.namespace)
            ioctx.write("test-obj", b"hello world")
            content = ioctx.read("test-obj")
            ioctx.remove_object("test-obj")
        return content == b"hello world"

    def close(self):
        self.rados.shutdown()


def validate_rados_rw(nfs_pool):
    # verify cluster access (RW permission for RADOS objects)
    rados_conn = RadosConn(nfs_pool, "ganesha")
    if not rados_conn.check_read_write_perms():
        raise Exception("Failed to validate RADOS rw access")
    rados_conn.close()
    log.info("RADOS rw access is available in pool '%s'", nfs_pool)
    return True


def validate_ganesha_daemon():
    # verify that nfs-ganesha gateways are still running
    result = __salt__['cmd.run']('systemctl is-active nfs-ganesha')
    log.info("Checking nfs-ganesha service: %s", result)
    if result != 'active':
        raise Exception("NFS-ganesha is not running")
    return True


def write_object(nfs_pool, obj_key, raw_config):
    rados_conn = RadosConn(nfs_pool, "ganesha")
    raw_config = raw_config.encode('utf-8')
    if rados_conn.object_exists(obj_key):
        if rados_conn.read(obj_key) == raw_config:
            # file exists but has the same content
            return True
        return False
    rados_conn.write(obj_key, raw_config)
    rados_conn.close()
    return True


def backup_config_file(source_file_path):
    dest_file_path = "{}.ses5.bak".format(source_file_path)
    if os.path.exists(dest_file_path):
        return False
    uid = getpwuid(os.stat(source_file_path).st_uid).pw_uid
    gid = getgrgid(os.stat(source_file_path).st_gid).gr_gid
    shutil.copy2(source_file_path, dest_file_path)
    os.chown(dest_file_path, uid, gid)
    return True
