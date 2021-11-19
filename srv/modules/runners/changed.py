# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# pylint: disable=modernize-parse-error,fixme,no-self-use
"""
This runner is here to detect config changes in the
various configuration files to control service restarts.
"""

from __future__ import absolute_import
from __future__ import print_function
import os
import hashlib
import logging
import glob
import sys
# pylint: disable=import-error,3rd-party-module-not-gated
import salt.client

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
        self._conf_files = glob.glob(self.conf_dir + self.conf_filename + self.conf_extension)

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


class Config(object):
    """
    Tracks the configuration files and checksums
    """

    def __init__(self, role):
        """
        Initialize locations for configuration files
        """
        self.role = role
        self.base_dir = '/srv/salt/ceph/configuration/files/'
        self.checksum_dir = self.base_dir + 'ceph.conf.checksum/'
        self.checksum_file = self.checksum_dir + self.role.conf_filename + self.role.conf_extension

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
        Compare md5s and return status, and also write out new checksum if
        the state has changed.  This is NOT idempotent!
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


def any():
    # pylint: disable=redefined-builtin
    """
    Checks whether any configuration has changed, and if it has, sets the
    various restart grains appropriately, then returns True, otherwise
    returns False.
    """
    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)
    master_minion = __salt__['master.minion']()

    # roles_to_check is a complete list of all possible roles that could exist,
    # that might have config changes.
    roles_to_check = [
        Role(role_name='mon'),
        Role(role_name='mgr'),
        Role(role_name='mds'),
        Role(role_name='storage', conf_filename='osd'),
        Role(role_name='client'),
        Role(
            role_name='igw',
            conf_dir='/srv/salt/ceph/igw/cache/',
            conf_filename="iscsi-gateway.*",
            conf_extension=".cfg"
        ),
    ]

    local = salt.client.LocalClient()
    rgw_roles = list(local.cmd(master_minion, 'pillar.get', ['rgw_configurations']).items())[0][1]
    if not rgw_roles:
        rgw_roles = ['rgw']
    for role in rgw_roles:
        roles_to_check.append(Role(role_name=role))

    # grains_to_set is the actual set of restart grains we want to set, based
    # on what configuration has actually changed.
    grains_to_set = set()

    # In the case where only individual config files are changed, we just add
    # only those changed roles to grains_to_set...
    for role in roles_to_check:
        if Config(role).has_change():
            grains_to_set.add(role.name)

    # ...but if the global config has changed, we go ahead and add every
    # possible role to grains_to_set, so all daemons get restarted if the
    # global config has changed.
    if Config(Role(role_name='global')).has_change():
        for role in roles_to_check:
            grains_to_set.add(role.name)

    if not grains_to_set:
        return False

    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    for role in grains_to_set:
        log.info("Setting restart_{} grain".format(role))
        search = 'I@cluster:ceph and I@roles:{}'.format(role)
        local.cmd(search, 'grains.setval', ["restart_{}".format(role), True], tgt_type="compound")
    sys.stdout = _stdout

    return True
