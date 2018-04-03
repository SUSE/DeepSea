# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error,fixme
"""
Generates the hardware profiles for a minion
"""
from __future__ import absolute_import
from __future__ import print_function
import pprint
from os.path import isdir, isfile
import os
# pylint: disable=redefined-builtin
from sys import exit
import logging
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client
import yaml
# pylint: disable=import-error
from deepsea_minions import DeepseaMinions

log = logging.getLogger(__name__)

USAGE = '''
The proposal runner compiles and either shows or writes storage profile
proposals. It offers two methods: 'peek' and 'populate'.
The 'peek' method simply collects the proposals from the minions and displays
the chosen proposal.
The 'populate' method writes these proposals to a storage profile directory.
By default this profile is written to
'/srv/pillar/ceph/proposal/profile-default'. The profile can also be named by
passing 'name=foo'. The profile is then written to
'/srv/pillar/ceph/proposal/profile-foo'.

There are several ways to influence what storage layouts are proposed and
which proposal is actually chosen. By default this runner will try to propose
the highest preforming storage setup for a node. That is it'll prefer journals
on nvme and data on ssd over journal on nvme and data on spinners over journal
on ssd and data on spinners (assuming the hardware is actually there). If all
this fails standalone OSDs will be proposed.

By default a 5 to 1 data device to journal device ratio will be proposed. This
can be changed (to say 7 to 1) by passing 'ratio=7'. Drives that are leftover
after proposing external journal OSDs will not be included unless
'leftovers=True' is passed.

To limit which drives will be considered as data or journal drives the 'data='
and 'journal=' parameters can be specified. Both will take either a number or a
range 'min-max' (for example data=500, data=500-1000). Only drives of the exact
capacity in GB (in case of a number) or drives that fall into the range (also
in GB) will be considered for data drives or journal drives respectively.

The 'target=' parameter can be passed to only show or store proposals from
minions fitting the specified glob. For example 'target="data1*"' will
only query minions whose minion id starts with 'data1'.

List of recognized parameters and their defaults:
    leftovers=False - Set to True to propose leftover drives as
                                 standalone OSDs.
    standalone=False
    nvme-ssd=False
    nvme-spinner=False
    ssd-spinner=False - Set any of these to True to force the runner to return
                        a certain proposal. Note that this can end up returning
                        an empty proposal
    ratio=5 - Set the amount of data drives per journal drive (for filestore)
              wal/db drive (for bluestore)
    db-ratio=5 - Set the amount of db drives per wal partition. Only has an
                  effect if format=bluestore and all three device classes are
                  present, i.e. spinners, ssds and nvmes
    target='*' - Glob to specify which nodes will be queried
    data=0
    journal=0
    db=0
    wal=0     - Size filter for data/journal/db/wal drives. 0 means no filtering. A
                number (in GB) can be specified or a range min-max (also in
                GB). For example journal=500-1000 will only consider drives
                between 500GB and 1TB for journal devices. journal and db are
                treated to be equivalent with db taking precedence.
    name=default - Name of the storage profile and thus location of the
                   resulting files.
    format=bluestore - The OSDs underlying storage format. Legal values are
                       bluestore and filestore.
    encryption='' - Set to dmcrypt to encrypt OSD. Leave empty (the default)
                    for non-encrypted OSDs.
    journal-size=5g
    db-size=500m
    wal-size=500m - Sizes for journal/db/wal partitions respectively. Specify a
                    number with a unit suffix. Unit suffix' as accepted by
                    sgdisk can be used, i.e. kibibytes (K), mebibytes (M),
                    gibibytes (G), tebibytes (T), or pebibytes (P).
'''

TARGET = DeepseaMinions()

STD_ARGS = {
    'leftovers': False,
    'standalone': False,
    'nvme-ssd-spinner': False,
    'nvme-ssd': False,
    'nvme-spinner': False,
    'ssd-spinner': False,
    'ratio': 5,
    'db-ratio': 5,
    'target': TARGET.deepsea_minions,
    'data': 0,
    'journal': 0,
    'wal': 0,
    'name': 'default',
    'format': 'bluestore',
    'encryption': '',
    'journal-size': '5g',
    'db-size': '500m',
    'wal-size': '500m',
}

BASE_DIR = '/srv/pillar/ceph/proposals'


def _parse_args(kwargs):
    """
    Parse command line arguments
    """
    args = STD_ARGS.copy()
    args.update(kwargs)
    if args.get('name') == 'import':
        print(('ERROR: profile name import is a reserved name. Please use'
              ' another name'))
        exit(-1)
    if args.get('encryption') != '' and args.get('encryption') != 'dmcrypt':
        print((('ERROR: encryption{} is not supported. Currently only '
               '"dmcrypt" is supported.').format(args.get('encryption'))))
        exit(-1)

    return args


def _propose(node, proposal, args):
    """
    Iterate over proposals and output appropriate device data
    """
    profile = {}
    for device in proposal:
        key, value = list(device.items())[0]
        dev_par = {}
        format_ = args.get('format')
        if isinstance(value, dict):
            assert format_ == 'bluestore'
            # pylint: disable=invalid-name
            db, wal = list(value.items())[0]
            dev_par['wal'] = wal
            dev_par['db'] = db
            dev_par['wal_size'] = args.get('wal-size')
            dev_par['db_size'] = args.get('db-size')
        elif isinstance(value, str) and value != '':
            if format_ == 'bluestore':
                dev_par['wal'] = value
                dev_par['db'] = value
                dev_par['wal_size'] = args.get('wal-size')
                dev_par['db_size'] = args.get('db-size')
            else:
                dev_par['journal'] = value
                dev_par['journal_size'] = args.get('journal-size')
        dev_par['format'] = format_
        if args.get('encryption') != '':
            dev_par['encryption'] = args.get('encryption')
        profile[key] = dev_par

    return {node: profile}


def _choose_proposal(node, proposal, args):
    """
    Select proposal or default to hardware present
    """
    confs = ['nvme-ssd-spinner', 'nvme-ssd', 'nvme-spinner', 'ssd-spinner', 'standalone']
    # propose according to flags if present
    for conf in confs:
        if args[conf]:
            return _propose(node, proposal[conf], args)
    # if no flags a present propose what is there
    for conf in confs:
        if conf in proposal:
            if proposal[conf]:
                return _propose(node, proposal[conf], args)
        else:
            log.error("Verify that targeted minions have proposal.generate")


def help_():
    """
    Usage
    """
    print(USAGE)


def test(**kwargs):
    """
    Runtime test case
    """
    args = _parse_args(kwargs)

    local_client = salt.client.LocalClient()

    proposals = local_client.cmd(args['target'], 'proposal.test',
                                 tgt_type='compound', kwarg=args)

    # determine which proposal to choose
    for node, proposal in proposals.items():
        _proposal = _choose_proposal(node, proposal, args)
        if _proposal:
            pprint.pprint(_proposal)


def peek(**kwargs):
    """
    Display the output to the user
    """
    args = _parse_args(kwargs)

    local_client = salt.client.LocalClient()

    proposals = local_client.cmd(args['target'], 'proposal.generate',
                                 tgt_type='compound', kwarg=args)

    # determine which proposal to choose
    for node, proposal in proposals.items():
        _proposal = _choose_proposal(node, proposal, args)
        if _proposal:
            pprint.pprint(_proposal)


def _write_proposal(prop, profile_dir):
    """
    Save the proposal for a specific minion
    """
    node, proposal = list(prop.items())[0]

    # write out roles
    role_file = '{}/cluster/{}.sls'.format(profile_dir, node)

    with open(role_file, 'w') as outfile:
        content = {'roles': ['storage']}
        # implement merge of existing data
        yaml.dump(content, outfile, default_flow_style=False)

    # TODO do not hardcode cluster name ceph here
    profile_file = '{}/stack/default/ceph/minions/{}.yml'.format(profile_dir,
                                                                 node)
    if isfile(profile_file):
        log.warning('not overwriting existing proposal {}'.format(node))
        return

    # write storage profile
    with open(profile_file, 'w') as outfile:
        content = {'ceph': {'storage': {'osds': proposal}}}
        # implement merge of existing data
        yaml.dump(content, outfile, default_flow_style=False)


def _record_filter(args, base_dir):
    """
    Save the filter provided
    """
    filter_file = '{}/.filter'.format(base_dir)

    if not isfile(filter_file):
        # do a touch filter_file
        open(filter_file, 'a').close()

    current_filter = {}
    with open(filter_file) as filehandle:
        current_filter = yaml.load(filehandle)
    if current_filter is None:
        current_filter = {}

    pprint.pprint(current_filter)

    # filter a bunch of salt content and the target key before writing
    rec_args = {k: v for k, v in args.items() if k is not 'target' and not
                k.startswith('__')}
    current_filter[args['target']] = rec_args

    with open(filter_file, 'w') as filehandle:
        yaml.dump(current_filter, filehandle, default_flow_style=False)


def populate(**kwargs):
    """
    Aggregate the results of the modules and save the desired proposal for
    all minions.
    """
    args = _parse_args(kwargs)

    local_client = salt.client.LocalClient()

    proposals = local_client.cmd(args['target'], 'proposal.generate',
                                 tgt_type='compound', kwarg=args)

    # check if profile of 'name' exists
    profile_dir = '{}/profile-{}'.format(BASE_DIR, args['name'])
    if not isdir(profile_dir):
        os.makedirs(profile_dir, 0o755)
    # TODO do not hardcode cluster name ceph here
    if not isdir('{}/stack/default/ceph/minions'.format(profile_dir)):
        os.makedirs('{}/stack/default/ceph/minions'.format(profile_dir), 0o755)
    if not isdir('{}/cluster'.format(profile_dir)):
        os.makedirs('{}/cluster'.format(profile_dir), 0o755)

    # determine which proposal to choose
    for node, proposal in proposals.items():
        _proposal = _choose_proposal(node, proposal, args)
        if _proposal:
            _write_proposal(_proposal, profile_dir)
    # write out .filter here...will need some logic to merge existing data too.
    _record_filter(args, profile_dir)

    return True

__func_alias__ = {
                 'help_': 'help',
                 }
