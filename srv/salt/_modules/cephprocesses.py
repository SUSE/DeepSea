# -*- coding: utf-8 -*-

import logging
import time

log = logging.getLogger(__name__)

"""
The original purpose of this runner is to verify that proceeding with an
upgrade is safe.  All expected services are running.

A secondary purpose is a utility to check the current state of all services.
"""

def check(roles=[]):
    """
    Query the status of running processes for each role.  Return False if any
    fail.
    """
    processes = {'mon': ['ceph-mon'],
                 'storage': ['ceph-osd'],
                 'mds': ['ceph-mds'],
                 'igw': ['lrbd'],
                 'rgw': ['radosgw'],
                 'ganesha': ['ganesha.nfsd', 'rpcbind', 'rpc.statd']}

    ret = True

    def check_process(role):
        for process in processes[role]:
            pid = __salt__['status.pid'](process)
            log.info("Pid for process {} is {}".format(process, result))
            if not pid.isdigit():
                log.error("ERROR: process {} for role {} is not running".format(process, role))
                return False
            else:
                return True

    ignore_roles = [ 'admin', 'master' ]

    for ig_role in ignore_roles:
      if ig_role in roles:
        roles.pop(ig_role)

    if 'roles' in __pillar__:
        for role in __pillar__['roles']:
            # custom roles are used
            if roles:
                if role in roles:
                    ret = check_process(role)
            # use all available roles from pillar
            else:
                ret = check_process(role)

    return ret

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
    if 'physical' ==  __grains__['virtual']:
        return 900
    else:
        return 120
