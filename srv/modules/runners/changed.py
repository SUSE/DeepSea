# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=modernize-parse-error,fixme,no-self-use
"""
This runner is here to detect config changes in the
various configuration files to control service restarts.
"""

import os.path
import hashlib
import logging
import salt.client


log = logging.getLogger(__name__)


class Config(object):
    """
    Tracks the configuration files, related dependencies and checksums
    """

    def __init__(self, service_name):
        """
        Initialize locations for configuration files
        """
        self.base_dir = '/srv/salt/ceph/configuration/files/'
        self.conf_dir = '/srv/salt/ceph/configuration/files/ceph.conf.d/'
        self.checksum_dir = '/srv/salt/ceph/configuration/files/ceph.conf.checksum/'
        self.checksum_file = self.checksum_dir + service_name + '.conf'
        self.service_name = service_name
        self.service_conf_files = [self.conf_dir + service_name + '.conf']
        self.dependencies = self.depends()
        self.rgw_configurations()
        log.debug("dependencies: {}".format(self.dependencies))

    def depends(self):
        """
        Services might depend on each other and have to trigger a restart.
        I.e. Changes in the MDS section might affect the NFS-Ganesha service
        hence the service should also be restarted.
        # TODO for other services and complete tree
        """
        return {'mds': ['mds'],
                'mon': ['mon'],
                'osd': ['osd'],
                'client': ['client'],
                'global': ['global']}

    def rgw_configurations(self):
        """
        RadosGW allows custom configurations.  Include these roles with a
        dependency on the global.conf.  Default to 'rgw' if not set.
        """
        local = salt.client.LocalClient()
        roles = []
        try:
            roles = local.cmd("I@roles:master", 'pillar.get',
                              ['rgw_configurations'],
                              expr_form="compound").values()[0]
            log.debug("Querying pillar for rgw_configurations")
        # pylint: disable=bare-except
        except:
            pass
        if not roles:
            roles = ['rgw']
        for role in roles:
            if role == self.service_name:
                self.dependencies[role] = [role, 'global']
                for dep in self.dependencies[role][1:]:
                    log.debug("Resolving RGW configurations files")
                    self.service_conf_files.append(self.conf_dir + dep + '.conf')

    def create_checksum(self):
        """
        Creating a checksums of checksums to detect a change
        even if there are multiple files used to configure a service.
        Cleanup old checksumfiles if the config was removed.
        """
        checksums = ''
        for _file in self.service_conf_files:
            if os.path.exists(_file):
                log.debug("Generating checksum for {}".format(_file))
                md5 = hashlib.md5(open(_file, 'rb').read()).hexdigest()
                log.debug("Checksum: {}".format(md5))
                checksums += md5
        if checksums:
            return hashlib.md5(checksums).hexdigest()
        log.debug(("No file found to generate a checksum from. Looked for "
                   "{}".format(self.service_conf_files)))
        if os.path.exists(self.checksum_file):
            os.remove(self.checksum_file)
        return None

    def write_checksum(self, md5):
        """
        Write md5 to corresponding checksum file.
        """
        if md5:
            log.debug("Writing md5 checksum {} to {}".format(md5, self.checksum_file))
            with open(self.checksum_file, 'w') as _fd:
                _fd.write(md5)

    def read_checksum(self):
        """
        Read md5 from corresponding checksum file and return it.
        """
        if os.path.exists(self.checksum_file):
            log.debug("Reading existing md5 checksum from {}".format(self.checksum_file))
            with open(self.checksum_file, 'r') as _fd:
                md5 = _fd.readline().rstrip()
            return md5
        log.debug("No existing checksum for {}".format(self.checksum_file))
        return None

    def has_change(self):
        """
        Compare md5s and return status
        """
        log.info("Checking service {}".format(self.service_name))
        previous_cs = self.read_checksum()
        current_cs = self.create_checksum()
        if not (current_cs or previous_cs):
            log.info("No config file {}".format(self.service_conf_files))
            return False
        if current_cs == previous_cs:
            log.info("No change in configuration detected for service {}".format(self.service_name))
            return False
        if current_cs != previous_cs:
            log.info("Change in configuration detected for service {}".format(self.service_name))
            self.write_checksum(current_cs)
            return True


def help_():
    """
    Usage
    """
    usage = ('salt-run changed.requires_conf_change service:\n'
             'salt-run changed.config service:\n\n'
             '    Checks whether the user configured files for the named service has changed\n'
             '\n\n'
             'salt-run changed.rgw:\n'
             'salt-run changed.mds:\n'
             'salt-run changed.osd:\n'
             'salt-run changed.mon:\n'
             'salt-run changed.global:\n'
             'salt-run changed.client:\n\n'
             '    Shortcuts for many services\n'
             '\n\n')
    print usage
    return ""


def requires_conf_change(service):
    """
    If any of the dependent services received a change
    in the its config, retrun True
    """
    cfg = Config(service)
    if service not in cfg.dependencies:
        return "Service {} not defined".format(service)
    for deps in cfg.dependencies[service]:
        if Config(deps).has_change():
            return True
    return False


def rgw():
    """
    Returns whether RadosGW configuration changed
    """
    return requires_conf_change('rgw')


def mds():
    """
    Returns whether CephFS configuration changed
    """
    return requires_conf_change('mds')


def osd():
    """
    Returns whether OSD configuration changed
    """
    return requires_conf_change('osd')


def mon():
    """
    Returns whether monitor configuration changed
    """
    return requires_conf_change('mon')


def global_():
    """
    Returns whether the global configuration changed
    """
    return requires_conf_change('global')


def client():
    """
    Returns whether the client configuration changed
    """
    return requires_conf_change('client')


def config(service):
    """
    Returns whether the configuration of the specified service changed
    """
    return requires_conf_change(service)


__func_alias__ = {
                  'global_': 'global',
                  'help_': 'help'
                 }
