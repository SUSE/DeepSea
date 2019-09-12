# -*- coding: utf-8 -*-
'''
'''
from __future__ import absolute_import
import errno
import os
import logging
import pprint
import uuid
import sys
import yaml

import salt.key
import salt.client
import salt.runner
from ext_lib.utils import master_minion, evaluate_state_return
from ext_lib.network import DeepSeaNetwork

log = logging.getLogger(__name__)


def _module(cmd):
    ''' Resolve Salt target '''
    local = salt.client.LocalClient()
    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    try:
        result = local.cmd(master_minion(), cmd, [], tgt_type="compound")
        sys.stdout = _stdout
    except SaltClientError as error:
        sys.stdout = _stdout
        log.error(f"salt-call {cmd} failed... {error}")
        return {}
    return list(result.values())[0]


def create(*args):
    '''   '''
    subcommands = {
        "admin": [create_adminrc],
        "bootstrap": [create_bootstraprc],
        "bad": [create_badrc],
        "all": [create_adminrc, create_bootstraprc]
    }

    if args:
        subcommand = args[0]
    else:
        subcommand = "all"

    for cmd in subcommands[subcommand]:
        ret = cmd()
        if ret['result']:
            print(ret['changes']['out'])
        else:
            print(f"Failed: {ret['comment']}")
            return ""
    return ""


def _friendly(ret):
    ''' Returns human readable output or error '''
    if ret['result']:
        return ret['changes']['out']
    else:
        return f"exit code: {ret['rc']}\n{ret['comment']}"


def create_admin():
    '''   '''
    print(_friendly(create_adminrc()))
    return ""


def create_adminrc():
    '''   '''
    return (_module('keyring2.adminrc'))


def create_bootstrap():
    '''   '''
    print(_friendly(create_bootstraprc()))
    return ""


def create_bootstraprc():
    '''   '''
    return (_module('keyring2.bootstraprc'))


def create_bad():
    '''   '''
    print(_friendly(create_badrc()))
    return ""


def create_badrc():
    '''   '''
    return (_module('keyring2.badrc'))
