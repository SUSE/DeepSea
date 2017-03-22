# -*- coding: utf-8 -*-

import logging
import time

log = logging.getLogger(__name__)

"""
The original purpose of this runner is to verify that proceeding with an
upgrade is safe.  All expected services are running.

A secondary purpose is a utility to check the current state of all services.
"""

def check(only_for=[]):
    """
    Query the status of running processes for each role.  Return False if any
    fail.
    """
    processes = { 'mon': [ 'ceph-mon' ],
                 'storage': [ 'ceph-osd' ],
                 'mds': [ 'ceph-mds' ],
                 'igw': [ 'lrbd' ],
                 'rgw': [ 'radosgw' ],
                 'ganesha': [ 'ganesha.nfsd', 'rpcbind', 'rpc.statd' ] }

    ret = True
    if 'roles' in __pillar__:
        if only_for:
          for role in only_for:
            log.info("Checking {} for status".format(role)
            for process in processes[role]:
	      result = __salt__['status.pid'](process)
              if result == '':
                log.error("ERROR: process {} for role {} is not running".format(process, role))
                ret = False
        else:
          for role in __pillar__['roles']:
              if role in processes:
                  for process in processes[role]:
                      result = __salt__['status.pid'](process)
                      print "ON ROLE: {}".format(role)
                      print "RESULT: {}".format(result)
                      if result == '':
                          log.error("ERROR: process {} for role {} is not running".format(process, role))
                          ret = False

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
