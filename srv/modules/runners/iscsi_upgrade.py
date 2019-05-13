# -*- coding: utf-8 -*-
"""
iSCSI Upgrade script
"""
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
# pylint: disable=broad-except,too-many-return-statements,unused-argument
from __future__ import absolute_import

import logging
import yaml

import salt.client
import salt.config
import salt.loader


log = logging.getLogger(__name__)


def _check_if_migration_needed():
    """
    Checks if we need to run the upgrade from lrbd to ceph-iscsi
    """
    none_have_lrbd = True
    local = salt.client.LocalClient()
    result = local.cmd('I@roles:igw', 'iscsi.is_pkg_installed', ['lrbd'],
                       tgt_type="compound")
    if not result:
        __context__['retcode'] = 1
        return "Failed to check if lrbd is installed in IGW nodes"

    for minion, res in result.items():
        if isinstance(res, bool) and res:
            none_have_lrbd = False
        elif isinstance(res, str):
            __context__['retcode'] = 1
            return "Error while checking if lrbd is installed in {}\n{}" \
                   .format(minion, res)

    if none_have_lrbd:
        # migration is not needed
        return False

    return True


def validate():
    """
    Validates some pre-conditions necessary for the successful completion of
    the upgrade process.
    """
    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)

    needed = _check_if_migration_needed()
    if not isinstance(needed, bool):
        return needed
    if not needed:
        # skip migration
        return True

    rbd_pool = __salt__['master.find_pool']('rbd', 'iscsi-images')

    if not rbd_pool:
        __context__['retcode'] = 1
        return "Could not find any RBD pool"

    log.info("Checking RADOS rw access of '%s' pool in IGW nodes", rbd_pool)

    # verify cluster access (RW permission for RADOS objects)
    local = salt.client.LocalClient(mopts=__opts__)
    result = local.cmd('I@roles:igw', 'iscsi.validate_rados_rw', [rbd_pool],
                       tgt_type="compound")
    log.info("RADOS RW RESULT: %s", result)
    if not result:
        __context__['retcode'] = 1
        return "Failed to check RADOS RW access"
    for minion, res in result.items():
        if not isinstance(res, bool):
            __context__['retcode'] = 1
            return "Failed RADOS RW access in minion {}:\n{}" \
                   .format(minion, res)

    # validate rtslib-fb is installed
    result = local.cmd('I@roles:igw', 'iscsi.is_pkg_installed', ['python3-rtslib-fb'],
                       tgt_type="compound")
    if not result:
        __context__['retcode'] = 1
        return "Failed to check if rtslib-fb is installed"
    for minion, res in result.items():
        if not res:
            __context__['retcode'] = 1
            return "rstlib-fb is not installed in {}".format(minion)

    return True


def upgrade():
    """
    Upgrades IGW minions from lrbd to ceph-iscsi
    """
    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)
    local = salt.client.LocalClient(mopts=__opts__)

    needed = _check_if_migration_needed()
    if not isinstance(needed, bool):
        return needed
    if not needed:
        # skip migration
        return True

    # make sure netifaces is installed
    result = local.cmd('I@roles:igw', 'pkg.install', ['python3-netifaces'],
                       tgt_type="compound")
    if not result:
        __context__['retcode'] = 1
        return "Failed to install netifaces in IGW minions"

    # gather list of IGW minion
    minions = []
    result = local.cmd('I@roles:igw', 'test.ping', tgt_type="compound")
    if not result:
        __context__['retcode'] = 1
        return "Failed to ping IGW minions"

    minions = [m for m in result]
    if not minions:
        __context__['retcode'] = 1
        return "No IGW minions found"

    rbd_pool = __salt__['master.find_pool']('rbd', 'iscsi-images')

    if not rbd_pool:
        __context__['retcode'] = 1
        return "Could not find any RBD pool"

    # migrate lrbd configuration sequentially
    for minion in minions:
        log.info("Migrating iSCSI gateway: %s", minion)
        result = local.cmd(minion, 'iscsi.migrate_gateway', [rbd_pool])
        if not result:
            __context__['retcode'] = 1
            return "Failed to migrate iSCSI gateway {}".format(minion)
        if minion not in result:
            __context__['retcode'] = 1
            return "Migration of gateway {} failed".format(minion)
        elif not isinstance(result[minion], bool):
            __context__['retcode'] = 1
            return "Migration of gateway {} failed:\n{}".format(minion,
                                                                result[minion])
        log.info("Migration of iSCSI gateway successful: %s", minion)

    result = local.cmd('I@roles:igw', 'iscsi.is_pkg_installed', ['ceph-iscsi'],
                       tgt_type="compound")
    if not result:
        __context__['retcode'] = 1
        return "Failed to check if ceph-iscsi is installed in IGW nodes"

    set_grain_list = []
    for minion, res in result.items():
        if isinstance(res, bool) and not res:
            set_grain_list.append(minion)
        elif isinstance(res, str):
            __context__['retcode'] = 1
            return "Error while checking if ceph-iscsi is installed in {}\n{}" \
                   .format(minion, res)

    # set grains for cleaning lio configuration before ceph-iscsi service restarts
    for minion in set_grain_list:
        result = local.cmd(minion, "grains.set", ["igw_clean_lio", True])
        if not result:
            __context__['retcode'] = 1
            return "Failed to set restart grains."
        for _, res in result.items():
            if not isinstance(res, dict):
                __context__['retcode'] = 1
                return "Failed to set restart grain in {}:\n{}" \
                       .format(minion, res)

    # remove lrbd from IGW minions
    result = local.cmd('I@roles:igw', 'pkg.remove', ['lrbd'], tgt_type="compound")
    if not result:
        __context__['retcode'] = 1
        return "Failed to remove lrbd from IGW minions"
    for minion, res in result.items():
        if not isinstance(res, dict) or 'lrbd' not in res:
            __context__['retcode'] = 1
            return "Failed to remove lrbd from {}:\n{}".format(minion, res)

    return True


def set_igw_service_daemon():
    """
    Set igw_service_daemons pillar item with ceph-iscsi daemon
    """
    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)
    local = salt.client.LocalClient(mopts=__opts__)

    filename = '/srv/pillar/ceph/stack/ceph/cluster.yml'
    contents = {}
    with open(filename, 'r') as yml:
        contents = yaml.safe_load(yml)
        if not contents:
            contents = {}
        contents['igw_service_daemons'] = ['rbd-target-api']
        friendly_dumper = yaml.SafeDumper
        friendly_dumper.ignore_aliases = lambda self, data: True
        with open(filename, 'w') as yml:
            yml.write(yaml.dump(contents,
                                Dumper=friendly_dumper,
                                default_flow_style=False))

    # refresh pillar
    master = __salt__['master.minion']()
    local.cmd(master, 'saltutil.pillar_refresh')
    return True
