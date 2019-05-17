#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" This module will match disks based on applied filter rules

Internally this will be called 'DriveGroups'
"""

from __future__ import absolute_import
import logging
import json
import yaml
import salt.client

log = logging.getLogger(__name__)

USAGE = """

The disks runner is there to map the DriveGroup specification
to actual disk representation and ceph-volume calls.

It looks into your DriveGroup specs(/srv/salt/ceph/configuration/files/drive_groups.yml)
For guidance and examples on how to structure that please look in the github wiki pages:
https://github.com/SUSE/DeepSea/wiki/Drive-Groups

Available Functions:

## salt-run disks.list

Gives you a list of drives that would match your DriveGroup specs.

## salt-run disks.c_v_commands

Gives you a list of commands that would be executed on the respective minions.

## salt-run disks.report

Gives you a detailed report about what the anticipated osd layout.

## salt-run disks.deploy

Will actually issue the commands generated from disks.d_v_commands.


"""


class NoTargetFound(Exception):
    """ A critical error when no target is found for DriveGroup targeting
    """
    pass


class NoFilterFound(Exception):
    """ A critical error when no target is found for DriveGroup targeting
    """
    pass


# pylint: disable=too-few-public-methods
class DriveGroup(object):
    """ The base class container for local_client and compound_target assignment
    """

    def __init__(self, drive_group_name, drive_group_values) -> None:
        self.drive_group_name = drive_group_name
        self.drive_group_values = drive_group_values

    def target(self) -> str:
        """ The 'target' key which the user identfies the OSD nodes

        This will source the 'drive_group' pillar entry
        and extract the 'target'

        Salt tends to return all sorts of bulls^&%, hence the extensive
        validation

        :return: The target indentifying the osd nodes
        :rtype: str
        """

        target: str = self.drive_group_values.get('target', '')

        if target and isinstance(target, str):
            return target
        else:
            raise NoTargetFound(
                "Could not find a 'target' in the drive_group definition. "
                "Please refer to the documentation")

    def filter_args(self) -> dict:
        """ The actual filter arguments"""
        if self.drive_group_values and isinstance(self.drive_group_values,
                                                  dict):
            return self.drive_group_values
        else:
            raise NoFilterFound("Found not find a filter specification."
                                "Please refer to the documentation")


class DriveGroups(object):
    """ A DriveGroup container class

    self._data_devices = None
    It resolves the 'target' from the drive_group spec and
    feeds the 'target' one by one to the DriveGroup class.
    This in turn filters all matching devices and returns
    self._data_devices = None
    matching disks based on the specified filters.
    """

    def __init__(self, **kwargs: dict) -> None:
        self.local_client = salt.client.LocalClient()
        self.dry_run: bool = kwargs.get('dry_run', False)
        self.include_unavailable: bool = kwargs.get('include_unavailable',
                                                    False)
        self.target: str = kwargs.get('target', '')
        self.drive_groups_path: str = '/srv/salt/ceph/configuration/files/drive_groups.yml'
        self.drive_groups: dict = self._get_drive_groups()

    def _load_drive_group_file(self) -> str:
        """ Load the drive_group file """
        with open(self.drive_groups_path, 'r') as _fd:
            return yaml.load(_fd)

    def _get_drive_groups(self) -> dict:
        """ Get the drive Group specs"""
        ret = self._load_drive_group_file()
        if not ret:
            raise RuntimeError("Make sure to to populate {}.".format(
                self.drive_groups_path))

        if not isinstance(ret, dict):
            raise RuntimeError("""DriveGroup is not in an expected structure.
                Please consult the documentation.
                Expected a dict - Got a {}""".format(type(ret)))

        return ret

    def call_out(self, command: str, module: str = 'dg',
                 alias: str = None) -> list:
        """ Call minion modules to get matching disks """
        ret: list = list()
        for dg_name, dg_values in self.drive_groups.items():
            print("Found DriveGroup <{}>".format(dg_name))
            dgo = DriveGroup(dg_name, dg_values)
            if self.target:
                target = self.target
            else:
                target = dgo.target()
            ret.append(
                self.call(
                    target,
                    dgo.filter_args(),
                    command,
                    module=module,
                    alias=alias))
        # There is a __context__ variable which allow you to pass
        # rcs and stuff to the orchestration
        return ret

    def call(self,
             target: str,
             filter_args: dict,
             command: str,
             module: str = 'dg',
             alias: str = None):
        """ Calls out to the minion"""
        command_name: str = command
        if alias:
            command_name = alias
        log.debug("Calling {}.{} on compound target {}".format(
            module, command_name, target))
        print("Calling {}.{} on compound target {}".format(
            module, command_name, target))
        ret: str = self.local_client.cmd(
            target,
            '{}.{}'.format(module, command),
            kwarg={
                'filter_args': filter_args,
                'dry_run': self.dry_run,
                'include_unavailable': self.include_unavailable,
                'destroyed_osds': destroyed()
            },
            tgt_type='compound')

        return ret


def list_(**kwargs):
    """ List matching drives """
    return DriveGroups(**kwargs).call_out('list_drives')


def c_v_commands(**kwargs):
    """ Return resulting ceph-volume command """
    return DriveGroups(**kwargs).call_out('c_v_commands')


def deploy(**kwargs):
    """ Execute the ceph-volume command to deploy OSDs"""
    return DriveGroups(**kwargs).call_out('deploy')


def details(**kwargs):
    """ List details about drives on each node """
    return DriveGroups(**kwargs).call_out('attr_list', module='cephdisks')


def destroyed():
    """ List destroyed (about to be replaced) disks
    """
    # This can't be solved with Popen since the salt-master is running as
    # salt:salt
    local_client = salt.client.LocalClient()
    ret: str = local_client.cmd(
        "roles:master",
        'cmd.shell', ['ceph osd tree destroyed --format json'],
        tgt_type='pillar')

    tree = {}
    if ret:
        try:
            tree = json.loads(list(ret.values())[0]).get('nodes')
        except json.decoder.JSONDecodeError:
            log.info(
                "No valid json in ceph osd tree. Probably no cluster deployed yet."
            )

    # what is stray? # probably destroyed osds that are not listed nder
    # a certain bucket/host. This may be useful later
    # stray = json.loads(ret).get('stray')

    report_map = dict()
    for item in tree:
        # only looking for type host
        if item.get('type', '') == 'host':
            report_map.update({
                item.get('name', ''):
                item.get('children', list())
            })

    return report_map


def report(**kwargs):
    """ Get the OSD deployment report """
    kwargs.update({'dry_run': True})
    return DriveGroups(**kwargs).call_out('deploy', alias='report')


def discover(**kwargs):
    """ Discover OSDs on known hosts """
    discover_map = DriveGroups(**kwargs).call_out('discover', module='osd')[0]
    for host, osds in discover_map.items():
        if not osds:
            continue
        print(f"Found the following OSDs on host {host}")
        for osd in osds:
            print(_format_osd_map(osd))
    return ''


def _format_osd_map(osd: dict) -> str:
    """ Format return from osd.discover return """
    message: str = f"""
osd_id  : {osd.get('_osd_id',''):<1}
osd_fsid: {osd.get('_fsid',''):<1}
backend : {osd.get('_backend',''):<1}
data    : {osd.get('_block_data',''):<1}
db      : {osd.get('_block_db',''):<1}
wal     : {osd.get('_block_wal',''):<1}
journal : {osd.get('_journal',''):<1}
dmcrypt : {osd.get('_block_dmcrypt',''):<1}
    """
    return message


def help_():
    """ Help/Usage class
    """
    print(USAGE)


__func_alias__ = {
    'help_': 'help',
    'list_': 'list',
}
