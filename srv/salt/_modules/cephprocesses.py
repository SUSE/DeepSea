# -*- coding: utf-8 -*-

import logging
import time

log = logging.getLogger(__name__)

"""
The original purpose of this runner is to verify that proceeding with an
upgrade is safe.  All expected services are running.

A secondary purpose is a utility to check the current state of all services.
"""


def check(**kwargs):
    """
    Query the status of running processes for each role.  Return False if any
    fail.
    """
    processes = {'mon': ['ceph-mon'],
                 'mgr': ['ceph-mgr'],
                 'storage': ['ceph-osd'],
                 'mds': ['ceph-mds'],
                 'igw': [],
                 'rgw': ['radosgw'],
                 'ganesha': ['ganesha.nfsd', 'rpcbind', 'rpc.statd'],
                 'admin': [],
                 'master': []}

    running = True
    results = {}

    if 'rgw_configurations' in __pillar__:
        for rgw_config in __pillar__['rgw_configurations']:
            processes[rgw_config] = ['radosgw']

    if 'roles' in __pillar__:
        for role in kwargs.get('roles', __pillar__['roles']):
            for process in processes[role]:
                pid = __salt__['status.pid'](process)
                if pid == '':
                    log.error("ERROR: process {} for role {} is not running".format(process, role))
                    running = False

    return running

def wait(**kwargs):
    """
    Periodically check until all services are up or until the timeout is
    reached.  Use a backoff for the delay to avoid filling logs.
    """
    settings = {
        'timeout': _timeout(),
        'delay': 3
    }
    settings.update(kwargs)

    end_time = time.time() + settings['timeout']
    current_delay = settings['delay']
    while end_time > time.time():
        if check():
            log.debug("Services are up")
            return True
        time.sleep(current_delay)
        if current_delay < 60:
            current_delay += settings['delay']
        else:
            current_delay = 60
    log.error("Timeout expired")
    return False


def _timeout():
    """
    Assume 15 minutes for physical hardware since some hardware has long
    shutdown/reboot times.  Assume 2 minutes for complete virtual environments.
    """
    if 'physical' == __grains__['virtual']:
        return 900
    else:
        return 120
