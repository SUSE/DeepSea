# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=modernize-parse-error,fixme,no-self-use
"""
This runner is here to detect config changes in the
various configuration files to control service restarts.
"""

from __future__ import absolute_import
from __future__ import print_function
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
        self._depends = []
        self._set_depends()

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

    @property
    def depends(self):
        """
        Getter for name attr
        """
        return self._depends

    @depends.setter
    def depends(self, role):
        """
        Setter for name attr
        """
        self._depends = role

    def _set_depends(self):
        """ Set dependency to self if not global """
        if self._role_name == 'global':
            # if the global config changed
            # stage restart on the core services
            self.add_dependencies(Role(role_name='mon'))
            self.add_dependencies(Role(role_name='mgr'))
            self.add_dependencies(Role(role_name='storage'))
            # also stage restarts on gateways (igw and genesha is not maintained here)
            self.add_dependencies(Role(role_name='mds'))
            self.add_dependencies(Role(role_name='rgw'))
        else:
            self.depends = [self]

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
                md5 = hashlib.md5(open(_file, 'rb').read()).hexdigest()
                log.debug("Checksum: {}".format(md5))
                checksums += md5
        if checksums:
            return hashlib.md5(checksums.encode('ascii')).hexdigest()
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
        return False


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
    print(usage)
    return ""


def requires_conf_change(**kwargs):
    """
    If any of the dependent roles received a change
    in the its config, retrun True
    """
    cfg = Config(**kwargs)
    role = cfg.role
    if not isinstance(role, Role):
        raise UnknownRole
    # pylint: disable=invalid-name
    local = salt.client.LocalClient()

    if Config(role=role).has_change():
        # If role has changes, also mark it's dependencies.
        for dep in cfg.role.dependencies:
            search = 'I@roles:{}'.format(dep.name)
            local.cmd(
                search,
                'grains.setval', ["restart_{}".format(dep.name), True],
                tgt_type="compound")
            log.info(f"Set restart grain for role:{dep.name}")
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
    Note: ceph-iscsi configuration is not kept in DeepSea
    """
    return False


def config(**kwargs):
    """
    Returns whether the configuration of the specified role changed
    """
    return requires_conf_change(role=Role(**kwargs))


__func_alias__ = {
                  'global_': 'global',
                  'help_': 'help'
                 }
