# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path
import hashlib
import logging
# pylint: disable=import-error,3rd-party-module-not-gated
import salt.client


__opts__ = salt.config.client_config('/etc/salt/master')

log = logging.getLogger(__name__)

class Config(object):
    def __init__(self, service_name):
        self.base_dir = '/srv/salt/ceph/configuration/files/'
        self.conf_dir = '/srv/salt/ceph/configuration/files/ceph.conf.d/'
        self.checksum_dir = '/srv/salt/ceph/configuration/files/ceph.conf.checksum/'
        self.checksum_file = self.checksum_dir + service_name + '.conf'
        self.service_name = service_name
        self.service_conf_files = [self.conf_dir + service_name + '.conf']
        self.dependencies = self.dependencies()
        self.rgw_configurations()
        log.debug("dependencies: {}".format(self.dependencies))

    def dependencies(self):
        """
        Services might depend on each other and have to trigger a restart.
        I.e. Changes in the MDS section might affect the NFS-Ganesha service
        hence the service should also be restarted.
        # TODO for other services and complete tree
        """
        return {'mds': ['mds'],
                'mon': ['mon'],
                'mgr': ['mgr'],
                'osd': ['osd'],
                'client': ['client'],
                'global': ['global']}

    def rgw_configurations(self):
        """
        RadosGW allows custom configurations.  Include these roles with a
        dependency on the global.conf.  Default to 'rgw' if not set.
        """
        # pylint: disable=redefined-outer-name
        local = salt.client.LocalClient()
        roles = []
        try:
            roles = local.cmd("I@roles:master", 'pillar.get', [ 'rgw_configurations' ], expr_form="compound").values()[0]
            log.debug("Querying pillar for rgw_configurations")
        except:
            pass
        if not roles:
            roles = [ 'rgw' ]
        for role in roles:
            if role == self.service_name:
                self.dependencies[role] = [ role, 'global' ]
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
                # pylint: disable=resource-leakage
                md5 = hashlib.md5(open(_file, 'rb').read()).hexdigest()
                log.debug("Checksum: {}".format(md5))
                checksums += md5
        if checksums:
            return hashlib.md5(checksums).hexdigest()
        log.debug("No file found to generate a checksum from. Looked for {}".format(self.service_conf_files))
        if os.path.exists(self.checksum_file):
            os.remove(self.checksum_file)
        return None

    def write_checksum(self, md5):
        """
        Write md5 to corresponding checksum file.
        """
        if md5:
            log.debug("Writing md5 checksum {} to {}".format(md5, self.checksum_file))
            # pylint: disable=resource-leakage
            with open(self.checksum_file, 'w') as _fd:
                _fd.write(md5)

    def read_checksum(self):
        """
        Read md5 from corresponding checksum file and return it.
        """
        if os.path.exists(self.checksum_file):
            log.debug("Reading existing md5 checksum from {}".format(self.checksum_file))
            # pylint: disable=resource-leakage
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

def help():
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
             '\n\n'
    )
    print usage
    return ""


def requires_conf_change(service, cluster='ceph'):
    """
    If any of the dependent services received a change
    in the its config, retrun True
    """
    cfg = Config(service)
    # pylint: disable=invalid-name
    local = salt.client.LocalClient()
    if service not in cfg.dependencies:
        return "Service {} not defined".format(service)
    for deps in cfg.dependencies[service]:
        if Config(deps).has_change():
            if service == 'osd':
                service = 'storage'
            search = 'I@cluster:{} and I@roles:{}'.format(cluster, service)
            local.cmd(search, 'grains.setval',
                      ["restart_{}".format(service), True],
                      expr_form="compound")
            return True
    return False

def rgw():
    return requires_conf_change('rgw')

def mds():
    return requires_conf_change('mds')

def osd():
    return requires_conf_change('osd')

def mon():
    return requires_conf_change('mon')

def mgr():
    return requires_conf_change('mgr')

def global_():
    return requires_conf_change('global')

def client():
    return requires_conf_change('client')

def config(service):
    return requires_conf_change(service)

__func_alias__ = {
                  'global_': 'global'
                 }
