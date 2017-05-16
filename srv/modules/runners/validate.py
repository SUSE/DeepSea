# -*- coding: utf-8 -*-

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

    def add(self, name, passed, errors, warnings):
        # Need to make colors optional, but looks better currently
        for attr in passed.keys():
            print "{:25}: {}{}{}{}".format(attr, bcolors.BOLD, bcolors.OKGREEN, passed[attr], bcolors.ENDC)
        for attr in errors.keys():
            print "{:25}: {}{}{}{}".format(attr, bcolors.BOLD, bcolors.FAIL, errors[attr], bcolors.ENDC)
        for attr in warnings.keys():
            print "{:25}: {}{}{}{}".format(attr, bcolors.BOLD, bcolors.WARNING, warnings[attr], bcolors.ENDC)

    def print_result(self):
        pass

class JsonPrinter:

    def __init__(self):
        self.result = {}

    def add(self, name, passed, errors, warnings):
        self.result[name] = {'passed': passed, 'errors': errors, 'warnings': warnings}

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
        for minion, cluster in self.minions.items():
            clusters.setdefault(cluster, []).append(minion)
        return clusters


class Util(object):
    """
    This class contains static helper methods
    """

    @staticmethod
    def parse_list_from_string(list_str, delim=','):
        """
        Transforms a string containing a list of elements separated
        by a specific delimiter into a python list of elements

        Args:
            list_str (string): string with list of elements
            delim    (string): string delimiter

        Returns:
            list: list of elements parsed from list_str
        """
        return [elem.strip() for elem in list_str.split(delim) if elem.strip()]


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
        self.in_dev_env = self.__dev_env()
        self.passed = OrderedDict()
        self.errors = OrderedDict()
        self.warnings = OrderedDict()
        self._minion_check()

    def __dev_env(self):
        if 'DEV_ENV' in os.environ:
            return os.environ['DEV_ENV'].lower() != 'false'
        elif len(self.data.keys()) > 1:
            any_minion = self.data.keys()[0]
            if 'DEV_ENV' in self.data[any_minion]:
                return self.data[any_minion]['DEV_ENV']
        return False

    def _minion_check(self):
        """
        """
        if not self.data:
            log.error("No minions responded")
            os._exit(1)

    def _set_pass_status(self, key):
        """
        Helper function to set status as passed when no entries are seen in errors
        """
        if key not in self.errors and key not in self.warnings:
            self.passed[key] = "valid"

    def dev_env(self):
        if self.in_dev_env:
            self.passed['DEV_ENV'] = "True"

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
        for node in self.data.keys():
            public_network = self.data[node].get("public_network", "")
            net_list = Util.parse_list_from_string(public_network)

            log.debug("public_network: {} {}".format(node, net_list))
            for network in net_list:
                try:
                    ipaddress.ip_network(u'{}'.format(network))
                except ValueError as err:
                    msg = "{} on {} is not valid".format(network, node)
                    self.errors.setdefault('public_network', []).append(msg)

        self._set_pass_status('public_network');

    def public_interface(self):
        """
        """
        for node in self.data.keys():
            if ('roles' in self.data[node] and
                'master' in self.data[node]['roles']):
                continue
            found = False
            public_network = self.data[node].get("public_network", "")
	    net_list = Util.parse_list_from_string(public_network)
            for address in self.grains[node]['ipv4']:
                try:
                    for network in net_list:
                        if ipaddress.ip_address(u'{}'.format(address)) in ipaddress.ip_network(u'{}'.format(network)):
                            found = True
                except ValueError:
                    # Don't care about reporting a ValueError here if
                    # public_network is malformed, because the
                    # previous validation in public_network() will do that.
                    pass
            if not found:
                msg = "minion {} missing address on public network {}".format(node, public_network)
                self.errors.setdefault('public_interface',[]).append(msg)

        self._set_pass_status('public_network')

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

        if len(storage) < 4 and not self.in_dev_env:
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

    def ganesha(self):
        """
        Nodes may only be assigned one ganesha role.  Ganesha depends on
        cephfs or radosgw.
        """
        ganesha_roles = []
        role_mds = False
        role_rgw = False
        role_ganesha = False

        for node, data in self.data.items():
            if ('roles' in data):
                if('ganesha_configurations' in data):
                    ganesha_roles = list(set(data.get("roles")) &
                                        set(data.get("ganesha_configurations")))
                    if len(ganesha_roles) > 1:
                        msg = "minion {} has {} roles. Only one permitted".format(node, ganesha_roles)
                        self.errors.setdefault('ganesha',[]).append(msg)
                    if len(ganesha_roles) == 1:
                        role_ganesha = True


                if not (role_mds or role_rgw):
                    if('mds' in data['roles']):
                        role_mds = True
                    if('rgw' in data['roles']):
                        role_rgw=True
                    if('rgw_configurations' in data):
                        if(list(set(data.get("roles")) &
                                set(data.get("rgw_configurations")))):
                            role_rgw=True

                if not role_ganesha:
                    role_ganesha = 'ganesha' in data['roles']

        if not (role_mds or role_rgw) and role_ganesha:
            msg = "Ganesha requires either mds or rgw node in cluster."
            self.errors['ganesha'] = msg

        self._set_pass_status('ganesha')

    def cluster_network(self):
        """
        All storage nodes must have the same cluster network.  The cluster
        network must be valid.
        """
        for node in self.data.keys():
            if ('roles' in self.data[node] and
                'storage' in self.data[node]['roles']):

                cluster_network = self.data[node].get("cluster_network", "")
                net_list = Util.parse_list_from_string(cluster_network)
                log.debug("cluster_network: {} {}".format(node, net_list))
                for network in net_list:
                    try:
                        ipaddress.ip_network(u'{}'.format(network))
                    except ValueError as err:
                        msg = "{} on {} is not valid".format(network, node)
                        self.errors.setdefault('cluster_network', []).append(msg)

        self._set_pass_status('cluster_network')

    def cluster_interface(self):
        """
        """
        for node in self.data.keys():
            if ('roles' in self.data[node] and
                'storage' in self.data[node]['roles']):
                found = False
                cluster_network = self.data[node].get("cluster_network", "")
	    	net_list = Util.parse_list_from_string(cluster_network)
                for address in self.grains[node]['ipv4']:
                    try:
                        for network in net_list:
                            if ipaddress.ip_address(u'{}'.format(address)) in ipaddress.ip_network(u'{}'.format(network)):
                                found = True
                    except ValueError:
                        # Don't care about reporting a ValueError here if
                        # cluster_network is malformed, because the
                        # previous validation in cluster_network() will do that.
                        pass
                if not found:
                    msg = "minion {} missing address on cluster network {}".format(node, cluster_network)
                    self.errors.setdefault('cluster_interface',[]).append(msg)

        self._set_pass_status('cluster_interface')

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
                    else:
                        self.errors[name] = [ msg ]
            else:
                msg = "host {} is missing {}".format(node, name)
                self.errors.setdefault(name, []).append(msg)

        if len(same_hosts.keys()) > 1:
            msg = "Different entries {}".format(same_hosts.keys())
            self.errors.setdefault(name, []).append(msg)
        elif same_hosts:
            count = len(same_hosts.keys()[0].split(","))
            if count < 3:
                msg = "Must have at least three entries"
                self.errors[name] = [ msg ]
        else:
            msg = "Missing {}".format(name)
            self.errors[name] = [ msg ]

        self._set_pass_status(name)

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

        self._set_pass_status('master_role')

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
                    self.errors['time_service'] = [ msg ]


    def _ping_check(self, server):
        """
        """
        result = self._popen([ '/usr/bin/ping', '-c', '1', server ])
        for line in result[0]:
            if re.match(r'\d+ bytes from', line):
                self.passed['time_service'] = "valid"
        if not 'time_service' in self.passed:
            if result[1]:
                # Take stderr
                self.errors['time_service'] = result[1]
            elif result[0][1]:
                # Take second line of stdout
                self.errors['time_service'] = [ result[0][1] ]
            else:
                # how did we get here?
                msg = "{} unavailable".format(server)
                self.errors['time_service'] = [ msg ]

    def time_service(self):
        """
        Check that time server is available
        """
        pillar_data = list(self.data.values())[0]
        time_service_data = pillar_data.get('ceph', {}).get('time_service')
        if not time_service_data or not time_service_data.get('manage'):
            self.passed['time_service'] = 'disabled'
            return
        ntp_server = time_service_data.get('ntp_server')
        if ntp_server:
            if os.path.isfile('/usr/sbin/sntp'):
                self._ntp_check(ntp_server)
            else:
                self._ping_check(ntp_server)
        self._set_pass_status('time_service')

    def fqdn(self):
        """
        Verify that fqdn matches minion id
        """
        for minion_id in self.grains.keys():
            fqdn = self.grains[minion_id]['fqdn']
            if fqdn != minion_id:
                msg = "fqdn {} does not match minion id {}".format(fqdn, minion_id)
                if fqdn != "localhost":
                    self.errors.setdefault('fqdn', []).append(msg)
                else:
                    self.warnings.setdefault('fqdn', []).append(msg)

        self._set_pass_status('fqdn')

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
        contents = local.cmd('*' , 'cmd.shell', [ '/usr/bin/zypper info ceph' ], expr_form="glob")

        for minion in contents.keys():
            m = re.search(r'Version: (\S+)', contents[minion])
            # Skip minions with no ceph repo
            if m:
                version = m.group(1)

                # String comparison works for now
                if version < JEWEL_VERSION:
                    msg = "ceph version {} on minion {}".format(version, minion)
                    self.errors.setdefault('ceph_version', []).append(msg)

        self._set_pass_status('ceph_version')

    def report(self):
        self.printer.add(self.name, self.passed, self.errors, self.warnings)

def usage():
    print "salt-run validate.pillar cluster_name"
    print "salt-run validate.pillar cluster=cluster_name"
    print "salt-run validate.pillars"


def pillars(**kwargs):
    """
    """
    local = salt.client.LocalClient()
    cluster = ClusterAssignment(local)

    printer = printer = get_printer(**kwargs)


    for name in cluster.names:
        pillar(name, printer=printer, **kwargs)

    printer.print_result()


def pillar(cluster = None, printer=None, **kwargs):
    """
    Check that the pillar for each cluster meets the requirements to install
    a Ceph cluster.
    """

    has_printer = printer is not None
    if not has_printer:
        printer = get_printer(**kwargs)

    if not cluster:
        usage()
        exit(1)

    local = salt.client.LocalClient()

    # Restrict search to this cluster
    search = "I@cluster:{}".format(cluster)

    pillar_data = local.cmd(search , 'pillar.items', [], expr_form="compound")
    grains_data = local.cmd(search , 'grains.items', [], expr_form="compound")

    v = Validate(cluster, pillar_data, grains_data, printer)
    v.dev_env()
    v.fsid()
    v.public_network()
    v.public_interface()
    v.cluster_network()
    v.cluster_interface()
    v.monitors()
    v.storage()
    v.ganesha()
    v.master_role()
    v.mon_host()
    v.mon_initial_members()
    v.osd_creation()
    v.pool_creation()
    v.time_service()
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
    printer = get_printer(**kwargs)

    v = Validate("setup", pillar_data, [], printer)
    v.master_minion()
    v.ceph_version()
    v.report()

    printer.print_result()
