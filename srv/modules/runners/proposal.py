# -*- coding: utf-8 -*-

import salt.client
# import salt.key
# import salt.config
# import salt.utils
# import salt.utils.minions

import argparse
import re
import pprint
import string
import random
import yaml
import json
from os.path import dirname, basename, isdir, isfile
import os
import struct
import time
import base64
import errno
import uuid
import ipaddress
import logging

import sys

log = logging.getLogger(__name__)

usage = '''
proposal runner assembles node proposals
'''

base_dir = '/srv/pillar/ceph/proposals'

std_args = {
    'standalone': False,
    'standalone-leftovers': False,
    'nvme-ssd': False,
    'nvme-spinner': False,
    'ssd-spinner': False,
    'ratio': 5,
    'target': '*',
    'data': 0,
    'journal': 0,
    'name': 'default',
    'format': 'bluestore',
    'encryption': '',
    'journal_size': 5,
}


def _parse_args(kwargs):
    args = std_args.copy()
    args.update(kwargs)
    return args


def _propose(node, proposal, args):
    # iterate over proposals and output appropriate device data
    profile = {}
    for device in proposal:
        k, v = device.items()[0]
        dev_par = {}
        dev_par['journal'] = v
        dev_par['format'] = args.get('format')
        dev_par['encryption'] = args.get('encryption')
        dev_par['journal_size'] = args.get('journal_size')
        profile[k] = dev_par

    return {node: profile}


def _choose_proposal(node, proposal, args):
    confs = ['nvme-ssd', 'nvme-spinner', 'ssd-spinner', 'standalone']
    # propose according to flags if present
    for conf in confs:
        if args[conf]:
            return _propose(node, proposal[conf], args)
    # if no flags a present propose what is there
    for conf in confs:
        if proposal[conf]:
            return _propose(node, proposal[conf], args)


def peek(help_=False, **kwargs):
    if help_:
        print(usage)
    args = _parse_args(kwargs)

    local_client = salt.client.LocalClient()

    proposals = local_client.cmd(args['target'], 'proposal.generate',
                                 expr_form='compound', kwarg=args)

    # determine which proposal to choose
    for node, proposal in proposals.items():
        p = _choose_proposal(node, proposal, args)
        if p:
            pprint.pprint(p)


def _write_proposal(p, profile_dir):

    node, proposal = p.items()[0]

    profile_file = '{}/{}.yml'.format(profile_dir, node)
    if isfile(profile_file):
        log.warn('not overwriting existing proposal {}'.format(node))
        return

    with open(profile_file, 'w') as outfile:
        content = {'ceph': {'storage': {'devices': proposal}}}
        yaml.dump(content, outfile, default_flow_style=False)


def populate(help_=False, **kwargs):
    if help_:
        print(usage)
    args = _parse_args(kwargs)

    local_client = salt.client.LocalClient()

    proposals = local_client.cmd(args['target'], 'proposal.generate',
                                 expr_form='compound', kwarg=args)

    # check if profile of 'name' exists
    profile_dir = '{}/profile-{}'.format(base_dir, args['name'])
    if not isdir(profile_dir):
        os.makedirs(profile_dir, 755)

    # determine which proposal to choose
    for node, proposal in proposals.items():
        p = _choose_proposal(node, proposal, args)
        if p:
            _write_proposal(p, profile_dir)
