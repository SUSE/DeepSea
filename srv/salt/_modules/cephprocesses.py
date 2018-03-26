# -*- coding: utf-8 -*-

"""
Operations for Ceph processes to roles
"""

from __future__ import absolute_import
import logging
import time
import os
import pwd
import shlex
# pylint: disable=import-error,3rd-party-module-not-gated
from subprocess import Popen, PIPE
import psutil


log = logging.getLogger(__name__)

"""
The original purpose of this runner is to verify that proceeding with an
upgrade is safe.  All expected services are running.

A secondary purpose is a utility to check the current state of all services.
"""

# pylint: disable=invalid-name
processes = {'mon': ['ceph-mon'],
             'mgr': ['ceph-mgr'],
             'storage': ['ceph-osd'],
             'mds': ['ceph-mds'],
             'igw': ['lrbd'],
             'rgw': ['radosgw'],
             'ganesha': ['ganesha.nfsd', 'rpcbind', 'rpc.statd'],
             'admin': [],
             'openattic': ['httpd-prefork'],
             'client-cephfs': [],
             'client-iscsi': [],
             'client-nfs': [],
             'client-radosgw': [],
             'benchmark-blockdev': [],
             'benchmark-fs': [],
             'master': []}

# Processes like lrbd have an inverted logic
# if they are running it means that the service is _NOT_ ready
# as opposed to the the services in the 'processes' map.
absent_processes = {'igw': ['lrbd']}


def check(results=False, quiet=False, **kwargs):

    """
    Query the status of running processes for each role.  Return False if any
    fail.  If results flag is set, return a dictionary of the form:
      { 'down': [ process, ... ], 'up': { process: [ pid, ... ], ...} }
    """
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
                pdict_name = pdict['name']
                pdict_pid = pdict['pid']
                # Convert the numerical UID to name.
                pdict_uid = pwd.getpwuid(pdict['uids'].real).pw_name
                if pdict_exe in processes[role] or pdict_name in processes[role]:
                    # When we don't have a binary but a python program
                    # we want to use it's name for the 'exe'
                    # Example:
                    # pdict_exe for a lrbd is '/usr/bin/python2.7'
                    # pdict['name'] is the actual name of the .py file to be executed
                    if 'python' in pdict_exe:
                        pdict_exe = pdict_name
                    # Verify httpd-worker pid belongs to openattic.
                    if (role != 'openattic') or (role == 'openattic' and pdict_uid == 'openattic'):
                        if pdict_exe in res['up']:
                            res['up'][pdict_exe] = res['up'][pdict_exe] + [pdict_pid]
                        else:
                            res['up'][pdict_exe] = [pdict_pid]

            if role in absent_processes.keys():
                for proc in absent_processes[role]:
                    if proc in res['up']:
                        # running is deceptive here
                        # running indicates wheter the service is in it's expected state
                        running = False
                        # pylint: disable=line-too-long
                        log.error("ERROR: process {} for role {} is pending(working)".format(proc, role))
            else:
                for proc in processes[role]:
                    if proc not in res['up']:
                        if not quiet:
                            # pylint: disable=line-too-long
                            log.error("ERROR: process {} for role {} is not running".format(proc, role))
                        running = False
                        res['down'] += [proc]

            # pylint: disable=fixme
            # FIXME: Map osd.ids to processes.pid to improve qualitify of logging
            # currently you can only say how many osds/ if any are down, but not
            # which osd is down exactly.
            if role == 'storage':
                if 'ceph-osd' in res['up']:
                    if len(__salt__['osd.list']()) > len(res['up']['ceph-osd']):
                        if not quiet:
                            log.error("ERROR: At least one OSD is not running")
                        res = {'up': {}, 'down': {'ceph-osd': 'ceph-osd'}}
                        running = False

    return res if results else running


# pylint: disable=unused-argument
def down(**kwargs):
    """
    Based on check(), return True/False if all Ceph processes that are meant
    to be running on a node are down.
    """
    return True if not list(check(True, True)['up'].values()) else False


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
        if check(**kwargs):
            log.debug("Services are up")
            return True
        time.sleep(current_delay)
        if current_delay < 60:
            current_delay += settings['delay']
        else:
            current_delay = 60
    log.error("Timeout expired")
    return False


def _process_map():
    """
    Create a map of processes that have deleted files.
    """
    procs = []
    proc1 = Popen(shlex.split('lsof '), stdout=PIPE)
    # pylint: disable=line-too-long
    proc2 = Popen(shlex.split("awk 'BEGIN {IGNORECASE = 1} /deleted/ {print $1 \" \" $2 \" \" $4}'"),
                  stdin=proc1.stdout, stdout=PIPE, stderr=PIPE)
    proc1.stdout.close()
    stdout, _ = proc2.communicate()
    stdout = __salt__['helper.convert_out'](stdout)
    for proc_l in stdout.split('\n'):
        proc = proc_l.split(' ')
        proc_info = {}
        if proc[0] and proc[1] and proc[2]:
            proc_info['name'] = proc[0]
            if proc_info['name'] == 'httpd-pre':
                # lsof 'nicely' abbreviates httpd-prefork to httpd-pre
                proc_info['name'] = 'httpd-prefork'
            proc_info['pid'] = proc[1]
            proc_info['user'] = proc[2]
            procs.append(proc_info)
        else:
            continue
    return procs


def zypper_ps(role, lsof_map):
    """
    Gets services that need a restart from zypper
    """
    assert role
    proc1 = Popen(shlex.split('zypper ps -sss'), stdout=PIPE)
    stdout, _ = proc1.communicate()
    stdout = __salt__['helper.convert_out'](stdout)
    processes_ = processes
    # adding instead of overwriting, eh?
    # radosgw is ceph-radosgw in zypper ps.
    processes_['rgw'] = ['ceph-radosgw', 'radosgw', 'rgw']
    # ganesha is called nfs-ganesha
    processes_['ganesha'] = ['ganesha.nfsd', 'rpcbind', 'rpc.statd', 'nfs-ganesha']
    for proc_l in stdout.split('\n'):
        if '@' in proc_l:
            proc_l = proc_l.split('@')[0]
        if proc_l in processes_[role]:
            lsof_map.append({'name': proc_l})
    return lsof_map


def restart_required_lsof(role=None):
    """
    Use the process map to determine if a service restart is required.
    """
    assert role
    lsof_proc_map = _process_map()
    proc_map = zypper_ps(role, lsof_proc_map)
    for proc in proc_map:
        if proc['name'] in processes[role]:
            if role == 'openattic' and proc['user'] != 'openattic':
                continue
            log.info("Found deleted file for ceph service: {} -> Queuing a restart".format(role))
            return True
    return False


def need_restart(role=None):
    """
    Condensed call for lsof and config change
    TODO: Theoretically you can make config changes for individual
          OSDs. We currently do not support that.
    """
    assert role
    grain_name = "restart_{}".format(role)
    if grain_name not in __grains__:
        log.debug("There is no {} in the grains.".format(grain_name))
        __grains__[grain_name] = False
    if __grains__[grain_name] or restart_required_lsof(role=role):
        log.info("Restarting ceph service: {} -> Queuing a restart".format(role))
        return True
    return False


def _timeout():
    """
    Assume 15 minutes for physical hardware since some hardware has long
    shutdown/reboot times.  Assume 2 minutes for complete virtual environments.
    """
    if __grains__['virtual'] == 'physical':
        return 900
    return 120
