#!/usr/bin/env python
#
# Simple client to run iperf3 from salt in parallel across many nodes.
# Since passing different command line parameters to different targets
# is difficult to do with in salt.
#
from __future__ import print_function
import sys
import json
import salt.config
import os
try:
    from salt.utils import which as find_executable
except:
    from distutils.spawn import find_executable

def usage():
    print("salt_iperf_client minion_csv_list target_csv_list ... \n")
    print("salt_iperf_client script takes 2 comment seperated lists of paramters (CSV)")
    print("The two CSV list must be of equal length.")
    print("The first list must include the salt minion id for the node running.")
    print("The second list must include the ip address expected to be connected to by iperf.")
    print("Any remaining paramters will be passed on to the iperf3 command")


def eprint(*args, **kwargs):
    # We use print rather than logging as we do not want to complications of
    # flushing buffers on a simple script that must exit quickly.
    print(*args, file=sys.stderr, **kwargs)


if len(sys.argv) < 3:
    usage()
    eprint("Error: Takes a minium of 2 paramters")
    sys.exit(1)

path = find_executable('iperf3')
if path is None:
    # Don not use logging as we quit before logger flushes
    eprint("Error:could not find iperf3 on path")
    sys.exit(2)

minions_list_raw = sys.argv[1]
ip_list_raw = sys.argv[2]
minions_list = minions_list_raw.split(',')
ip_list = ip_list_raw.split(',')
if len(minions_list) != len(ip_list):
    usage()
    eprint("Error: minion_csv_list target_csv_list are different lengths.")
    sys.exit(3)

salt_opts = salt.config.minion_config('/etc/salt/minion')
salt_grains = salt.loader.grains(salt_opts)
minion_id = salt_grains['id']
try:
    index = minions_list.index(minion_id)
except ValueError as expt:
    usage()
    msg = "Error: minion_csv_list does not contain local minion id : {minion_id}".format(minion_id=minion_id)
    eprint(msg)
    sys.exit(4)

# Build command attributes
arguments = [path, '-c', ip_list[index]]
arguments.extend(sys.argv[3:])
# Replace process with iperf3
os.execvp(path, arguments)
