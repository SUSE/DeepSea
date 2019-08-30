# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4

import salt.client


def get_sys_versions(cluster_name='ceph'):
    """
    Query grains, run commands for current versions
    """
    local = salt.client.LocalClient()
    search = "I@cluster:{}".format(cluster_name)
    # grains might be inaccurate or not up to date because they are designed
    # to hold static data about the minion. In case of an update though, the
    # data will change.  grains are refreshed on reboot(restart of the service).
    os_codename = local.cmd(search, 'grains.get', ['oscodename'], tgt_type="compound")
    salt_version = local.cmd(search, 'grains.get', ['saltversion'], tgt_type="compound")
    ceph_version = local.cmd(search, 'cmd.shell', ['test -e /usr/bin/ceph && ceph --version || echo "Not installed"'], tgt_type="compound")
    return os_codename, salt_version, ceph_version
