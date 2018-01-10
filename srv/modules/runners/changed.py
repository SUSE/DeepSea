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
# pylint: disable=import-error,3rd-party-module-not-gated
import salt.client

__opts__ = salt.config.client_config('/etc/salt/master')
log = logging.getLogger(__name__)


class UnknownRole(Exception):
    """
    Raise when passed an unknown type or role to
    Role().
    """
    pass


class Role(object):
    """
    Class for roles to access meta data more easily
    """

    def __init__(self, **kwargs):
        self._role_name = kwargs.get('role_name')
        self.conf_dir = kwargs.get('conf_dir', '/srv/salt/ceph/configuration/files/ceph.conf.d/')
        self.conf_filename = kwargs.get('conf_filename', self._role_name)
        self.conf_extension = kwargs.get('conf_extension', '.conf')
        self._conf_files = [self.conf_dir + self.conf_filename + self.conf_extension]
        self._depends = [self]
        self.rgw_configurations()

    @property
    def name(self):
        """
        Getter for name attr
        """
        return self._role_name

    @name.setter
    def name(self, name):
        """
        Setter for name attr
        """
        self._role_name = name

    @property
    def conf_files(self):
        """
        Returns corresponding config files
        """
        return self._conf_files

    def add_conf_file(self, conf_file):
        """
        Adds config files to list
        """
        self._conf_files.append(conf_file)

    @property
    def dependencies(self):
        """
        Returns dependency list
        """
        return self._depends

    def add_dependencies(self, role):
        """
        Adds Role to list of dependencies
        """
        if isinstance(role, list):
            # also if the containting items are instance of Role
            self._depends.extend(role)
        elif isinstance(role, Role):
            self._depends.append(role)
        else:
            raise UnknownRole

    def dependencies_unwrapped(self):
        """
        Return a list of human readable names of Roles
        DEV/DEBUG
        """
        return [dep.name for dep in self.dependencies]

    def rgw_configurations(self):
        """
        RadosGW allows custom configurations.  Include these roles with a
        dependency on the global.conf.  Default to 'rgw' if not set.
        """
        # pylint: disable=redefined-outer-name
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
            if role == self.name:
                self.add_dependencies(Role(role_name='global'))


class Config(object):
    """
    Tracks the configuration files, related dependencies and checksums
    """

    def __init__(self, **kwargs):
        """
        Initialize locations for configuration files
        """
        self.role = kwargs.get('role')
        self.base_dir = '/srv/salt/ceph/configuration/files/'
        self.checksum_dir = self.base_dir + 'ceph.conf.checksum/'
        self.checksum_file = self.checksum_dir + self.role.conf_filename + self.role.conf_extension
        log.debug("dependencies of role {}: {}".format(self.role.name,
                                                       self.role.dependencies_unwrapped()))

    def create_checksum(self):
        """
        Creating a checksums of checksums to detect a change
        even if there are multiple files used to configure a role.
        Cleanup old checksumfiles if the config was removed.
        """
        checksums = ''
        for _file in self.role.conf_files:
            if os.path.exists(_file):
                log.debug("Generating checksum for {}".format(_file))
                # pylint: disable=resource-leakage
                md5 = hashlib.md5(open(_file, 'rb').read()).hexdigest()
                log.debug("Checksum: {}".format(md5))
                checksums += md5
        if checksums:
            return hashlib.md5(checksums).hexdigest()
        log.debug(("No file found to generate a checksum from. Looked for "
                   "{}".format(self.role.conf_files)))
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
        log.info("Checking role {}".format(self.role.name))
        previous_cs = self.read_checksum()
        current_cs = self.create_checksum()
        if not (current_cs or previous_cs):
            log.info("No config file {}".format(self.role.conf_files))
            return False
        if current_cs == previous_cs:
            log.info("No change in configuration detected for role {}".format(self.role.name))
            return False
        if current_cs != previous_cs:
            log.info("Change in configuration detected for role {}".format(self.role.name))
            self.write_checksum(current_cs)
            return True


def help_():
    """
    Usage
    """
    usage = ('salt-run changed.requires_conf_change role:\n'
             'salt-run changed.config name=role:\n\n'
             '    Checks whether the user configured files for the named role has changed\n'
             '\n\n'
             'salt-run changed.rgw:\n'
             'salt-run changed.mds:\n'
             'salt-run changed.osd:\n'
             'salt-run changed.mon:\n'
             'salt-run changed.global:\n'
             'salt-run changed.client:\n\n'
             '    Shortcuts for many roles\n'
             '\n\n')
    print usage
    return ""


def requires_conf_change(**kwargs):
    """
    If any of the dependent roles received a change
    in the its config, retrun True
    """
    cfg = Config(**kwargs)
    role = cfg.role
    cluster = kwargs.get('cluster', 'ceph')
    if not isinstance(role, Role):
        raise UnknownRole
    # pylint: disable=invalid-name
    local = salt.client.LocalClient()
    if role not in cfg.role.dependencies:
        return "Role {} not defined".format(role.name)
    for deps in cfg.role.dependencies:
        if Config(role=deps).has_change():
            search = 'I@cluster:{} and I@roles:{}'.format(cluster, role.name)
            local.cmd(search, 'grains.setval',
                      ["restart_{}".format(role.name), True],
                      tgt_type="compound")
            return True
    return False


def rgw():
    """
    Returns whether RadosGW configuration changed
    """
    return requires_conf_change(role=Role(role_name='rgw'))


def mds():
    """
    Returns whether CephFS configuration changed
    """
    return requires_conf_change(role=Role(role_name='mds'))


def osd():
    """
    Returns whether OSD configuration changed
    """
    return requires_conf_change(role=Role(role_name='storage',
                                          conf_filename='osd'))


def mon():
    """
    Returns whether monitor configuration changed
    """
    return requires_conf_change(role=Role(role_name='mon'))


def mgr():
    """
    Returns whether monitor configuration changed
    """
    return requires_conf_change(role=Role(role_name='mgr'))


def global_():
    """
    Returns whether the global configuration changed
    """
    return requires_conf_change(role=Role(role_name='global'))


def client():
    """
    Returns whether the client configuration changed
    """
    return requires_conf_change(role=Role(role_name='client'))


def igw():
    """
    Returns whether igw configuration has changed
    """
    return requires_conf_change(role=Role(role_name='igw',
                                          conf_dir='/srv/salt/ceph/igw/cache/',
                                          conf_filename='lrbd'))


def config(**kwargs):
    """
    Returns whether the configuration of the specified role changed
    """
    return requires_conf_change(role=Role(**kwargs))


__func_alias__ = {
                  'global_': 'global',
                  'help_': 'help'
                 }
