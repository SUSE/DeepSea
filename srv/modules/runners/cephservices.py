#!/usr/bin/python

import salt.client
import pprint
import os
import sys
import logging
import time
import salt.utils
import salt.utils.master

log = logging.getLogger(__name__)

"""
The original purpose of this runner is to verify that proceeding with an
upgrade is safe.  All expected services are running.

A secondary purpose is a utility to check the current state of all services.
"""

def check(cluster='ceph', **kwargs):
    """
    Query the status of running processes for each role.  Also, verify that
    all minions assigned roles do respond.  Return False if any fail. 
    """
    processes = { 'mon': [ 'ceph-mon' ],
                 'storage': [ 'ceph-osd' ],
                 'mds': [ 'ceph-mds' ],
                 'igw': [ 'lrbd' ],
                 'rgw': [ 'radosgw' ],
                 'ganesha': [ 'ganesha.nfsd', 'rpcbind', 'rpc.statd' ] }
    search = "I@cluster:{}".format(cluster)

    roles = _cached_roles(search)
    status = _status(processes, search)

    ret = True
    for role in status.keys():
        for process in status[role].keys():
            if role in roles:
                for minion in roles[role]:
                    if minion not in status[role][process]:
                        log.error("ERROR: minion {} did not respond for {}".format(minion, process))
                        ret = False
            for minion in status[role][process].keys():
                if status[role][process][minion] == '':
                    log.error("ERROR: process {} on {} for role {} is not running".format(process, minion, role))
                    ret = False
    return ret

def _status(processes, search):
    """
    Return a structure of roles with processes.

    Note: status.pid is chosen over service.status since the latter gives
    false positives.
    """
    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')


    status = {}
    local = salt.client.LocalClient()
    for role in processes.keys():
        status.setdefault(role, {})
        for process in processes[role]:
            role_search = search + " and I@roles:{}".format(role)
            status[role][process] = local.cmd(role_search,
                                    'status.pid',
                                    [ process ],
                                    expr_form="compound")

    logging.debug(pprint.pformat(status))

    sys.stdout = _stdout
    return status

def _cached_roles(search):
    """
    Return the cached roles in a convenient structure.  Trust the cached
    values from the master pillar since a downed minion will be absent 
    from any dynamic query.
    """
    pillar_util = salt.utils.master.MasterPillarUtil(search, "compound",
                                                     use_cached_grains=True,
                                                     grains_fallback=False,
                                                     opts=__opts__)

    cached = pillar_util.get_minion_pillar()
    expected = set(cached.keys())
    roles = {}
    for minion in cached.keys():
        if 'roles' in cached[minion]:
            for role in cached[minion]['roles']:
                roles.setdefault(role, []).append(minion)

    logging.debug(pprint.pformat(roles))
    return roles


def wait(**kwargs):
    """
    Periodically check until all services are up or until the timeout is
    reached.  Use a backoff for the delay to avoid filling logs.

    Note: state.orch does not obey return codes from runners last time I 
    checked.  Raising an exception is ugly but does stop the process.
    """
    settings = {
        'timeout': 900,
        'delay': 3
    }
    settings.update(kwargs)

    end_time = time.time() + settings['timeout']
    current_delay = settings['delay']
    while end_time > time.time():
        if check():
            log.debug("Services are up")
            return True
        time.sleep(settings['delay'])
        if current_delay < 60:
            current_delay += delay
        else:
            current_delay = 60
    log.error("Timeout expired")
    raise RuntimeError("Timeout expired")

