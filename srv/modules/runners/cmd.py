# -*- coding: utf-8 -*-
from __future__ import absolute_import
import salt.client


def run(**kwargs):
    args = {'cmd': 'echo no command supplied'}
    args.update(kwargs)
    local_client = salt.client.LocalClient()
    target = 'I@roles:admin'
    output = local_client.cmd(target, 'cmd.shell', [args['cmd']], expr_form='compound')
    return next(iter(output.values()))
