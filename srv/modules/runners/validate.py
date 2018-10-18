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

from __future__ import absolute_import
from __future__ import print_function
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
from distutils.version import LooseVersion  # pylint: disable=no-name-in-module,import-error,blacklisted-module,3rd-party-module-not-gated
import yaml
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client
import salt.utils.error
# pylint: disable=relative-import


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
    def add(self, name, skipped, passed, errors, warnings):
        """
        Print colored results.  Green is ok, yellow is warning,
        red is error and blue is skipped.
        """
        # Need to make colors optional, but looks better currently
        for attr in skipped.keys():
            format_str = "{:25}: {}{}{}{}".format(attr,
                                                  Bcolors.BOLD,
                                                  Bcolors.OKBLUE,
                                                  skipped[attr],
                                                  Bcolors.ENDC)
            log.info("VALIDATE SKIPPED  %s", format_str)
            print(format_str)
        for attr in passed.keys():
            format_str = "{:25}: {}{}{}{}".format(attr,
                                                  Bcolors.BOLD,
                                                  Bcolors.OKGREEN,
                                                  passed[attr],
                                                  Bcolors.ENDC)
            log.info("VALIDATE PASSED  %s", format_str)
            print(format_str)
        for attr in errors.keys():
            format_str = "{:25}: {}{}{}{}".format(attr,
                                                  Bcolors.BOLD,
                                                  Bcolors.FAIL,
                                                  errors[attr],
                                                  Bcolors.ENDC)
            log.info("VALIDATE ERROR   %s", format_str)
            print(format_str)
        for attr in warnings.keys():
            format_str = "{:25}: {}{}{}{}".format(attr,
                                                  Bcolors.BOLD,
                                                  Bcolors.WARNING,
                                                  warnings[attr],
                                                  Bcolors.ENDC)
            log.info("VALIDATE WARNING %s", format_str)
            print(format_str)

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
        printer = kwargs['printer']
    elif __pub_output in ['json', 'quiet']:
        printer = JsonPrinter()
    else:
        printer = PrettyPrinter()
    return printer


class Preparation(object):
    """
    Provide commonly used preparations for ClusterAssignment and
    Validate
    """

    def __init__(self):
        self.search = __utils__['deepsea_minions.show']()
        self.matches = __utils__['deepsea_minions.matches']()
        self.local = salt.client.LocalClient()


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


class ClusterAssignment(Preparation):
    """
    Discover the cluster assignment and ignore unassigned
    """

    def __init__(self):
        """
        Query the cluster assignment and remove unassigned
        """
        # Python2 syntax is only used because the test is running in python2
        super(ClusterAssignment, self).__init__()
        self.minions = self.local.cmd(self.search, 'pillar.get', ['cluster'])

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


LUMINOUS_VERSION = "11.2"


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class Validate(Preparation):
    """
    Perform checks on pillar and grain data
    """

    def __init__(self, name, search_pillar=False, search_grains=False,
                 printer=None, search=None, skip_init=False):
        """
        Query the cluster assignment and remove unassigned
        """
        # Python2 syntax is only used because the test is running in python2
        if not skip_init:
            super(Validate, self).__init__()
        self.name = name
        self.data = self.__get_items(search_pillar, 'pillar')
        self.grains = self.__get_items(search_grains, 'grains')
        self.printer = printer
        self.in_dev_env = self.__dev_env()
        self.skipped = OrderedDict()
        self.passed = OrderedDict()
        self.errors = OrderedDict()
        self.warnings = OrderedDict()
        if search:
            self.search = search

        # Ceph version
        self.package = 'ceph-common'
        self.uninstalled = []

    def __get_items(self, enabled, target):
        """
        Look up [pillar|grains].items
        """
        if enabled:
            items = self.local.cmd(self.search, target + '.items',
                                   [], tgt_type="compound")
            return items
        return None

    def __dev_env(self):
        """
        Check if DEV_ENV is set in the environment or pillar
        """
        if 'DEV_ENV' in os.environ:
            return os.environ['DEV_ENV'].lower() != 'false'
        elif self.data:
            any_minion = list(self.data.keys())[0]
            if 'DEV_ENV' in self.data[any_minion]:
                return self.data[any_minion]['DEV_ENV']
        return False

    def _set_pass_status(self, key):
        """
        Helper function to set status as passed when no entries are seen in errors
        """
        if key not in self.errors and key not in self.warnings:
            self.passed[key] = "valid"

    def skip(self, key):
        """
        Assign skipped steps
        """
        self.skipped[key] = "skipping"

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
        fsid = self.data[list(self.data.keys())[0]].get("fsid", "")
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

    def master_role(self):
        """
        At least one minion has a master role
        """
        found = False
        for node in self.data.keys():
            if 'roles' in self.data[node] and 'master' in self.data[node]['roles']:

                found = True
        if not found:
            msg = "No minion assigned master role"
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
            line = line.decode('ascii')
            stdout.append(line.rstrip('\n'))
        for line in proc.stderr:
            line = line.decode('ascii')
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
        time_init = self.data[list(self.data.keys())[0]].get("time_init", "")
        if time_init == 'disabled':
            self.passed['time_server'] = "disabled"
            return

        time_server = self.data[list(self.data.keys())[0]].get("time_server", "")
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
                                   tgt_type="glob")
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
        except IndexError as err:
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
        Verify that the master minion setting is not empty
        """
        # Checking the master module 'master.minion' causes the states of
        # ceph.stage.0.minion to fail.  Leaving this example here, since we
        # have no effective way of using master modules in python.
        #
        # __opts__ = salt.config.client_config('/etc/salt/master')
        # __grains__ = salt.loader.grains(__opts__)
        # __opts__['grains'] = __grains__
        # __utils__ = salt.loader.utils(__opts__)
        # __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)
        # master_minion = __salt__['master.minion']()

        if 'master_minion' in __pillar__ and __pillar__['master_minion'] is None:
            msg = "master_minion is empty - "
            msg += "Check master_minion setting in pillar"
            self.errors['master_minion'] = [msg]
        else:
            self.passed['master_minion'] = "valid"

    def ceph_version(self):
        """
        Scan all minions for ceph versions in their repos.
        """
        self._check_installed()
        self._check_available()
        self._set_pass_status('ceph_version')

    def _check_installed(self):
        """
        Check for installed Ceph packages.  The query is faster and a fresh
        install only happens once.
        """
        search = __utils__['deepsea_minions.show']()
        results = self._silent_search(search, 'pkg.info_installed')

        for minion in results:
            if isinstance(results[minion], dict) and self.package in results[minion]:
                if 'version' in results[minion][self.package]:
                    version = self._check_version(minion, 'pkg.info_installed',
                                                  results[minion][self.package]['version'])
                    if (version and LooseVersion(version) < LooseVersion(LUMINOUS_VERSION)):
                        prefix = 'Ceph version is older than Luminous on'
                        self.errors.setdefault('ceph_version', [prefix]).append(minion)
                else:
                    # Something is really wrong
                    prefix = 'Version missing from'
                    self.errors.setdefault('ceph_version', [prefix]).append(minion)
            else:
                self.uninstalled.append(minion)

    def _check_available(self):
        """
        Check for available Ceph packages.  If all minions have Ceph installed,
        then the query has no results.
        """
        if not self.uninstalled:
            return

        search = "L@{}".format(",".join(self.uninstalled))
        results = self._silent_search(search, 'pkg.info_available')
        for minion in results:
            if isinstance(results[minion], dict) and self.package in results[minion]:
                if 'version' in results[minion][self.package]:
                    version = self._check_version(minion, 'pkg.info_available',
                                                  results[minion][self.package]['version'])
                    if (version and LooseVersion(version) < LooseVersion(LUMINOUS_VERSION)):
                        prefix = 'Ceph repository version is older than Luminous on'
                        self.errors.setdefault('ceph_version', [prefix]).append(minion)
                else:
                    # Something is really wrong
                    prefix = 'Repo version missing from'
                    self.errors.setdefault('ceph_version', [prefix]).append(minion)
            else:
                prefix = 'Ceph repository is missing from'
                self.errors.setdefault('ceph_version', [prefix]).append(minion)

    def _silent_search(self, search, func):
        """
        Search that matches no minions prints to stdout confusing users when
        mixed with the normal messages.  Suppress stdout.
        """
        _stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        results = self.local.cmd(search, func, [self.package], tgt_type="compound")
        sys.stdout = _stdout
        return results

    def _check_version(self, minion, func, version):
        """
        Version may be an error message
        """
        if version.split('.')[0].isdigit():
            return version
        prefix = 'Ceph repository version {} is malformed from {}'.format(version, func)
        self.errors.setdefault('ceph_version', [prefix]).append(minion)
        return ""

    def salt_version(self):
        """
        Scan all minions for their salt versions.
        """
        grains_data = self.local.cmd(self.search, 'grains.get',
                                     ['saltversion'], tgt_type="compound")

        for node in grains_data:
            year, month, release = grains_data[node].split('.')
            warning_str = '{node}: {year}.{month}.{release} not supported' \
                          .format(node=node, year=year, month=month,
                                  release=release)
            if int(year) < 2017 or int(year) > 2018:
                if 'salt_version' not in self.warnings:
                    self.warnings['salt_version'] = [warning_str]
                else:
                    self.warnings['salt_version'].append(warning_str)
        self._set_pass_status('salt_version')

    def _accumulate_files_from(self, policy_file):
        """
        Process policy file skipping comments, unmatched lines
        """
        accumulated_files = []
        proposals_dir = "/srv/pillar/ceph/proposals"

        with open(policy_file, "r") as policy:
            for line in policy:
                # strip comments from the end of the line
                line = re.sub(r'\s+#.*$', '', line)
                line = line.rstrip()
                if line.startswith('#') or not line:
                    log.debug("Ignoring '{}'".format(line))
                    continue
                proposal_files = self._parse(proposals_dir + "/" + line)
                if not proposal_files:
                    log.warning("{} matched no files".format(line))
                log.debug(line)
                log.debug(proposal_files)
                for proposal_file in proposal_files:
                    if os.stat(proposal_file).st_size == 0:
                        log.warning("Skipping empty file {}".format(proposal_file))
                        continue
                    accumulated_files.append(proposal_file)
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

    def deepsea_minions(self):
        """
        Verify deepsea_minions is set
        """
        if self.search:
            if self.matches:
                self.passed['deepsea_minions'] = "valid"
            else:
                # pylint: disable=line-too-long
                msg = ("No minions matched for {} - See `man deepsea-minions`".format(self.search))
                self.errors['deepsea_minions'] = [msg]
        else:
            msg = ("deepsea_minions not defined - " +
                   "See `/srv/pillar/ceph/deepsea_minions.sls` for details")
            self.errors['deepsea_minions'] = [msg]

    def kernel(self):
        """
        Verify that target_core_rbd kernel module is available on iSCSI Gateways and admin node
        """
        targets = [node for node in self.data if node == 'admin' or
                   ('roles' in self.data[node] and 'igw' in self.data[node]['roles'])]
        check = self.local.cmd(targets, 'kmod.check_available', ['target_core_rbd'],
                               tgt_type='list')
        for node, passed in check.items():
            if not passed:
                self.errors.setdefault('kernel_module', []).append(
                        "{}: kernel module not active".format(node))

        if 'kernel_module' not in self.errors:
            self.passed['kernel_module'] = 'valid'
        self._set_pass_status('kernel_module')

    def config_check(self):
        """
        Verify if config does not contain any deprecated config k:v pairs
        """
        issue_map = ConfigCheck().run()
        for conf_obj in issue_map:
            key = conf_obj.key
            values = conf_obj.values
            filename = conf_obj.filename
            release = conf_obj.release
            if not values:
                msg = "Key {} is deprecated. Please remove it from your config".format(key)
            else:
                values = '/'.join(values)
                # pylint: disable=line-too-long
                msg = "Key {} with value(s) {} was found (deprecated since {})".format(key, values, release)

            self.errors["{}::{}".format(filename, key)] = msg

    def report(self):
        """
        Print the validation report
        """
        self.printer.add(self.name, self.skipped, self.passed, self.errors, self.warnings)
        self.printer.print_result()


class ConfigCheck(object):
    """Class to detect deprecated config values in files.

    Attributes:
        base_path (str): Base path
        map_file (str): Map file path
        conf_path (str): Conf file path
        suffix (str): Suffix for config files
        files (list): List of files from glob
        map (dict): Map of deprecated k:v
        issues (list): List of found incidents
    """
    def __init__(self):

        self.base_path = '/srv/salt/ceph/configuration/files'
        self.map_file = '{}/deprecated_map.yml'.format(self.base_path)
        self.conf_path = '{}/ceph.conf.d'.format(self.base_path)
        self.suffix = '.conf'
        self.files = glob.glob("{path}/*{suffix}".format(path=self.conf_path,
                                                         suffix=self.suffix))
        self.map = self.load_map()
        self.issues = []

    def load_map(self):
        """
        Loads k:v map from disk

        Returns:
            YAML map
        Raises:
            YAMLError
        """
        with open(self.map_file, 'r') as _fd:
            try:
                return yaml.load(_fd)
            except yaml.YAMLError:
                log.error('Could not read {}'.format(self.map_file))

    def read_lines(self, filename):
        """ Reads lines from an open file and returns a generator
        Args:
            fn (str): filename
        Yields:
            str: line from file
        """
        with open(filename, 'r') as _fd:
            for line in _fd.readlines():
                yield line

    def extract_k_v(self, line):
        """ Extracts key and value from line
        Args:
            line (str): line from file
        Returns:
            tuple: stripped key and value
        """
        _key, _value = line.split('=')
        return _key.strip(), _value.strip()

    def check_line(self, line):
        """ Checks a line for deprecated keys/values
        Args:
            line (str): line from file
        Returns:
            DeprecatedConf: instance of obj
        """
        _key, _value = self.extract_k_v(line)
        return self.compare_k_v_to_map(_key, _value)

    def compare_k_v_to_map(self, key, value):
        """ Compares k:v against a map of k:v that are know to be deprecated
        Args:
            k (str): key from config
            v (str): value from config
        Returns:
            DeprecatedConf: instance of obj or None
        """
        obj = None
        for release, kv_map in self.map.items():
            if key not in kv_map:
                continue
            if isinstance(kv_map[key], list):
                obj = DeprecatedConf(key=key,
                                     release=release)
                for depr_val in kv_map[key]:
                    if value == depr_val:
                        obj.add_value(depr_val)
            if isinstance(kv_map[key], str):
                if kv_map[key] == value:
                    obj = DeprecatedConf(key=key,
                                         release=release,
                                         values=[value])
        return obj

    def run(self):
        """
        Returns:
            list: contains objects of DeprecatedConf
        """
        for filename in self.files:
            for line in self.read_lines(filename):
                conf_object = self.check_line(line)
                if not conf_object:
                    continue
                conf_object.set_filename(filename)
                self.issues.append(conf_object)
        return self.issues


class DeprecatedConf(object):
    """Simple class to store and access information conveniently.

    Attributes:
        filename (str): Filename the k:v is associated with
        release (str): Release the k:v is deprecated in
        key (str): Name of the key
        value (list): List of found deprecated values
    """

    def __init__(self, **kwargs):
        self.filename = kwargs.get('filename', None)
        self.release = kwargs.get('release', None)
        self.key = kwargs.get('key', None)
        self.values = kwargs.get('values', [])

    def add_value(self, value):
        """ Adds value to values attribute
        Args:
            value (str): Deprecated config value
        """
        self.values.append(value)

    def set_filename(self, filename):
        """ Sets filename
        Args:
            fn (str): Filename the object is associated with
        """
        self.filename = filename


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
    print(_usage)
    return ""


def usage(func='None'):
    """
    Short usage
    """
    print("salt-run validate.{} cluster_name".format(func))
    print("salt-run validate.{} cluster=cluster_name".format(func))


def pillars(**kwargs):
    """
    Check all clusters (Only one is supported currently)
    """
    cluster = ClusterAssignment()

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

    # Restrict search to this cluster
    if 'cluster' in __pillar__:
        if __pillar__['cluster']:
            # Salt accepts either list or string as target
            search = "I@cluster:{}".format(cluster)
    else:
        search = None

    printer = get_printer(**kwargs)
    valid = Validate(cluster, search_pillar=True, printer=printer,
                     search=search)
    valid.deepsea_minions()
    valid.lint_yaml_files()
    if not valid.in_dev_env:
        valid.profiles_populated()
    valid.report()

    if valid.errors:
        return False

    return True


def config_check(cluster=None, printer=None, **kwargs):
    """
    Config Check user facing call
    """
    if not cluster:
        usage(func='pillar')
        exit(1)

    # Restrict search to this cluster
    search = "I@cluster:{}".format(cluster)

    printer = get_printer(**kwargs)
    valid = Validate(cluster, search_pillar=True, search_grains=True,
                     printer=printer, search=search)
    valid.config_check()
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

    # Restrict search to this cluster
    search = "I@cluster:{}".format(cluster)

    printer = get_printer(**kwargs)
    valid = Validate(cluster, search_pillar=True, search_grains=True,
                     printer=printer, search=search)
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
    printer = get_printer(**kwargs)

    valid = Validate("deploy", search_pillar=True, search_grains=True,
                     printer=printer)
    valid.openattic()
    valid.kernel()
    valid.report()

    if valid.errors:
        return False

    return True


def saltapi(**kwargs):
    """
    Verify that the Salt API is working
    """
    printer = get_printer(**kwargs)
    valid = Validate("salt-api", search_pillar=True, printer=printer)
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
    Check that initial files prior to any stage are correct.  These
    validations are intended for fresh deployments.  Skip automatic
    checks on working clusters.
    """
    printer = get_printer(**kwargs)
    if ('bypass' in kwargs and kwargs['bypass'] and
        __salt__['cephprocesses.mon']()):
        # Disable all Salt lookups
        valid = Validate("setup", search_pillar=False, search_grains=False,
                         skip_init=True, printer=printer)
        valid.skip('deepsea_minions')
        valid.skip('master_minion')
        valid.skip('ceph_version')
        valid.skip('salt_version')
        valid.report()
        return True
    valid = Validate("setup", search_pillar=True, printer=printer)
    valid.deepsea_minions()
    valid.master_minion()
    valid.ceph_version()
    valid.salt_version()
    valid.report()

    if valid.errors:
        return False

    return True

__func_alias__ = {
                 'help_': 'help',
                 }
