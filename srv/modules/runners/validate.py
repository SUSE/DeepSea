# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error,too-few-public-methods
# pylint: disable=visually-indented-line-with-same-indent-as-next-logical-line
# pylint: disable=fixme,no-self-use
"""
For Ceph, the generation of ceph.conf requires additional information.
Although this information can be determined from Salt itself, the
prerequisite is monitor assignment. This step is more of a post configuration
before deployment.

Eventually, root assignment within the crushmap may live here.  The similar
prerequisite is that osd assignment must be decided before segregating types
of hardware.
"""

import logging
import ipaddress
import json
import os
from os.path import dirname
import re
import sys
import glob
from subprocess import Popen, PIPE
from collections import OrderedDict
import yaml
import salt.client
import salt.utils.error
# pylint: disable=relative-import
import deepsea_minions


log = logging.getLogger(__name__)


class Bcolors(object):
    """
    Sequences for colored text
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class PrettyPrinter(object):
    """
    Console printing
    """

    # pylint: disable=unused-argument
    def add(self, name, passed, errors, warnings):
        """
        Print colored results.  Green is ok, yellow is warning and
        red is error.
        """
        # Need to make colors optional, but looks better currently
        for attr in passed.keys():
            format_str = "{:25}: {}{}{}{}".format(attr,
                                                  Bcolors.BOLD,
                                                  Bcolors.OKGREEN,
                                                  passed[attr],
                                                  Bcolors.ENDC)
            log.info("VALIDATE PASSED  " + format_str)
            print format_str
        for attr in errors.keys():
            format_str = "{:25}: {}{}{}{}".format(attr,
                                                  Bcolors.BOLD,
                                                  Bcolors.FAIL,
                                                  errors[attr],
                                                  Bcolors.ENDC)
            log.info("VALIDATE ERROR   " + format_str)
            print format_str
        for attr in warnings.keys():
            format_str = "{:25}: {}{}{}{}".format(attr,
                                                  Bcolors.BOLD,
                                                  Bcolors.WARNING,
                                                  warnings[attr],
                                                  Bcolors.ENDC)
            log.info("VALIDATE WARNING " + format_str)
            print format_str

    def print_result(self):
        """
        Printing happens during add
        """
        pass


class JsonPrinter(object):
    """
    API printing
    """

    def __init__(self):
        """
        Initialize result
        """
        self.result = {}

    def add(self, name, passed, errors, warnings):
        """
        Collect results
        """
        self.result[name] = {'passed': passed, 'errors': errors, 'warnings': warnings}

    def print_result(self):
        """
        Dump results as json
        """
        json.dump(self.result, sys.stdout)


def get_printer(__pub_output=None, **kwargs):
    """
    Return the passed printer, JsonPrinter or PrettyPrinter function
    """
    if 'printer' in kwargs:
        return kwargs['printer']

    if __pub_output in ['json', 'quiet']:
        return JsonPrinter()
    else:
        return PrettyPrinter()


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
        target = deepsea_minions.DeepseaMinions()
        search = target.deepsea_minions
        self.minions = local.cmd(search, 'pillar.get', ['cluster'])

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


JEWEL_VERSION = "10.2"


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class Validate(object):
    """
    Perform checks on pillar and grain data
    """

    def __init__(self, name, data=None, grains=None, printer=None):
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
        # self._minion_check()

    def __dev_env(self):
        """
        Check if DEV_ENV is set in the environment or pillar
        """
        if 'DEV_ENV' in os.environ:
            return os.environ['DEV_ENV'].lower() != 'false'
        elif self.data:
            any_minion = self.data.keys()[0]
            if 'DEV_ENV' in self.data[any_minion]:
                return self.data[any_minion]['DEV_ENV']
        return False

    def _minion_check(self):
        """
        Originally here to stop the process, but commented out.
        Intend to remove since we have minions.ready
        """
        if not self.data:
            log.error("No minions responded")
            # pylint: disable=protected-access
            os._exit(1)

    def _set_pass_status(self, key):
        """
        Helper function to set status as passed when no entries are seen in errors
        """
        if key not in self.errors and key not in self.warnings:
            self.passed[key] = "valid"

    def dev_env(self):
        """
        Add a validation state to let user know this is set
        """
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
                    self.errors['fsid'] = [msg]

            else:
                msg = "{} has {} characters, not 36".format(fsid, len(fsid))
                self.errors['fsid'] = [msg]
        else:
            stack_dir = "/srv/pillar/ceph/stack"
            cluster_yml = "{}/cluster.yml".format(self.name)

            msg = ("fsid is not defined.  "
                   "Check {0}/{1} and {0}/default/{1}".
                   format(stack_dir, cluster_yml))
            self.errors['fsid'] = [msg]

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
                    msg = "{} on {} is not valid: {}".format(network, node, err)
                    self.errors.setdefault('public_network', []).append(msg)

        self._set_pass_status('public_network')

    def public_interface(self):
        """
        Check that all minions have an address on the public network
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
                        addr = ipaddress.ip_address(u'{}'.format(address))
                        net = ipaddress.ip_network(u'{}'.format(network))
                        if addr in net:
                            found = True
                except ValueError:
                    # Don't care about reporting a ValueError here if
                    # public_network is malformed, because the
                    # previous validation in public_network() will do that.
                    pass
            if not found:
                msg = "minion {} missing address on public network {}".format(node, public_network)
                self.errors.setdefault('public_interface', []).append(msg)

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

        if (not self.in_dev_env and len(monitors) < 3) or (self.in_dev_env and len(monitors) < 1):
            msg = "Too few monitors {}".format(",".join(monitors))
            self.errors['monitors'] = [msg]
        else:
            self.passed['monitors'] = "valid"

    def mgrs(self):
        """
        At least three nodes should have the mgr role
        """
        # TODO: Only make this mandatory for Ceph >= Luminous
        mgrs = []
        for node in self.data.keys():
            if ('roles' in self.data[node] and
                'mgr' in self.data[node]['roles']):
                mgrs.append(node)

        if (not self.in_dev_env and len(mgrs) < 3) or (self.in_dev_env and len(mgrs) < 1):
            msg = "Too few mgrs {}".format(",".join(mgrs))
            self.errors['mgrs'] = [msg]
        else:
            self.passed['mgrs'] = "valid"

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
                if not self._has_storage(node):
                    missing.append(node)

        if (not self.in_dev_env and len(storage) < 4) or (self.in_dev_env and len(storage) < 1):
            msg = "Too few storage nodes {}".format(",".join(storage))
            self.errors['storage'] = [msg]
        else:
            if missing:
                stack_dir = "/srv/pillar/ceph/stack"
                minion_yml = "{}/minions/*.yml".format(self.name)
                err = "Storage nodes {} missing storage attribute.  ".format(",".join(storage))
                check = "Check {0}/{1} and {0}/default/{1}".format(stack_dir, minion_yml)
                self.errors['storage'] = [err + check]
            else:
                self.passed['storage'] = "valid"

    def _has_storage(self, node):
        """
        Check original and ceph name space for storage attribute
        """
        if ('storage' in self.data[node] or
           ('ceph' in self.data[node] and
           'storage' in self.data[node]['ceph'])):
            return True
        return False

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
            if 'roles' in data:
                if 'ganesha_configurations' in data:
                    ganesha_roles = list(set(data.get("roles")) &
                                         set(data.get("ganesha_configurations")))
                    if len(ganesha_roles) > 1:
                        msg = "minion {}".format(node)
                        msg += " {} roles. Only one permitted".format(ganesha_roles)
                        self.errors.setdefault('ganesha', []).append(msg)
                    if len(ganesha_roles) == 1:
                        role_ganesha = True

                if not (role_mds or role_rgw):
                    if 'mds' in data['roles']:
                        role_mds = True
                    if 'rgw' in data['roles']:
                        role_rgw = True
                    if 'rgw_configurations' in data:
                        if (list(set(data.get("roles")) &
                            set(data.get("rgw_configurations")))):
                            role_rgw = True

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
                        msg = "{} on {} is not valid: {}".format(network, node, err)
                        self.errors.setdefault('cluster_network', []).append(msg)

        self._set_pass_status('cluster_network')

    def cluster_interface(self):
        """
        Check that storage nodes have an interface on the cluster network
        """
        # pylint: disable=too-many-nested-blocks
        for node in self.data.keys():
            if ('roles' in self.data[node] and
                'storage' in self.data[node]['roles']):
                found = False
                cluster_network = self.data[node].get("cluster_network", "")
                net_list = Util.parse_list_from_string(cluster_network)
                for address in self.grains[node]['ipv4']:
                    try:
                        for network in net_list:
                            addr = ipaddress.ip_address(u'{}'.format(address))
                            net = ipaddress.ip_network(u'{}'.format(network))
                            if addr in net:
                                found = True
                    except ValueError:
                        # Don't care about reporting a ValueError here if
                        # cluster_network is malformed, because the
                        # previous validation in cluster_network() will do that.
                        pass
                if not found:
                    msg = "minion {}".format(node)
                    msg += " missing address on cluster network {}".format(cluster_network)
                    self.errors.setdefault('cluster_interface', []).append(msg)

        self._set_pass_status('cluster_interface')

    def _monitor_check(self, name):
        """
        Verify the minimum number of monitors for the environment
        """
        same_hosts = {}
        for node in self.data.keys():
            if name in self.data[node]:
                same_hosts[",".join(self.data[node][name])] = ""
                if self.data[node][name][0].strip() == "":
                    msg = "host {} is missing values for {}.  ".format(node, name)
                    msg += ("Verify that "
                            "role-mon/stack/default/ceph/minions/*.yml "
                            "or similar is in your policy.cfg")
                    if name in self.errors:
                        continue
                    else:
                        self.errors[name] = [msg]
            else:
                msg = "host {} is missing {}".format(node, name)
                self.errors.setdefault(name, []).append(msg)

        if len(same_hosts.keys()) > 1:
            msg = "Different entries {}".format(same_hosts.keys())
            self.errors.setdefault(name, []).append(msg)
        elif same_hosts:
            count = len(same_hosts.keys()[0].split(","))
            if (not self.in_dev_env and count < 3) or (self.in_dev_env and count < 1):
                if self.in_dev_env:
                    msg = "Must have at least one monitor"
                else:
                    msg = "Must have at least three monitors"
                self.errors[name] = [msg]
        else:
            msg = "Missing {}".format(name)
            self.errors[name] = [msg]

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
            self.errors['master_role'] = [msg]

        if not matched:
            msg = "The master_minion does not match any minion assigned the master role"
            self.errors['master_role'] = [msg]

        self._set_pass_status('master_role')

    def _redirection_check(self, name):
        """
        I believe this method and the next two will be removed.  Neither
        osd_creation nor pool_creation exist in the pillar.  Honestly, I do
        not remember going down this path.
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
                    self.errors[attr] = [msg]

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
        Return stdout, stderr of cmd
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
        Check the ntp server is responding
        """
        result = self._popen(['/usr/sbin/sntp', '-t', '1', server])
        for line in result[0]:
            if re.search(r'{}'.format(server), line):
                if re.search(r'no.*response', line):
                    msg = line
                    self.errors['time_server'] = [msg]

    def _ping_check(self, server):
        """
        Check that the time server responds to ping
        """
        result = self._popen(['/usr/bin/ping', '-c', '1', server])
        for line in result[0]:
            if re.match(r'\d+ bytes from', line):
                self.passed['time_server'] = "valid"
        if 'time_server' not in self.passed:
            if result[1]:
                # Take stderr
                self.errors['time_server'] = result[1]
            elif result[0][1]:
                # Take second line of stdout
                self.errors['time_server'] = [result[0][1]]
            else:
                # how did we get here?
                msg = "{} unavailable".format(server)
                self.errors['time_server'] = [msg]

    def time_server(self):
        """
        Check that time server is available
        """
        time_init = self.data[self.data.keys()[0]].get("time_init", "")
        if time_init == 'disabled':
            self.passed['time_server'] = "disabled"
            return

        time_server = self.data[self.data.keys()[0]].get("time_server", "")
        if not isinstance(time_server, list):
            time_server = [time_server]
        for server in time_server:
            if time_init == 'ntp' and os.path.isfile('/usr/sbin/sntp'):
                self._ntp_check(server)
            else:
                self._ping_check(server)
        self._set_pass_status('time_server')

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

    def openattic(self):
        """
        Check for incompatible issues for openATTIC

        The rgw role (or any custom rgw role) may be configured to use
        port 80.  With all the configuration allowed in the pillar, checking the
        final ceph.conf seems the most reliable.
        """
        local = salt.client.LocalClient()
        for node in self.data.keys():
            if ('roles' in self.data[node] and
                'openattic' in self.data[node]['roles'] and
                'rgw' in self.data[node]['roles']):
                # Would use file.contains if it supported '='
                result = local.cmd(node, 'file.search',
                                   ['/etc/ceph/ceph.conf', r'port\=80\b'],
                                   expr_form="glob")
                if result[node]:
                    msg = "rgw port conflicts with openATTIC on {} - check ceph.conf".format(node)
                    self.errors.setdefault('openattic', []).append(msg)

        self._set_pass_status('openattic')

    def saltapi(self):
        """
        Log into the salt-api and verify that a token is returned.

        Note: The duplicate functionality between the post section of the
        DeepSea rpm and the salt state may come across as unnecessary.
        However, some install using the Makefile and not the rpm.  Also,
        the rpm will only attempt restarts of the salt-api, but neither
        enable nor start the salt-api.  The salt state does.

        In the expected case, the salt-master is restarted with the
        sharedsecret when DeepSea is installed.  The salt-api is then
        started and enabled as part of Stage 0.  This check is really
        here for those that went a completely different path.
        """
        __opts__ = salt.config.client_config('/etc/salt/master')
        # pylint: disable=unused-variable
        stdout, stderr = self._popen(['curl', '-si', 'localhost:8000/login',
                                      '-H', '"Accept: application/json"',
                                      '-d' 'username=admin',
                                      '-d', 'sharedsecret={}'.format(__opts__['sharedsecret']),
                                      '-d', 'eauth=sharedsecret'])
        try:
            result = json.loads(stdout[-1])
        except ValueError as err:
            msg = ("Salt API is failing to authenticate"
                   " - try 'systemctl restart salt-master': {}".format(err))
            self.errors.setdefault('salt-api', []).append(msg)
            return
        if 'return' in result:
            if 'token' in result['return'][0]:
                self._set_pass_status('salt-api')
                return
        msg = "Unexpected return for Salt API - check logs"
        self.errors.setdefault('salt-api', []).append(msg)

# Note: the master_minion and ceph_version are specific to the Stage 0
# validate.  These are also more similar to the ready.py for the firewall
# check than to all the Stage 3 checks.  The difference is that these need
# to error and not just issue a warning.  I expect that this runner and ready.py
# will be combined at some point in the near future.

    def master_minion(self):
        """
        Verify that the master minion setting is a minion
        """
        data = None
        node = None
        local = salt.client.LocalClient()
        for node in self.data.keys():
            data = local.cmd(self.data[node]['master_minion'],
                             'pillar.get', ['master_minion'], expr_form="glob")
            break
        if data:
            self.passed['master_minion'] = "valid"
        else:
            if node:
                msg = "Could not find minion {}.".format(self.data[node]['master_minion'])
                msg += " Check /srv/pillar/ceph/master_minion.sls"
            else:
                msg = "Missing pillar data"
            self.errors['master_minion'] = [msg]

    def ceph_version(self):
        """
        Scan all minions for ceph versions in their repos.
        """
        target = deepsea_minions.DeepseaMinions()
        search = target.deepsea_minions
        local = salt.client.LocalClient()
        contents = local.cmd(search, 'pkg.latest_version', ['ceph'], expr_form="compound")
        for minion, version in contents.items():
            if not version:
                info = local.cmd(minion, 'pkg.info_installed', ['ceph'])
                if info and 'version' in info[minion]['ceph']:
                    version = info[minion]['ceph']['version']
                else:
                    self.errors.setdefault('ceph_version', []).append(
                        "No Ceph version is available for installation in {}".format(minion))
                    continue

            colon_idx = version.find(':')
            if colon_idx != -1:
                version = version[colon_idx+1:]
            dash_idx = version.rfind('-')
            if dash_idx != -1:
                version = version[:dash_idx]
            if version < JEWEL_VERSION:
                self.errors.setdefault('ceph_version', []).append(
                    "The Ceph version available in {} is older than 'jewel' (10.2)"
                    .format(minion))

        self._set_pass_status('ceph_version')

    def _accumulate_files_from(self, filename):
        """
        Process policy file skipping comments, unmatched lines
        """
        accumulated_files = []
        proposals_dir = "/srv/pillar/ceph/proposals"

        with open(filename, "r") as policy:
            for line in policy:
                # strip comments from the end of the line
                line = re.sub(r'\s+#.*$', '', line)
                line = line.rstrip()
                if line.startswith('#') or not line:
                    log.debug("Ignoring '{}'".format(line))
                    continue
                files = self._parse(proposals_dir + "/" + line)
                if not files:
                    log.warning("{} matched no files".format(line))
                log.debug(line)
                log.debug(files)
                for filename in files:
                    if os.stat(filename).st_size == 0:
                        log.warning("Skipping empty file {}".format(filename))
                        continue
                    accumulated_files.append(filename)
        return accumulated_files

    def _stack_files(self, stack_dir, filetype='yml'):
        """
        Lists all files under stack_dir
        """
        stack_files = []
        # pylint: disable=unused-variable
        for drn, drns, flnm in os.walk(stack_dir):
            for filename in flnm:
                if filename.split('.')[-1] == filetype:
                    stack_files.append((os.path.join(drn, filename)))
        return stack_files

    def profiles_populated(self):
        """
        Check for hardware profiles
        """
        policy_file = '/srv/pillar/ceph/proposals/policy.cfg'
        accum_files = self._accumulate_files_from(policy_file)
        profiles = [prf for prf in accum_files if 'profile' in prf]
        if not profiles:
            message = ("There are no files under the profiles directory."
                       "Probably an issue with the discovery stage.")
            self.errors.setdefault('profiles_populated', []).append(message)
        self._set_pass_status('profiles_populated')

    def lint_yaml_files(self):
        """
        Scans for sanity of yaml files
        """
        policy_file = '/srv/pillar/ceph/proposals/policy.cfg'
        stack_dir = '/srv/pillar/ceph/stack'

        stack_dir_files = self._stack_files(stack_dir, filetype='yml')
        accum_files = self._accumulate_files_from(policy_file)

        files = stack_dir_files + accum_files

        for filename in files:
            if os.stat(filename).st_size == 0:
                log.warning("Skipping empty file {}".format(filename))
                continue
            with open(filename, 'r') as stream:
                try:
                    log.debug(yaml.load(stream))
                except yaml.YAMLError as exc:
                    # pylint: disable=no-member
                    pmark = exc.problem_mark
                    message = "syntax error in {}".format(pmark.name)
                    message += " on line {} at position {}".format(pmark.line, pmark.column)
                    self.errors.setdefault('yaml_syntax', []).append(message)
        self._set_pass_status('yaml_syntax')

    def _parse(self, line):
        """
        Return globbed files constrained by optional slices or regexes.
        """
        if " " in line:
            parts = re.split(r'\s+', line)
            files = sorted(glob.glob(parts[0]))
            for keyvalue in parts[1:]:
                key, value = keyvalue.split('=')
                if key == "re":
                    regex = re.compile(value)
                    files = [match.group(0) for _file in files
                             for match in [regex.search(_file)] if match]
                elif key == "slice":
                    # pylint: disable=eval-used
                    files = eval("files{}".format(value))
                else:
                    log.warning("keyword {} unsupported".format(key))

        else:
            files = glob.glob(line)
        return files

    def deepsea_minions(self, target):
        """
        Verify deepsea_minions is set
        """
        if target.deepsea_minions:
            if target.matches:
                self.passed['deepsea_minions'] = "valid"
            else:
                msg = ("No minions matched for {} - check "
                       "/srv/pillar/ceph/deepsea_minions.sls".format(target.deepsea_minions))
                self.errors['deepsea_minions'] = [msg]
        else:
            msg = "deepsea_minions not defined - check /srv/pillar/ceph/deepsea_minions.sls"
            self.errors['deepsea_minions'] = [msg]

    def report(self):
        """
        Print the validation report
        """
        self.printer.add(self.name, self.passed, self.errors, self.warnings)
        self.printer.print_result()


def help_():
    """
    Usage
    """
    _usage = ('salt-run validate.pillars:\n'
              'salt-run validate.pillar ceph:\n'
              'salt-run validate.pillar cluster=ceph:\n\n'
              '    Verify that Stage 3/deploy will succeed\n'
              '\n\n'
              'salt-run validate.setup:\n\n'
              '    Verify that Stage 0/prep will succeed\n'
              '\n\n'
              'salt-run validate.prep:\n\n'
              '    Verify that Stage 1/discovery will succeed\n'
              '\n\n'
              'salt-run validate.discovery:\n\n'
              '    Verify that Stage 2/configuration will succeed\n'
              '\n\n'
              'salt-run validate.deploy:\n\n'
              '    Verify that Stage 4/services will succeed\n'
              '\n\n'
              'salt-run validate.saltapi:\n\n'
              '    Verify that the Salt API is working\n'
              '\n\n')
    print _usage
    return ""


def usage(func='None'):
    """
    Short usage
    """
    print "salt-run validate.{} cluster_name".format(func)
    print "salt-run validate.{} cluster=cluster_name".format(func)


def pillars(**kwargs):
    """
    Check all clusters (Only one is supported currently)
    """
    local = salt.client.LocalClient()
    cluster = ClusterAssignment(local)

    printer = get_printer(**kwargs)

    for name in cluster.names:
        pillar(name, printer=printer, **kwargs)

    printer.print_result()
    return ""


def discovery(cluster=None, printer=None, **kwargs):
    """
    Check that the pillar for each cluster meets the requirements to install
    a Ceph cluster.
    """
    if not cluster:
        usage(func='discovery')
        exit(1)

    local = salt.client.LocalClient()

    # Restrict search to this cluster
    target = deepsea_minions.DeepseaMinions()
    search = target.deepsea_minions
    if 'cluster' in __pillar__:
        if __pillar__['cluster']:
            # pylint: disable=redefined-variable-type
            # Salt accepts either list or string as target
            search = "I@cluster:{}".format(cluster)

    pillar_data = local.cmd(search, 'pillar.items', [], expr_form="compound")

    printer = get_printer(**kwargs)
    valid = Validate(cluster, data=pillar_data, printer=printer)

    valid.deepsea_minions(target)
    valid.lint_yaml_files()
    if not valid.in_dev_env:
        valid.profiles_populated()
    valid.report()

    if valid.errors:
        return False

    return True


def pillar(cluster=None, printer=None, **kwargs):
    """
    Check that the pillar for each cluster meets the requirements to install
    a Ceph cluster.
    """

    if not cluster:
        usage(func='pillar')
        exit(1)

    local = salt.client.LocalClient()

    # Restrict search to this cluster
    search = "I@cluster:{}".format(cluster)

    pillar_data = local.cmd(search, 'pillar.items', [], expr_form="compound")
    grains_data = local.cmd(search, 'grains.items', [], expr_form="compound")

    printer = get_printer(**kwargs)
    valid = Validate(cluster, pillar_data, grains_data, printer)
    valid.dev_env()
    valid.fsid()
    valid.public_network()
    valid.public_interface()
    valid.cluster_network()
    valid.cluster_interface()
    valid.monitors()
    valid.mgrs()
    valid.storage()
    valid.ganesha()
    valid.master_role()
    valid.osd_creation()
    valid.pool_creation()
    valid.time_server()
    valid.fqdn()
    valid.report()

    if valid.errors:
        return False

    return True


def deploy(**kwargs):
    """
    Verify that Stage 4, Services can succeed.
    """
    target = deepsea_minions.DeepseaMinions()
    search = target.deepsea_minions
    local = salt.client.LocalClient()
    pillar_data = local.cmd(search, 'pillar.items', [], expr_form="compound")
    grains_data = local.cmd(search, 'grains.items', [], expr_form="compound")
    printer = get_printer(**kwargs)

    valid = Validate("deploy", pillar_data, grains_data, printer)
    valid.openattic()
    valid.report()

    if valid.errors:
        return False

    return True


def saltapi(**kwargs):
    """
    Verify that the Salt API is working
    """
    target = deepsea_minions.DeepseaMinions()
    search = target.deepsea_minions
    local = salt.client.LocalClient()

    pillar_data = local.cmd(search, 'pillar.items', [], expr_form="compound")
    printer = get_printer(**kwargs)

    valid = Validate("salt-api", pillar_data, [], printer)
    valid.saltapi()
    valid.report()

    if valid.errors:
        return False

    return True


def prep(**kwargs):
    """
    Enough users seem to skip around.  Verify that the basics are still
    correct for Stage 1.
    """
    setup(**kwargs)


def setup(**kwargs):
    """
    Check that initial files prior to any stage are correct
    """
    target = deepsea_minions.DeepseaMinions()
    search = target.deepsea_minions
    local = salt.client.LocalClient()

    pillar_data = local.cmd(search, 'pillar.items', [], expr_form="compound")
    printer = get_printer(**kwargs)

    valid = Validate("setup", pillar_data, [], printer)
    valid.deepsea_minions(target)
    valid.master_minion()
    valid.ceph_version()
    valid.report()

    if valid.errors:
        return False

    return True

__func_alias__ = {
                 'help_': 'help',
                 }
