# -*- coding: utf-8 -*-

"""
iSCSI execution module

This module allows to query information about iSCSI targets served by a gateway
"""
# pylint: disable=import-error,3rd-party-module-not-gated
# pylint: disable=too-many-nested-blocks,missing-docstring,invalid-name
from __future__ import absolute_import

import datetime
import glob
import json
import logging
import pprint
import socket
import time

import requests
from salt.exceptions import CommandExecutionError
import netaddr

try:
    from rtslib_fb.root import RTSRoot
except ModuleNotFoundError:
    RTSRoot = None
import rados

try:
    import netifaces
except ModuleNotFoundError:
    netifaces = None


__virtualname__ = 'iscsi'


log = logging.getLogger(__name__)


class RadosConn(object):
    def __init__(self, pool, client_name, namespace=None):
        self.pool = pool
        self.namespace = namespace
        self.rados = rados.Rados(conffile="/etc/ceph/ceph.conf",
                                 name=client_name)
        self.rados.connect()

    def object_exists(self, obj):
        with self.rados.open_ioctx(self.pool) as ioctx:
            if self.namespace:
                ioctx.set_namespace(self.namespace)
            try:
                ioctx.stat(obj)
            except rados.ObjectNotFound:
                return False
        return True

    def write(self, obj, content, xattrs=None):
        with self.rados.open_ioctx(self.pool) as ioctx:
            if self.namespace:
                ioctx.set_namespace(self.namespace)
            ioctx.write_full(obj, content)
            if xattrs is not None:
                for key, val in xattrs.items():
                    ioctx.set_xattr(obj, key, val)

    def read(self, obj):
        with self.rados.open_ioctx(self.pool) as ioctx:
            if self.namespace:
                ioctx.set_namespace(self.namespace)
            size, _ = ioctx.stat(obj)
            return ioctx.read(obj, length=size)

    def check_read_write_perms(self):
        with self.rados.open_ioctx(self.pool) as ioctx:
            if self.namespace:
                ioctx.set_namespace(self.namespace)
            obj_name = "test-obj-{}".format(__salt__['grains.get']('host'))
            ioctx.write(obj_name, b"hello world")
            content = ioctx.read(obj_name)
            ioctx.remove_object(obj_name)
        return content == b"hello world"

    def get_pool_id(self, pool):
        return self.rados.pool_lookup(pool)

    def close(self):
        self.rados.shutdown()


class CephCluster(object):

    config_name = 'gateway.conf'

    def __init__(self, pool_name):
        self.pool_name = pool_name
        client_name = "client.igw.{}".format(__salt__['grains.get']('host'))
        self.cluster = RadosConn(pool_name, client_name)

    def read_config(self):
        cfg_str = self.cluster.read(self.config_name)
        return json.loads(cfg_str)

    def write_config(self, config, epoch):
        self.cluster.write(self.config_name, config.encode('utf-8'),
                           {'epoch': str(epoch).encode('utf-8')})

    def get_pool_id(self, pool):
        return self.cluster.get_pool_id(pool)


class CephIscsiConfig(object):

    controls_defaults = {
        "block_size": 512,
        "emulate_3pc": 1,
        "emulate_caw": 1,
        "emulate_dpo": 1,
        "emulate_fua_read": 1,
        "emulate_fua_write": 1,
        "emulate_model_alias": 1,
        "emulate_pr": 1,
        "emulate_rest_reord": 0,
        "emulate_tas": 1,
        "emulate_tpu": 0,
        "emulate_tpws": 0,
        "emulate_ua_intlck_ctrl": 0,
        "emulate_write_cache": 0,
        "enforce_pr_isids": 1,
        "force_pr_aptpl": 0,
        "is_nonrot": 1,
        "max_unmap_block_desc_count": 1,
        "max_unmap_lba_count": 8192,
        "max_write_same_len": 65535,
        "optimal_sectors": 8192,
        "pi_prot_type": 0,
        "pi_prot_verify": 0,
        "queue_depth": 256,
        "unmap_granularity": 8192,
        "unmap_granularity_alignment": 0,
        "unmap_zeroes_data": 8192
    }

    target_controls_defaults = {
        "default_cmdsn_depth": 64,
        "default_erl": 0,
        "login_timeout": 15,
        "netif_timeout": 2,
        "prod_mode_write_protect": 0,
        "t10_pi": 0
    }

    errors = []

    def __init__(self, pool_name, ):
        self.pprinter = pprint.PrettyPrinter()
        self.cluster = CephCluster(pool_name)
        try:
            self.config = self.cluster.read_config()
            config_pretty = self.pprinter.pformat(self.config)
            log.info('Reading config:\n%s', config_pretty)
        except rados.ObjectNotFound:
            self.reset_config()

    def reset_config(self):
        now = CephIscsiConfig._get_time()
        self.config = {
            "disks": {},
            "gateways": {},
            "targets": {},
            "discovery_auth": {'username': '',
                               'password': '',
                               'password_encryption_enabled': False,
                               'mutual_username': '',
                               'mutual_password': '',
                               'mutual_password_encryption_enabled': False},
            "version": 9,
            "epoch": 0,
            "created": now,
            "updated": now
        }

    @staticmethod
    def _get_time():
        utc = datetime.datetime.utcnow()
        return utc.strftime('%Y/%m/%d %H:%M:%S')

    def add_target(self, target_iqn, acl_enabled, target_controls):
        log.debug('Adding target %s / %s', target_iqn, acl_enabled)
        now = CephIscsiConfig._get_time()
        if target_iqn not in self.config['targets']:
            self.config['targets'][target_iqn] = {
                'created': now,
                'disks': [],
                'acl_enabled': acl_enabled,
                'clients': {},
                'portals': {},
                'groups': {},
                'controls': target_controls
             }

    def _get_controls(self, pool, image):
        backstore_object_name = '{}-{}'.format(pool, image)
        glob_path = "{}/{}/{}".format('/sys/kernel/config/target',
                                      'core',
                                      'rbd_*/{}/attrib'.format(backstore_object_name))
        paths = glob.glob(glob_path)
        if not paths:
            self.errors.append('(Disk attribs not found) - Cannot find attribs at '
                               '{}'.format(glob_path))
        controls_overrides = {}
        for base in paths:
            for attr in self.controls_defaults:
                path = base + "/" + attr
                content = open(path).read().rstrip('\n')
                if attr in controls_overrides and controls_overrides[attr] != content:
                    self.errors.append(
                        '(Each attr must have the same value for all disks in the targets) - '
                        'Check attr {} on {}'.format(attr, path))
                if str(self.controls_defaults[attr]) != content:
                    if isinstance(content, int):
                        content = int(content)
                    controls_overrides[attr] = content
        return controls_overrides

    def get_target_controls(self, target_iqn):
        glob_path = "{}/{}/{}".format('/sys/kernel/config/target',
                                      'iscsi',
                                      '{}/tpgt_*/attrib'.format(target_iqn))
        paths = glob.glob(glob_path)
        if not paths:
            self.errors.append('(Target attribs not found) - Cannot find attribs at '
                               '{}'.format(glob_path))
        controls_overrides = {}
        for base in paths:
            for attr in self.target_controls_defaults:
                path = base + "/" + attr
                content = open(path).read().rstrip('\n')
                if attr in controls_overrides and controls_overrides[attr] != content:
                    self.errors.append(
                        '(Each attr must have the same value for all tpgs in the target) - '
                        'Check attr {} on {}'.format(attr, path))
                if str(self.target_controls_defaults[attr]) != content:
                    if isinstance(content, int):
                        content = int(content)
                    controls_overrides[attr] = content
        return controls_overrides

    def add_portal(self, target_iqn, portal_name, addr):
        log.debug('Adding portal %s / %s / %s', target_iqn, portal_name, addr)
        now = CephIscsiConfig._get_time()
        if portal_name not in self.config['gateways']:
            self.config['gateways'][portal_name] = {
                'active_luns': 0,
                'created': now
            }
        target_config = self.config['targets'][target_iqn]
        if 'ip_list' not in target_config:
            target_config['ip_list'] = []
        if portal_name not in target_config['portals']:
            target_config['portals'][portal_name] = {
                'created': now,
                'gateway_ip_list': [],
                'inactive_portal_ips': [],
                'portal_ip_addresses': [addr],
                'tpgs': 0
            }
        else:
            portal_config = target_config['portals'][portal_name]
            if addr not in portal_config['portal_ip_addresses']:
                portal_config['portal_ip_addresses'].append(addr)

        if addr not in target_config['ip_list']:
            target_config['ip_list'].append(addr)
        for _, portal_config in target_config['portals'].items():
            portal_config['gateway_ip_list'] = target_config['ip_list']
            inactive_portal_ips = list(portal_config['gateway_ip_list'])
            for portal_ip_address in portal_config['portal_ip_addresses']:
                inactive_portal_ips.remove(portal_ip_address)
            portal_config['inactive_portal_ips'] = inactive_portal_ips
            portal_config['tpgs'] = len(target_config['ip_list'])

    def _get_owner(self, target_iqn):
        target_config = self.config['targets'][target_iqn]
        owner = None
        for portal_name in target_config['portals'].keys():
            g_conf = self.config['gateways']
            if owner is None or g_conf[portal_name]['active_luns'] < g_conf[owner]['active_luns']:
                owner = portal_name
        return owner

    def add_disk(self, target_iqn, pool, image, wwn):
        log.debug('Adding disk %s / %s / %s / %s', target_iqn, pool, image, wwn)
        now = CephIscsiConfig._get_time()
        disk_id = '{}/{}'.format(pool, image)
        if disk_id in self.config['disks']:
            if disk_id not in self.config['targets'][target_iqn]['disks']:
                raise Exception("Disk {} cannot be exported by multiple targets".format(disk_id))
            return
        owner = self._get_owner(target_iqn)
        self.config['disks'][disk_id] = {
            'controls': self._get_controls(pool, image),
            'backstore': 'rbd',
            'backstore_object_name': '{}-{}'.format(pool, image),
            'created': now,
            'image': image,
            'owner': owner,
            'pool': pool,
            'pool_id': self.cluster.get_pool_id(pool),
            'wwn': wwn
        }
        self.config['targets'][target_iqn]['disks'].append(disk_id)
        self.config['gateways'][owner]['active_luns'] += 1

    def add_client(self, target_iqn, client_iqn):
        log.debug('Adding client %s / %s', target_iqn, client_iqn)
        target_config = self.config['targets'][target_iqn]
        target_config['clients'][client_iqn] = {
            'auth': {
                'username': '',
                'password': '',
                'password_encryption_enabled': False,
                'mutual_username': '',
                'mutual_password': '',
                'mutual_password_encryption_enabled': False
            },
            'luns': {},
            'group_name': ''
        }

    def add_client_auth(self, target_iqn, client_iqn, userid, password, userid_mutual,
                        password_mutual):
        log.debug('Adding client lun %s / %s / %s / %s / %s / %s', target_iqn,
                  client_iqn, userid, password, userid_mutual, password_mutual)
        client_config = self.config['targets'][target_iqn]['clients'][client_iqn]
        if userid and password:
            client_config['auth']['username'] = userid
            client_config['auth']['password'] = password
        if userid_mutual and password_mutual:
            client_config['auth']['mutual_username'] = userid_mutual
            client_config['auth']['mutual_password'] = password_mutual

    def add_client_lun(self, target_iqn, client_iqn, pool, image, lun_id):
        log.debug('Adding client lun %s / %s / %s / %s / %s', target_iqn, client_iqn,
                  pool, image, lun_id)
        client_config = self.config['targets'][target_iqn]['clients'][client_iqn]
        disk_id = '{}/{}'.format(pool, image)
        client_config['luns'][disk_id] = {
            'lun_id': lun_id
        }

    def add_discovery_auth(self, userid, password, userid_mutual, password_mutual):
        log.debug('Adding discovery auth %s / %s / %s / %s', userid, password,
                  userid_mutual, password_mutual)
        if userid and password:
            self.config['discovery_auth']['username'] = userid
            self.config['discovery_auth']['password'] = password
        if userid_mutual and password_mutual:
            self.config['discovery_auth']['mutual_username'] = userid_mutual
            self.config['discovery_auth']['mutual_password'] = password_mutual

    def get_tpgs(self, target_iqn):
        target_config = self.config['targets'][target_iqn]
        if 'ip_list' in target_config:
            return len(target_config['ip_list'])
        return 0

    def persist_config(self):
        config_pretty = self.pprinter.pformat(self.config)
        log.info('Writing config:\n%s', config_pretty)
        if self.errors:
            errors_str = ''
            for error in self.errors:
                errors_str += '\n    - {}'.format(error)
            raise Exception('ceph-iscsi config not persisted. Check the following errors:'
                            '{}'.format(errors_str))
        else:
            self.config['epoch'] = self.config['epoch'] + 1
            self.cluster.write_config(json.dumps(self.config), self.config['epoch'])


def _ip_addresses():
    ip_list = set()
    for iface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(iface):
            for link in netifaces.ifaddresses(iface)[netifaces.AF_INET]:
                ip_list.add(link['addr'])
        if netifaces.AF_INET6 in netifaces.ifaddresses(iface):
            for link in netifaces.ifaddresses(iface)[netifaces.AF_INET6]:
                if '%' in link['addr']:
                    continue
                ip_list.add(link['addr'])

    ip_list.discard('::1')
    ip_list.discard('127.0.0.1')

    return list(ip_list)


def _this_host():
    """
    return the local machine's shortname
    """
    return socket.getfqdn()


def _get_portal_name(addr):
    if addr in _ip_addresses():
        return _this_host()
    return None


def _is_acl_enabled(target):
    for tpg in target.tpgs:
        if tpg.get_attribute('generate_node_acls') == '0':
            return True
    return False


def validate(lio_root):
    """
    Checks if the existing LIO configuration is supported by ceph-iscsi
    """
    targets_by_disk = {}
    for target in lio_root.targets:
        for tpg in target.tpgs:
            for lun in tpg.luns:
                udev_path_list = lun.storage_object.udev_path.split('/')
                pool = udev_path_list[len(udev_path_list) - 2]
                image = udev_path_list[len(udev_path_list) - 1]
                disk_id = '{}/{}'.format(pool, image)
                if disk_id not in targets_by_disk:
                    targets_by_disk[disk_id] = []
                if target.wwn not in targets_by_disk[disk_id]:
                    targets_by_disk[disk_id].append(target.wwn)
                if len(targets_by_disk[disk_id]) > 1:
                    raise Exception(
                        'Unsupported LIO configuration: Disk {} belongs to more than one '
                        'target ({})'.format(disk_id, targets_by_disk[disk_id]))


def generate_config(lio_root, pool_name):
    """
    Reads from LIO and generates the corresponding gateway.conf
    """
    ceph_iscsi_config = CephIscsiConfig(pool_name)
    if _this_host() in ceph_iscsi_config.config['gateways']:
        return
    try:
        discovery_auth_path = '{}/{}/{}'.format('/sys/kernel/config/target',
                                                'iscsi',
                                                'discovery_auth')
        userid = open(discovery_auth_path + "/userid").read().rstrip('\n')
        userid = '' if userid == 'NULL' else userid
        password = open(discovery_auth_path + "/password").read().rstrip('\n')
        password = '' if password == 'NULL' else password
        userid_mutual = open(discovery_auth_path + "/userid_mutual").read().rstrip('\n')
        userid_mutual = '' if userid_mutual == 'NULL' else userid_mutual
        password_mutual = open(discovery_auth_path + "/password_mutual").read().rstrip('\n')
        password_mutual = '' if password_mutual == 'NULL' else password_mutual
        ceph_iscsi_config.add_discovery_auth(userid, password, userid_mutual, password_mutual)
        for target in lio_root.targets:
            acl_enabled = _is_acl_enabled(target)
            target_controls = ceph_iscsi_config.get_target_controls(target.wwn)
            ceph_iscsi_config.add_target(target.wwn, acl_enabled, target_controls)
            for tpg in target.tpgs:
                log.info('Processing tpg - %s', tpg)
                for network_portal in tpg.network_portals:
                    portal_name = _get_portal_name(network_portal.ip_address)
                    if portal_name:
                        ceph_iscsi_config.add_portal(target.wwn, portal_name,
                                                     network_portal.ip_address)
                if len(list(target.tpgs)) == ceph_iscsi_config.get_tpgs(target.wwn):
                    disks_by_lun = {}
                    for lun in tpg.luns:
                        udev_path_list = lun.storage_object.udev_path.split('/')
                        pool = udev_path_list[len(udev_path_list) - 2]
                        image = udev_path_list[len(udev_path_list) - 1]
                        disks_by_lun[lun.lun] = (pool, image)
                        ceph_iscsi_config.add_disk(target.wwn, pool, image, lun.storage_object.wwn)
                    for node_acl in tpg.node_acls:
                        ceph_iscsi_config.add_client(target.wwn, node_acl.node_wwn)
                        userid = node_acl.chap_userid
                        password = node_acl.chap_password
                        userid_mutual = node_acl.chap_mutual_userid
                        password_mutual = node_acl.chap_mutual_password
                        ceph_iscsi_config.add_client_auth(target.wwn, node_acl.node_wwn, userid,
                                                          password, userid_mutual, password_mutual)
                        for mapped_lun in node_acl.mapped_luns:
                            disk = disks_by_lun[mapped_lun.mapped_lun]
                            ceph_iscsi_config.add_client_lun(target.wwn, node_acl.node_wwn, disk[0],
                                                             disk[1], mapped_lun.mapped_lun)
        ceph_iscsi_config.persist_config()
    except Exception as ex:
        ceph_iscsi_config.reset_config()
        ceph_iscsi_config.persist_config()
        raise ex


def delete_disabled_acls(lio_root):
    """
    Lrbd creates acls on all tpgs, even the disabled ones, but ceph-iscsi
    will not manage those acls, so we delete all acls from disabled tpgs
    """
    for target in lio_root.targets:
        for tpg in target.tpgs:
            if not tpg.enable:
                for node_acl in tpg.node_acls:
                    log.info('Deleting %s from disabled tpg %s/%s',
                             node_acl.node_wwn, target.wwn, tpg)
                    node_acl.delete()


def migrate_gateway(pool_name):
    log.info("Migrating iSCSI gateway")
    lio_root = RTSRoot()
    validate(lio_root)
    generate_config(lio_root, pool_name)
    delete_disabled_acls(lio_root)
    log.info("Migration iSCSI gateway done")
    return True


def validate_rados_rw(rbd_pool):
    # verify cluster access (RW permission for RADOS objects)
    client_name = "client.igw.{}".format(__salt__['grains.get']('host'))
    log.info("Checking RADOS RW acces for client: %s", client_name)
    rados_conn = RadosConn(rbd_pool, client_name)
    if not rados_conn.check_read_write_perms():
        raise Exception("Failed to validate RADOS rw access")
    rados_conn.close()
    log.info("RADOS rw access is available in pool '%s'", rbd_pool)
    return True


def is_pkg_installed(pkg_name):
    # verify that lrbd is installed
    try:
        result = __salt__['pkg.info_installed'](pkg_name)
    except CommandExecutionError as ex:
        log.info("%s is not installed? %s", pkg_name, str(ex))
        if str(ex).startswith('package {} is not'.format(pkg_name)):
            __context__['retcode'] = 0
            return False

        return str(ex)
    log.info("Checking if %s is installed: %s", pkg_name, result)
    return isinstance(result, dict) and pkg_name in result


def wait_for_gateway():
    """
    This method waits for a ceph-iscsi gateway to be ready for accepting
    REST requests.
    The method runs an infinite loop that is only broken if a successful
    HTTP request is made, or we detect that the service is not running.

    We are assuming that if an error occurs when running the ceph-iscsi
    service it will kill the service process and thus we will detect it.
    Otherwise we should wait because applying an LIO configuration might
    take several minutes.
    """
    username = __pillar__.get('ceph_iscsi_username', 'admin')
    password = __pillar__.get('ceph_iscsi_password', 'admin')
    port = __pillar__.get('ceph_iscsi_port', '5000')
    ssl = __pillar__.get('ceph_iscsi_ssl', False)
    address = __salt__['public.address']()

    if netaddr.valid_ipv6(address) is True:
        address = "[{}]".format(address)

    url = "http{}://{}:{}@{}:{}/api/_ping" \
          .format("s" if ssl else "", username,
                  password, address, port)

    while True:
        try:
            if not __salt__['service.status']('rbd-target-api'):
                log.info("Gateway service is not running, stopped waiting")
                return False
            log.info("Checking gateway: GET %s", url)
            res = requests.get(url, verify=False, timeout=5)
            if res.status_code in [200, 503]:
                log.info("Gateway is now available")
                return True
        except requests.RequestException as ex:
            log.info("Gateway not yet available: %s", str(ex))
        time.sleep(5)


def __virtual__():
    """
    Salt module virtual function
    """
    return __virtualname__
