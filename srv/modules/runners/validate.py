#!/usr/bin/python

import salt.client
import salt.utils.error
import logging
import ipaddress
import pprint
import json
import yaml
import os
import re
import sys
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
    
class PrettyPrinter:
    
    def add(self, name, passed, errors):
        # Need to make colors optional, but looks better currently
        for attr in passed.keys():
            print "{:25}: {}{}{}{}".format(attr, bcolors.BOLD, bcolors.OKGREEN, passed[attr], bcolors.ENDC)
        for attr in errors.keys():
            print "{:25}: {}{}{}{}".format(attr, bcolors.BOLD, bcolors.FAIL, errors[attr], bcolors.ENDC)
            
    def print_result(self):
        pass
            
class JsonPrinter:
    
    def __init__(self):
        self.result = {}
    
    def add(self, name, passed, errors):
        self.result[name] = {'passed': passed, 'errors': errors}
            
    def print_result(self):
        json.dump(self.result, sys.stdout)
        
def get_printer(__pub_output=None, **kwargs):
    return JsonPrinter() if __pub_output in ['json', 'quiet'] else PrettyPrinter()
    


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
    Perform checks on pillar and grain data
    """

    def __init__(self, name, data, grains, printer):
        """
        Query the cluster assignment and remove unassigned
        """
        self.name = name
        self.data = data
        self.grains = grains
        self.printer = printer
        self.passed = OrderedDict()
        self.errors = OrderedDict()

        self._minion_check()

    def _minion_check(self):
        """
        """
        if not self.data:
            log.error("No minions responded")
            os._exit(1)

    def fsid(self):
        """
        Validate fsid from first entry
        """
        fsid = self.data[self.data.keys()[0]].get("fsid", "")
        log.debug("fsid: {}".format(fsid))
        if fsid:
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
            public_network = self.data[node].get("public_network", "")
            log.debug("public_network: {} {}".format(node, public_network))
            same_network[public_network] = ""
            try:
                ipaddress.ip_network(u'{}'.format(public_network))
            except ValueError as err:
                msg = "{} on {} is not valid".format(public_network, node)
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
            public_network = self.data[node].get("public_network", "")
            for address in self.grains[node]['ipv4']:
                try:
                    if ipaddress.ip_address(u'{}'.format(address)) in ipaddress.ip_network(u'{}'.format(public_network)):
                        found = True
                except ValueError:
                    # Don't care about reporting a ValueError here if
                    # public_network is malformed, because the
                    # previous validation in public_network() will do that.
                    pass
            if not found:
                msg = "minion {} missing address on public network {}".format(node, public_network)
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

                cluster_network = self.data[node].get("cluster_network", "")
                log.debug("cluster_network: {} {}".format(node, cluster_network))
                same_network[cluster_network] = ""
                try:
                    ipaddress.ip_network(u'{}'.format(cluster_network))
                except ValueError as err:
                    msg = "{} on {} is not valid".format(cluster_network, node)
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
                cluster_network = self.data[node].get("cluster_network", "")
                for address in self.grains[node]['ipv4']:
                    try:
                        if ipaddress.ip_address(u'{}'.format(address)) in ipaddress.ip_network(u'{}'.format(cluster_network)):
                            found = True
                    except ValueError:
                        # Don't care about reporting a ValueError here if
                        # cluster_network is malformed, because the
                        # previous validation in cluster_network() will do that.
                        pass
                if not found:
                    msg = "minion {} missing address on cluster network {}".format(node, cluster_network)
                    if 'cluster_interface' in self.errors:
                        self.errors['cluster_interface'].append(msg)
                    else:
                        self.errors['cluster_interface'] = [ msg ]
        if not 'cluster_interface' in self.errors:
            self.passed['cluster_interface'] = "valid"



    def _monitor_check(self, name):
        """
        """
        same_hosts = {}
        for node in self.data.keys():
            if name in self.data[node]:
                same_hosts[",".join(self.data[node][name])] = ""
                if self.data[node][name][0].strip() == "":
                    msg = "host {} is missing values for {}.  ".format(node, name) 
                    msg += "Verify that role-mon/stack/default/ceph/minions/*.yml or similar is in your policy.cfg"
                    if name in self.errors:
                        continue
                        #self.errors[name].append(msg)
                    else:
                        self.errors[name] = [ msg ]
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
        At least one minion has a master role
        """
        found = False
        matched = False
        for node in self.data.keys():
            if 'roles' in self.data[node] and 'master' in self.data[node]['roles']:
                
                found = True
                if 'master_minion' in self.data[node] and node == self.data[node]['master_minion']:
                    matched = True

        if not found:
            msg = "No minion assigned master role"
            self.errors['master_role'] = [ msg ]

        if not matched:
            msg = "The master_minion does not match any minion assigned the master role"
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
        time_server = self.data[self.data.keys()[0]].get("time_server", "")
        time_service = self.data[self.data.keys()[0]].get("time_service", "")
        if time_service == 'disabled':
            self.passed['time_server'] = "disabled"
            return

        if (time_service == 'ntp' and os.path.isfile('/usr/sbin/sntp')):
            self._ntp_check(time_server)
        else:
            self._ping_check(time_server)

        if not 'time_server' in self.errors:
            self.passed['time_server'] = "valid"

    def fqdn(self):
        """
        Verify that fqdn matches minion id
        """
        for node in self.grains.keys():
            if self.grains[node]['fqdn'] != node:
                msg = "fqdn {} does not match minion id {}".format(self.grains[node]['fqdn'], node)
                if 'fqdn' in self.errors:
                    self.errors['fqdn'].append(msg)
                else:
                    self.errors['fqdn'] = [ msg ]
        if not 'fqdn' in self.errors:
            self.passed['fqdn'] = "valid"

# Note: the master_minion and ceph_version are specific to the Stage 0 
# validate.  These are also more similar to the ready.py for the firewall
# check than to all the Stage 3 checks.  The difference is that these need
# to error and not just issue a warning.  I expect that this runner and ready.py
# will be combined at some point in the near future.

    def master_minion(self):
        """
        Verify that the master minion setting is a minion
        """
        local = salt.client.LocalClient()
        for node in self.data.keys():
            data = local.cmd(self.data[node]['master_minion'] , 'pillar.get', [ 'master_minion' ], expr_form="glob")
            break
        if data:
            self.passed['master_minion'] = "valid"
        else:
            msg = "Could not find minion {}. Check /srv/pillar/ceph/master_minion.sls".format(self.data[node]['master_minion'])
            self.errors['master_minion'] = [ msg ]


    def ceph_version(self):
        """
        Scan all minions for ceph versions in their repos.
        """
        JEWEL_VERSION="10.2"
        local = salt.client.LocalClient()
        contents = local.cmd('*' , 'cmd.run', [ '/usr/bin/zypper info ceph' ], expr_form="glob")
        
        for minion in contents.keys():
            m = re.search(r'Version: (\S+)', contents[minion])
            # Skip minions with no ceph repo
            if m:
                version = m.group(1)

                # String comparison works for now
                if version < JEWEL_VERSION:
                    msg = "ceph version {} on minion {}".format(version, minion)
                    if 'ceph_version' in self.errors:
                        self.errors['ceph_version'].append(msg)
                    else:
                        self.errors['ceph_version'] = [ msg ]
        if 'ceph_version' not in self.errors:
            self.passed['ceph_version'] = "valid"

    def report(self):
        self.printer.add(self.name, self.passed, self.errors)

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
    
    printer = printer = get_printer(**kwargs)


    for name in cluster.names:
        pillar(name, printer=printer, **kwargs)
    
    printer.print_result()


def pillar(name = None, printer=None, **kwargs):
    """
    Check that the pillar for each cluster meets the requirements to install
    a Ceph cluster.
    """
    has_printer = printer is not None
    if not has_printer:
        printer = get_printer(**kwargs)
        
    if not name:
        usage()
        exit(1)

    #options = SaltOptions()
    local = salt.client.LocalClient()

    # Restrict search to this cluster
    search = "I@cluster:{}".format(name)

    pillar_data = local.cmd(search , 'pillar.items', [], expr_form="compound")
    grains_data = local.cmd(search , 'grains.items', [], expr_form="compound")
    
    v = Validate(name, pillar_data, grains_data, printer)
    v.fsid()
    v.public_network()
    v.public_interface()
    v.cluster_network()
    v.cluster_interface()
    v.monitors()
    v.storage()
    v.master_role()
    v.mon_role()
    v.mon_host()
    v.mon_initial_members()
    v.osd_creation()
    v.pool_creation()
    v.time_server()
    v.fqdn()
    v.report()
    
    if not has_printer:
        printer.print_result()

    if v.errors:
        return False

    return True

def setup(**kwargs):
    """
    Check that initial files prior to any stage are correct
    """
    local = salt.client.LocalClient()
    pillar_data = local.cmd('*' , 'pillar.items', [], expr_form="glob")
    printer = printer = get_printer(**kwargs)

    v = Validate("setup", pillar_data, [], printer)
    v.master_minion()
    v.ceph_version()
    v.report()
    
    printer.print_result()
