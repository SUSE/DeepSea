# -*- coding: utf-8 -*-
"""
This runner enables any minion to run a command on an admin node. Most notably
this enables minions to execute ceph commands that needs an admin keyring.
"""
from __future__ import absolute_import
import salt.client


def run(**kwargs):
    """
    Run an arbitrary command on a admin node (any node that has a admin
    keyring)
    """
    args = {'cmd': 'echo no command supplied'}
    args.update(kwargs)
    local_client = salt.client.LocalClient()
    target = 'I@roles:admin'
    output = local_client.cmd(target, 'cmd.shell', [args['cmd']], expr_form='compound')
    return next(iter(output.values()))
