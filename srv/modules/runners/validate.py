#!/usr/bin/python

import salt.client
import salt.utils.error
import logging
import ipaddress
import pprint
import yaml
import os
import re
from subprocess import call, Popen, PIPE
from os.path import dirname

from collections import OrderedDict

log = logging.getLogger(__name__)

# Next items
#
# monitors require admin roles
# make time_server optional
# 

"""
For Ceph, the generation of ceph.conf requires additional information.
Although this information can be determined from Salt itself, the 
prerequisite is monitor assignment. This step is more of a post configuration
before deployment.

Eventually, root assignment within the crushmap may live here.  The similar
prerequisite is that osd assignment must be decided before segregating types
of hardware.
"""

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SaltOptions(object):
    """
    Keep the querying of salt options separate 
    """

    def __init__(self):
        """
        Capture __opts__ and stack_dir
        """
        self.__opts__ = salt.config.client_config('/etc/salt/master')
        for ext in self.__opts__['ext_pillar']:
            if 'stack' in ext:
                self.stack_dir = dirname(ext['stack'])

class ClusterAssignment(object):
    """
    Discover the cluster assignment and ignore unassigned
    """

    def __init__(self, local):
        """
        Query the cluster assignment and remove unassigned
        """
        self.minions = local.cmd('*' , 'pillar.get', [ 'cluster' ])

        self.names = dict(self._clusters())
        if 'unassigned' in self.names:
            self.names.pop('unassigned')
        

    def _clusters(self):
        """
        Create a dictionary of cluster to minions
        """
        clusters = {}
        for minion in self.minions.keys():
            cluster = self.minions[minion]
            if not cluster in clusters:
                clusters[cluster] = []
            clusters[cluster].extend([ minion ])
        return clusters
    
class Validate(object):
    """
    Perform checks on pillar data
    """

    def __init__(self, name, data, grains):
        """
        Query the cluster assignment and remove unassigned
        """
        self.name = name
        self.data = data
        self.grains = grains
        self.passed = OrderedDict()
        self.errors = OrderedDict()

    def fsid(self):
        """
        Validate fsid from first entry
        """
        fsid = self.data[self.data.keys()[0]]['fsid']
        log.debug("fsid: {}".format(fsid))
        if 'fsid':
            if len(fsid) == 36:
                # More specific regex?
                if re.match(r'\w+-\w+-\w+-\w+-\w+', fsid):
                    self.passed['fsid'] = "valid"
                else:
                    msg = "{} does not appear to be a UUID".format(fsid)
                    self.errors['fsid'] = [ msg ]

            else:
                msg = "{} has {} characters, not 36".format(fsid, len(fsid))
                self.errors['fsid'] = [ msg ]
        else:
            stack_dir = "/srv/pillar/ceph/stack"
            cluster_yml = "{}/cluster.yml".format(self.name)
            
            msg = ( "fsid is not defined.  "
                    "Check {0}/{1} and {0}/default/{1}".
                    format(stack_dir, cluster_yml))
            self.errors['fsid'] = [ msg ]

    def public_network(self):
        """
        All nodes must have the same public network.  The public network
        must be valid.
        """
        same_network = {}
        for node in self.data.keys():
            log.debug("public_network: {} {}".format(node, self.data[node]['public_network']))
            same_network[self.data[node]['public_network']] = ""
            try:
                ipaddress.ip_network(u'{}'.format(self.data[node]['public_network']))
            except ValueError as err:
                msg = "{} on {} is not valid".format(self.data[node]['public_network'], node)
                if 'public_network' in self.errors:
                    self.errors['public_network'].append(msg)
                else:
                    self.errors['public_network'] = [ msg ]
        if len(same_network.keys()) > 1:
            msg = "Different public networks {}".format(same_network.keys())
            if 'public_network' in self.errors:
                self.errors['public_network'].append(msg)
            else:
                self.errors['public_network'] = [ msg ]
        if not 'public_network' in self.errors:
            self.passed['public_network'] = "valid"

    def public_interface(self):
        """
        """
        for node in self.data.keys():
            if ('roles' in self.data[node] and 
                'master' in self.data[node]['roles']):
                continue
            found = False
            for address in self.grains[node]['ipv4']:
                if ipaddress.ip_address(u'{}'.format(address)) in ipaddress.ip_network(u'{}'.format(self.data[node]['public_network'])):
                    found = True
            if not found:
                msg = "minion {} missing address on public network {}".format(node, self.data[node]['public_network'])
                if 'public_interface' in self.errors:
                    self.errors['public_interface'].append(msg)
                else:
                    self.errors['public_interface'] = [ msg ]
        if not 'public_interface' in self.errors:
            self.passed['public_interface'] = "valid"

    def monitors(self):
        """
        At least three nodes must have the monitor role
        """
        monitors = []
        for node in self.data.keys():
            if ('roles' in self.data[node] and 
                'mon' in self.data[node]['roles']):
                monitors.append(node)

        if len(monitors) < 3:
            msg = "Too few monitors {}".format(",".join(monitors))
            self.errors['monitors'] = [ msg ]
        else:
            self.passed['monitors'] = "valid"

    def storage(self):
        """
        At least four nodes must have the storage role.  All storage nodes
        must have a storage attribute.
        """
        storage = []
        missing = []
        for node in self.data.keys():
            if ('roles' in self.data[node] and 
                'storage' in self.data[node]['roles']):
                storage.append(node)
                if not 'storage' in self.data[node]:
                    missing.append(node)

        if len(storage) < 4:
            msg = "Too few storage nodes {}".format(",".join(storage))
            self.errors['storage'] = [ msg ]
        else:
            if missing:
                stack_dir = "/srv/pillar/ceph/stack"
                minion_yml = "{}/minions/*.yml".format(self.name)
                err = "Storage nodes {} missing storage attribute.  ".format(",".join(storage))
                check = "Check {0}/{1} and {0}/default/{1}".format(stack_dir, minion_yml)
                self.errors['storage'] = [ err + check ]
            else:
                self.passed['storage'] = "valid"

    def cluster_network(self):
        """
        All storage nodes must have the same cluster network.  The cluster
        network must be valid.
        """
        same_network = {}
        for node in self.data.keys():
            if ('roles' in self.data[node] and 
                'storage' in self.data[node]['roles']):

                log.debug("cluster_network: {} {}".format(node, self.data[node]['cluster_network']))
                same_network[self.data[node]['cluster_network']] = ""
                try:
                    ipaddress.ip_network(u'{}'.format(self.data[node]['cluster_network']))
                except ValueError as err:
                    msg = "{} on {} is not valid".format(self.data[node]['cluster_network'], node)
                    if 'cluster_network' in self.errors:
                        self.errors['cluster_network'].append(msg)
                    else:
                        self.errors['cluster_network'] = [ msg ]
        if len(same_network.keys()) > 1:
            msg = "Different cluster networks {}".format(same_network.keys())
            if 'cluster_network' in self.errors:
                self.errors['cluster_network'].append(msg)
            else:
                self.errors['cluster_network'] = [ msg ]
        if not 'cluster_network' in self.errors:
            self.passed['cluster_network'] = "valid"

    def cluster_interface(self):
        """
        """
        for node in self.data.keys():
            if ('roles' in self.data[node] and 
                'storage' in self.data[node]['roles']):
                found = False
                for address in self.grains[node]['ipv4']:
                    if ipaddress.ip_address(u'{}'.format(address)) in ipaddress.ip_network(u'{}'.format(self.data[node]['cluster_network'])):
                        found = True
                if not found:
                    msg = "minion {} missing address on cluster network {}".format(node, self.data[node]['cluster_network'])
                    if 'cluster_interface' in self.errors:
                        self.errors['cluster_interface'].append(msg)
                    else:
                        self.errors['cluster_interface'] = [ msg ]
        if not 'cluster_interface' in self.errors:
            self.passed['cluster_interface'] = "valid"

    def _check_keyring(self, name, role = None):
        """
        Check for a matching role and keyring.
        """
        if role:
            _role = role
        else:
            _role = name

        _keyring = "{}_keyring".format(name) 
        for node in self.data.keys():
            if ('roles' in self.data[node] and 
                _role in self.data[node]['roles']):
                if 'keyring' in self.data[node]:
                    for entry in self.data[node]['keyring']:
                        if name in entry:
                            keyring = entry[name]
                            size = len(keyring)
                            if size == 40:
                                pass
                            else:
                                msg = "keyring is {} characters, not 40".format(size)
                                if _keyring in self.errors:
                                    self.errors[_keyring].append(msg)
                                else:
                                    self.errors[_keyring] = [ msg ]
                else:
                    msg = "{} keyring is missing on {}.  ".format(name, node)
                    stack_dir = "/srv/pillar/ceph/stack"
                    keyring_yml = "{}/roles/{}.yml".format(self.name, name)
                    check = "Check {0}/{1} and {0}/default/{1}".format(stack_dir, keyring_yml)
                    if _keyring in self.errors:
                        self.errors[_keyring].append(msg + check)
                    else:
                        self.errors[_keyring] = [ msg + check ]
        
        if not _keyring in self.errors:
            self.passed[_keyring] = "valid"


    def admin_keyring(self):
        """
        The admin role requires an admin keyring
        """
        self._check_keyring('mon')

    def mon_keyring(self):
        """
        The mon role requires an mon keyring
        """
        self._check_keyring('mon')

    def osd_keyring(self):
        """
        The storage role requires an osd keyring
        """
        self._check_keyring('osd', 'storage')

    def mds_keyring(self):
        """
        The mds role requires an mds keyring
        """
        self._check_keyring('mds')

    def rgw_keyring(self):
        """
        The rgw role requires an rgw keyring
        """
        self._check_keyring('rgw')

    def _monitor_check(self, name):
        """
        """
        same_hosts = {}
        for node in self.data.keys():
            if name in self.data[node]:
                same_hosts[",".join(self.data[node][name])] = ""
            else:
                msg = "host {} is missing {}".format(node, name)
                if name in self.errors:
                    self.errors[name].append(msg)
                else:
                    self.errors[name] = [ msg ]

        if len(same_hosts.keys()) > 1:
            msg = "Different entries {}".format(same_hosts.keys())
            if name in self.errors:
                self.errors[name].append(msg)
            else:
                self.errors[name] = [ msg ]
        elif same_hosts:
            count = len(same_hosts.keys()[0].split(","))
            if count < 3:
                msg = "Must have at least three entries"
                self.errors[name] = [ msg ]
        else:
            msg = "Missing {}".format(name)
            self.errors[name] = [ msg ]

        if not name in self.errors:
            self.passed[name] = "valid"

    def master_role(self):
        """
        The master role has keyrings
        """
        for node in self.data.keys():
            if 'roles' in self.data[node] and 'master' in self.data[node]['roles']:
                if 'keyring' not in self.data[node]:
                    msg = "master role missing keyrings on {}, check /srv/pillar/ceph/proposals/policy.cfg for master.yml".format(node)
                    self.errors['master_role'] = [ msg ]

        if not 'master_role' in self.errors:
            self.passed['master_role'] = "valid"


    def mon_role(self):
        """
        The monitors also need the admin role
        """
        for node in self.data.keys():
            if 'roles' in self.data[node] and 'mon' in self.data[node]['roles']:
                if 'admin' not in self.data[node]['roles']:
                  msg = "host {} is a monitor and missing admin role".format(node)
                  if 'mon_role' in self.errors:
                      self.errors['mon_role'].append(msg) 
                  else:
                      self.errors['mon_role'] = [ msg ]

        if not 'mon_role' in self.errors:
            self.passed['mon_role'] = "valid"

    def mon_host(self):
        """
        The mon_host must be the same on all nodes and have at least
        three entries.
        """
        self._monitor_check('mon_host')

    def mon_initial_members(self):
        """
        The mon_initial_members must be the same on all nodes and have at least
        three entries.
        """
        self._monitor_check('mon_initial_members')

    def _redirection_check(self, name):
        """
        """
        attr = "{}_creation".format(name)
        for node in self.data.keys():
            if attr in self.data[node]:
                ceph_dir = "/srv/salt/ceph"
                filename = "{}/{}/{}.sls".format(ceph_dir, name, self.data[node][attr])
                if os.path.isfile(filename):
                    self.passed[attr] = "valid"
                else:
                    msg = "No such state file {}".format(filename)
                    self.errors[attr] = [ msg ]


    def osd_creation(self):
        """
        The value of osd_creation must match a state file
        """
        self._redirection_check('osd')
    
    def pool_creation(self):
        """
        The value of pool_creation must match a state file
        """
        self._redirection_check('pool')
    
    def _popen(self, cmd):
        """
        """
        stdout = []
        stderr = []
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        for line in proc.stdout:
            stdout.append(line.rstrip('\n'))
        for line in proc.stderr:
            stderr.append(line.rstrip('\n'))
        proc.wait()
        return (stdout, stderr)

    def _ntp_check(self, server):
        """
        """
        result = self._popen([ '/usr/sbin/sntp', '-t', '1', server ])
        for line in result[0]:
            if re.search(r'{}'.format(server), line):
                if re.search(r'no.*response', line):
                    msg = line
                    self.errors['time_server'] = [ msg ]


    def _ping_check(self, server):
        """
        """
        result = self._popen([ '/usr/bin/ping', '-c', '1', server ])
        for line in result[0]:
            if re.match(r'\d+ bytes from', line):
                self.passed['time_server'] = "valid"
        if not 'time_server' in self.passed:
            if result[1]:
                # Take stderr
                self.errors['time_server'] = result[1]
            elif result[0][1]:
                # Take second line of stdout
                self.errors['time_server'] = [ result[0][1] ]
            else:
                # how did we get here?
                msg = "{} unavailable".format(server)
                self.errors['time_server'] = [ msg ]
 

    def time_server(self):
        """
        Check that time server is available
        """
        time_server = self.data[self.data.keys()[0]]['time_server']
        time_service = self.data[self.data.keys()[0]]['time_service']
        if time_service == 'disabled':
            self.passed['time_server'] = "disabled"
            return

        if (time_service == 'ntp' and os.path.isfile('/usr/sbin/sntp')):
            self._ntp_check(time_server)
        else:
            self._ping_check(time_server)

        if not 'time_server' in self.errors:
            self.passed['time_server'] = "valid"

    def report(self):
        """
        """
        # Need to make colors optional, but looks better currently
        for attr in self.passed.keys():
            print "{:25}: {}{}{}{}".format(attr, bcolors.BOLD, bcolors.OKGREEN, self.passed[attr], bcolors.ENDC)
        for attr in self.errors.keys():
            print "{:25}: {}{}{}{}".format(attr, bcolors.BOLD, bcolors.FAIL, self.errors[attr], bcolors.ENDC)

def usage():
    print "salt-run validate.pillar cluster"
    print "salt-run validate.pillar name=cluster"
    print "salt-run validate.pillars"


def pillars(**kwargs):
    """
    """
    #options = SaltOptions()
    local = salt.client.LocalClient()
    cluster = ClusterAssignment(local)

    for name in cluster.names:
        pillar(name, **kwargs)


def pillar(name = None, **kwargs):
    """
    Check that the pillar for each cluster meets the requirements to install
    a Ceph cluster.
    """

    if name == None:
        if 'name' in kwargs:
            name = kwargs['name']

    if not name:
        usage()
        exit(1)

    #options = SaltOptions()
    local = salt.client.LocalClient()

    # Restrict search to this cluster
    search = "I@cluster:{}".format(name)

    pillar_data = local.cmd(search , 'pillar.items', [], expr_form="compound")
    grains_data = local.cmd(search , 'grains.items', [], expr_form="compound")
    
    v = Validate(name, pillar_data, grains_data)
    v.fsid()
    v.public_network()
    v.public_interface()
    v.cluster_network()
    v.cluster_interface()
    v.monitors()
    v.storage()
    v.admin_keyring()
    v.mon_keyring()
    v.mds_keyring()
    v.rgw_keyring()
    v.osd_keyring()
    v.master_role()
    v.mon_role()
    v.mon_host()
    v.mon_initial_members()
    v.osd_creation()
    v.pool_creation()
    v.time_server()
    v.report()

    if v.errors:
        return False

    return True
