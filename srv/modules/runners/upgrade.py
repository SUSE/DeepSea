# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
"""
Verify that an automated upgrade is possible
"""
import salt.client
import salt.utils.error


class UpgradeValidation(object):
    """
    Due to the current situation you have to upgrade
    all monitors before ceph allows you to start any OSD
    Our current implementation of maintenance upgrades
    triggers this behavior if you happen to have
    Monitors and Storage roles assigned on the same node
    (And more then one monitor)
    To avoid this, before actually providing a proper solution,
    we stop users to execute the upgade in the first place.
    """

    def __init__(self, cluster='ceph'):
        """
        Initialize Salt client, cluster
        """
        self.local = salt.client.LocalClient()
        self.cluster = cluster

    def colocated_services(self):
        """
        Check for shared monitor and storage roles
        """
        search = "I@cluster:{}".format(self.cluster)
        pillar_data = self.local.cmd(search, 'pillar.items', [], expr_form="compound")
        for host in pillar_data:
            if 'roles' in pillar_data[host]:
                if ('storage' in pillar_data[host]['roles']
                   and 'mon' in pillar_data[host]['roles']):
                    msg = """
                         ************** PLEASE READ ***************
                         We currently do not support upgrading when
                         you have a monitor and a storage role
                         assigned on the same node.
                         ******************************************"""
                    return False, msg
        return True, ""

    def is_master_standalone(self):
        """
        Check for shared master and storage role
        """
        search = "I@roles:master"
        pillar_data = self.local.cmd(search, 'pillar.items', [], expr_form="compound")
        # in case of multimaster
        for host in pillar_data:
            if 'roles'in pillar_data[host]:
                if 'storage' in pillar_data[host]:
                    msg = """
                         ************** PLEASE READ ***************
                         Detected a storage role on your master.
                         This is not supported. Please migrate all
                         OSDs off the master in order to continue.
                         ******************************************"""
                    return False, msg
        return True, ""


def help_():
    """
    Usage
    """
    usage = ('salt-run upgrade.check:\n\n'
             '    Performs a series of checks to verify that upgrades are possible\n'
             '\n\n')
    print usage
    return ""


def check():
    """
    Run upgrade checks
    """
    uvo = UpgradeValidation()
    checks = [uvo.is_master_standalone]  # , uvo.colocated_services]
    for chk in checks:
        ret, msg = chk()
        if not ret:
            print msg
            return ret
    return ret

__func_alias__ = {
                 'help_': 'help',
                 }
