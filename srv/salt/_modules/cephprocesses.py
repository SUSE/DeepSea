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
             'igw': ['rbd-target-gw', 'rbd-target-api'],
             'rgw': ['radosgw'],
             'ganesha': ['ganesha.nfsd', 'rpcbind', 'rpc.statd'],
             'admin': [],
             'client-cephfs': [],
             'client-iscsi': [],
             'client-nfs': [],
             'client-radosgw': [],
             'benchmark-blockdev': [],
             'benchmark-rbd': [],
             'benchmark-fs': [],
             'prometheus': [],
             'grafana': ['grafana-server'],
             'master': []}

absent_processes = {}


# pylint: disable=too-few-public-methods
class SystemdUnit(object):
    """
    Class representation of the processes' systemd state
    """

    def __init__(self, proc_name=None, osd_id=None):
        self.proc_name = proc_name
        self._is_disabled = False
        self.osd_id = osd_id
        self.service_names = self._service_names()

    @property
    def is_disabled(self):
        """
        Reach out to systemctl and call is-enabled.
        Property for this state
        """
        if not self.service_names:
            return False

        for fsn in self.service_names:
            proc = Popen(shlex.split('systemctl is-enabled {}'.format(fsn)), stdout=PIPE)
            stdout, stderr = proc.communicate()
            if stderr:
                # pylint: disable=line-too-long
                log.error('Requesting the is-enabled flag from {} has resulted in {}'.format(fsn, stderr))
                return False
            try:
                status = stdout.decode('utf-8').strip()
            except AttributeError:
                log.error("Could not decode type-> {}".format(type(stdout)))
                status = ''
            if status == 'disabled':
                log.info("Found {} to be disabled".format(fsn))
                return True
            if status == 'enabled':
                log.info("Found {} to be enabled".format(fsn))
            else:
                log.info("Expected to get disabled/enabled but got {} instead".format(status))
        # Return False when no unit is 'disabled'
        return False

    def _service_names(self):
        """
        The construction of systemd unit names vary
        from service to service
        """
        service_names = []
        if self.osd_id and self.proc_name == 'ceph-osd':
            service_names = ["{}@{}".format(self.proc_name, self.osd_id)]
        if self.proc_name in ['ceph-mon', 'ceph-mgr', 'ceph-mds']:
            service_names = ["{}@{}".format(self.proc_name, __grains__['host'])]
        if self.proc_name == 'radosgw':
            service_names = ["{}@{}".format('ceph-radosgw', __grains__['host'])]
        if self.proc_name == 'ganesha.nfsd':
            service_names = ['nfs-ganesha', 'rpcbind']
        if self.proc_name == 'grafana':
            service_names = ['grafana-server']
        return service_names


# pylint: disable=too-many-instance-attributes, too-few-public-methods
class ProcInfo(object):
    """
    Maps processes to a helper class and tries to deduce
    the osd_ids from the process.
    """

    def __init__(self, proc):
        # the proc object
        self.proc = proc
        # e.g. python3, perl, etc
        self.exe = os.path.basename(proc.exe())
        # e.g. salt-call, ceph-osd
        self.name = proc.name()
        # e.g. systems pid
        self.pid = proc.pid
        # uid the proc is running under.
        self.uid = proc.uids().real
        # uid to name. (root, salt.. etc)
        self.uid_name = pwd.getpwuid(self.uid).pw_name
        if self.name == 'ceph-osd':
            self.osd_id = self._map_osd_proc_to_osd_id()
        else:
            self.osd_id = None
        if 'python' in self.exe:
            self.exe = self.name
        if self.proc.status() == 'running':
            self.up = False
        self._is_disabled = False

    def __repr__(self):
        """
        custom __repr__ to identify the class a bit easier while debugging
        """
        return "Process <{}>".format(self.name)

    def _map_osd_proc_to_osd_id(self):
        """
        Look into the commandline the process has been called
        with and extract the --id portion.
        """
        _id = self.proc.cmdline()[self.proc.cmdline().index('--id') + 1]
        if _id:
            return _id
        else:
            raise NoOSDIDFound


class NoOSDIDFound(Exception):
    """
    Custom Exception to raise when no OSD ID is found.
    """
    pass


class MetaCheck(object):
    """
    Class to handle checks of Processes
    """

    def __init__(self, **kwargs):
        self.up = list()
        self.down = list()
        self.running = True
        self.quiet = kwargs.get('quiet', False)
        self.insufficient_osd_count = False
        self.__blacklist = kwargs.get('blacklist', dict())

    @property
    def blacklist(self):
        """
        The blacklist gets sourced from kwargs.
        In our usecase we get the data from the salt-master
        as a central place to annotate blacklisted OSDs
        The current implementation only allows OSDs.
        """
        if self.__blacklist:
            return self.__blacklist
        return __salt__['pillar.get']('blacklist')

    @blacklist.setter
    def blacklist(self, bl):
        """
        For testing purposes
        """
        self.__blacklist = bl

    @property
    def expected_osds(self):
        """
        Return the expected OSDs ( Minus the blacklisted )
        """
        blacklisted_osds = []
        blacklist = self.blacklist
        if 'ceph-osd' in blacklist:
            if blacklist['ceph-osd']:
                blacklisted_osds = [str(x) for x in blacklist['ceph-osd']]
                log.warning("You configured OSDs to be blacklisted. {}".format(blacklisted_osds))
        return list(set(__salt__['osd.list']()) - set(blacklisted_osds))

    def filter_for(self, prc_name):
        """
        utils method to filter for process names
        """
        return [x for x in self.up if x.exe == prc_name]

    def add(self, prc, role):
        """
        Add a role to the self.up list if it's process is found
        in the process dict.
        """
        if prc.exe in processes[role] or prc.name in processes[role]:
            self.up.append(prc)

    def check_inverts(self, role):
        """
        Running indicates whether the service is in its expected state
        while here the logic is inverted.
        If the process is considered 'running' it means that it has not
        finished yet and is still 'working'
        """
        if role in absent_processes.keys():
            for proc in absent_processes[role]:
                if proc in [prc.name for prc in self.up]:
                    self.running = False
                    # pylint: disable=line-too-long
                    log.error("ERROR: process {} for role {} is pending(working)".format(proc, role))

    def check_absents(self, role):
        """
        If found processes are not in the list of required
        processes, set running to False and mark as down
        """
        for proc in processes[role]:
            if proc not in [prc.name for prc in self.up]:
                if not self.quiet:
                    # pylint: disable=line-too-long
                    log.error("ERROR: process {} for role {} is not running".format(proc, role))
                self.running = False
                self.down.append(proc)

    @property
    def _up_osds(self):
        """
        Property that returns a str(osd_id) of filtered ceph-osd processes
        """
        return [str(x.osd_id) for x in self.filter_for('ceph-osd')]

    @property
    def _missing_osds(self):
        """
        Property that returns the diff between expected and up osds
        """
        return list(set(self.expected_osds) - set(self._up_osds))

    def _insufficient_osd_count(self):
        """
        Check if the sufficient number of OSDs are up
        """
        if len(self.expected_osds) > len(self._up_osds):
            if not self.quiet:
                # pylint: disable=line-too-long
                log.error("{} OSDs not running: {}".format(len(self._missing_osds), self._missing_osds))
                log.error("Found less OSDs then expected. Expected {} | Found {}".format(len(self.expected_osds), len(self._up_osds)))
            self.insufficient_osd_count = True
        else:
            self.insufficient_osd_count = False

    def check_osds(self):
        """
        Check the count of OSDs
        """
        self._insufficient_osd_count()
        if self.filter_for('ceph-osd'):
            if self.insufficient_osd_count:
                self.running = False

    def report(self):
        """
        Format the structures so that salt understands it

        {'up':   {'ceph-osd': [1,2,3],
                  'ceph-mon': [1]
                 },
         'down': {'ceph-osd': [4]
                 }
        }
        In the down->ceph-osd case, the key describes the
        osd_id which is down as opposed to the up->ceph-osd
        where the key describes the process id.
        """
        res = {'up': {}, 'down': {}}
        # initialize
        for proc in self.up:
            res['up'][proc.exe] = list()
        for proc in self.down:
            # We only consider down/enabled as abort condition
            if not SystemdUnit(proc_name=proc).is_disabled:
                res['down'][proc] = proc

        for proc in self.up:
            # We are checking if a systemd-unit is up,
            # but not if it is disabled. maybe we should?
            res['up'][proc.exe].append(proc.pid)
        if self.insufficient_osd_count:
            for missing_osd in self._missing_osds:
                if not SystemdUnit(proc_name='ceph-osd', osd_id=missing_osd).is_disabled:
                    res['down']['ceph-osd'] = self._missing_osds
        return res


def _extend_processes():
    """
    Extend the processes by rgw_configurations
    """
    if 'rgw_configurations' in __pillar__:
        for rgw_config in __pillar__['rgw_configurations']:
            processes[rgw_config] = ['radosgw']


def check(results=False, **kwargs):

    """
    Query the status of running processes for each role.  Return False if any
    fail.  If results flag is set, return a dictionary of the form:
      { 'down': [ process, ... ], 'up': { process: [ pid, ... ], ...} }
    """
    _extend_processes()
    res = MetaCheck(**kwargs)

    if 'roles' not in __pillar__:
        log.error("Did not find _roles_ in pillar. Aborting")
        return False
    for role in kwargs.get('roles', __pillar__['roles']):
        for running_proc in psutil.process_iter():
            res.add(ProcInfo(running_proc), role)
        res.check_inverts(role)
        res.check_absents(role)
        if role == 'storage':
            res.check_osds()

    return res.report() if results else res.running


def down():
    """
    Based on check(), return True/False if all Ceph processes that are meant
    to be running on a node are down.
    """
    return True if not list(check(True)['up'].values()) else False


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


def need_restart_lsof(role=None):
    """
    Use the process map to determine if a service restart is required.
    """
    assert role
    lsof_proc_map = _process_map()
    proc_map = zypper_ps(role, lsof_proc_map)
    for proc in proc_map:
        if proc['name'] in processes[role]:
            log.info("Found deleted file for ceph service: {} -> Queuing a restart".format(role))
            return True
    return False


def need_restart_config_change(role=None):
    """
    Check for a roles restart grain, i.e. is a restart required due to a config
    change.
    """
    assert role
    grain_name = "restart_{}".format(role)
    if grain_name in __grains__ and __grains__[grain_name]:
        log.debug("Found {}: True in the grains.".format(grain_name))
        return True
    return False


def need_restart(role=None):
    """
    Condensed call for lsof and config change
    TODO: Theoretically you can make config changes for individual
          OSDs. We currently do not support that.
    """
    assert role
    if need_restart_config_change(role=role) or need_restart_lsof(role=role):
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
