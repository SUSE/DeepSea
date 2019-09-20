# -*- coding: utf-8 -*-
"""
NFS-Ganesha helper functions
"""
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
# pylint: disable=broad-except,too-many-return-statements,unused-argument
from __future__ import absolute_import

import salt.client
import salt.config
import salt.loader


def report():
    """
    Returns information about current nfs-ganesha configuration
        - Gateways
        - Exports
    """
    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)

    runner = salt.runner.RunnerClient(__opts__)
    local = salt.client.LocalClient()

    minions = runner.cmd('select.minions', ['cluster=ceph', 'roles=ganesha'],
                         print_event=False)
    minions.extend(runner.cmd('select.minions',
                   ['cluster=ceph', 'ganesha_configurations=*'],
                   print_event=False))

    if not minions:
        return "No minions found with ganesha role"

    master = __salt__['master.minion']()
    nfs_pool = __salt__['master.find_pool'](['cephfs', 'rgw'])

    rep = {}
    rep['configuration'] = {'pool': nfs_pool, 'namespace': 'ganesha'}
    rep['gateways'] = {}

    # check if ganesha pkg installed
    nfs_pkgs = ['nfs-ganesha', 'nfs-ganesha-ceph', 'nfs-ganesha-rgw']
    for minion in minions:
        result = local.cmd(minion, 'pkg.info_installed', nfs_pkgs)
        if not result or minion not in result:
            raise Exception("Failed to run pkg.info_installed in {}".format(minion))

        res = result[minion]
        rep['gateways'][minion] = {'packages': {}}
        for pkg in nfs_pkgs:
            rep['gateways'][minion]['packages'][pkg] = {
                'installed': isinstance(res, dict) and pkg in res
            }
            if isinstance(res, dict) and pkg in res:
                rep['gateways'][minion]['packages'][pkg]['version'] = res[pkg]['version']

    # check if ganesha is running
    for minion in minions:
        if rep['gateways'][minion]['packages']['nfs-ganesha']['installed']:
            result = local.cmd(minion, 'service.status', ['nfs-ganesha'])
            if not result or minion not in result:
                raise Exception("Failed to run service.status in {}".format(minion))
            res = result[minion]
            rep['gateways'][minion]['running'] = res
        else:
            rep['gateways'][minion]['running'] = False

    # get ganesha.conf
    for minion in minions:
        if rep['gateways'][minion]['packages']['nfs-ganesha-ceph']['installed'] or \
                rep['gateways'][minion]['packages']['nfs-ganesha-rgw']['installed']:
            result = local.cmd(minion, 'cmd.run', ['cat /etc/ganesha/ganesha.conf'])
            if not result or minion not in result:
                raise Exception("Failed to retrieve ganesha.conf from {}".format(minion))
            res = result[minion]
            rep['gateways'][minion]['ganesha.conf'] = res

    # get rados conf obect
    for minion in minions:
        if rep['gateways'][minion]['packages']['nfs-ganesha-ceph']['installed'] or \
                rep['gateways'][minion]['packages']['nfs-ganesha-rgw']['installed']:
            gateway_id = local.cmd(minion, 'grains.get', ['host'])[minion]
            result = local.cmd(master, 'ganesha.get_gateway_conf_raw', [nfs_pool, gateway_id])
            if not result or master not in result:
                raise Exception("Failed to read gateway RADOS conf object in {}".format(master))
            res = result[master]
            rep['gateways'][minion]['rados_conf'] = res

    # get exports configuration
    result = local.cmd(master, 'ganesha.get_exports_raw', [nfs_pool])
    if not result or master not in result:
        raise Exception("Failed to read exports objects in {}".format(master))
    res = result[master]
    rep['exports'] = res

    return rep
