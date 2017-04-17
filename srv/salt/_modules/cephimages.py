#!/usr/bin/python

import os
import re
import pprint
from glob import glob
from subprocess import Popen, PIPE


def list():
    """
    Find all rbd images
    """
    images = {}
    proc = Popen([ 'rados', 'lspools' ], stdout=PIPE, stderr=PIPE)
    for line in proc.stdout:
	pool = line.rstrip('\n')
	cmd = [ '/usr/bin/rbd', '-p', pool, 'ls' ]
	rbd_proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
	for rbd_line in rbd_proc.stdout:
	    if pool not in images:
		images[pool] = []
	    images[pool].append(rbd_line.rstrip('\n'))

    return images
