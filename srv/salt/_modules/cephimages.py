# -*- coding: utf-8 -*-
"""
List the rbd images
"""

from __future__ import absolute_import
from subprocess import Popen, PIPE


def list_():
    """
    Find all rbd images
    """
    images = {}
    proc = Popen(['rados', 'lspools'], stdout=PIPE, stderr=PIPE)
    for line in proc.stdout:
        pool = line.rstrip('\n')
        cmd = ['/usr/bin/rbd', '-p', pool, 'ls']
        rbd_proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        for rbd_line in rbd_proc.stdout:
            if pool not in images:
                images[pool] = []
            images[pool].append(rbd_line.rstrip('\n'))

    return images

__func_alias__ = {
                 'list_': 'list',
                 }
