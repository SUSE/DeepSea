# -*- coding: utf-8 -*-
"""
Operations for Ceph processes to roles
"""

from __future__ import absolute_import
import logging
import time
import os
import pwd
# pylint: disable=import-error,3rd-party-module-not-gated
import psutil

log = logging.getLogger(__name__)

"""
The original purpose of this runner is to verify that proceeding with an
upgrade is safe.  All expected services are running.

A secondary purpose is a utility to check the current state of all services.
"""


def check(results=False, quiet=False, **kwargs):
    """
    Query the status of running processes for each role.  Return False if any
    fail.  If results flag is set, return a dictionary of the form:
      { 'down': [ process, ... ], 'up': { process: [ pid, ... ], ...} }
    """
    processes = {'mon': ['ceph-mon'],
                 'mgr': ['ceph-mgr'],
                 'storage': ['ceph-osd'],
                 'mds': ['ceph-mds'],
                 'igw': [],
                 'rgw': ['radosgw'],
                 'ganesha': ['ganesha.nfsd', 'rpcbind', 'rpc.statd'],
                 'admin': [],
                 'openattic': ['httpd-prefork'],
                 'master': []}

    running = True
    res = {'up': {}, 'down': []}

    if 'rgw_configurations' in __pillar__:
        for rgw_config in __pillar__['rgw_configurations']:
            processes[rgw_config] = ['radosgw']

    # pylint: disable=too-many-nested-blocks
    if 'roles' in __pillar__:
        for role in kwargs.get('roles', __pillar__['roles']):
            # Checking running first.
            for running_proc in psutil.process_iter():
                # NOTE about `ps` and psutils.Process():
                # `ps -e` determines process names by examining
                # /proc/PID/stat,status files.  The name derived
                # there is also found in psutil.Process.name.
                # `ps -ef`, according to strace, appears to also reference
                # /proc/PID/cmdline when determining
                # process names.  We have found that some processes (ie.
                # ceph-mgr was noted) will _sometimes_
                # contain a process name in /proc/PIDstat/stat,status that does
                # not match that found in /proc/PID/cmdline.
                # In our ceph-mgr example, the process name was found to be
                # 'exe' (which happens to also be the name a of
                # symlink in /proc/PID that points to the executable) while the
                # cmdline entry contained 'ceph-mgr' etc.
                # As such, we've decided that a check based on executable
                # path is more reliable.
                pdict = running_proc.as_dict(attrs=['pid', 'name', 'exe', 'uids'])
                pdict_exe = os.path.basename(pdict['exe'])
                pdict_pid = pdict['pid']
                # Convert the numerical UID to name.
                pdict_uid = pwd.getpwuid(pdict['uids'].real).pw_name
                if pdict_exe in processes[role]:
                    # Verify httpd-worker pid belongs to openattic.
                    if (role != 'openattic') or (role == 'openattic' and pdict_uid == 'openattic'):
                        if pdict_exe in res['up']:
                            res['up'][pdict_exe] = res['up'][pdict_exe] + [pdict_pid]
                        else:
                            res['up'][pdict_exe] = [pdict_pid]

            # Any processes for this role that aren't running, mark them down.
            for proc in processes[role]:
                if proc not in res['up']:
                    if not quiet:
                        log.error("ERROR: process {} for role {} is not running".format(proc, role))
                    running = False
                    res['down'] += [proc]

    return res if results else running


# pylint: disable=unused-argument
def down(**kwargs):
    """
    Based on check(), return True/False if all Ceph processes that are meant
    to be running on a node are down.
    """
    return True if not check(True, True)['up'].values() else False


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
    if __grains__['virtual'] == 'physical':
        return 900
    else:
        return 120
