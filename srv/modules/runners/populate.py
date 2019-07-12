# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4
# pylint: skip-file
# pylint: disable=too-few-public-methods,modernize-parse-error
"""
WHY THIS RUNNER EXISTS:

For a set of servers, multiple Ceph configurations are possible.  Enumerating
all of them would generate so many that the useful would be lost in the noise.
Rather than following a template of a contrived example, this utility creates
all the possible configuration files for each server of the existing equipment.
This should help those that can never seem to get their YAML indentation correct.

Second, all the complexity of combining these files is kept in a policy.cfg at
the root of /srv/pillar/ceph/proposals.  Assigning multiple roles to the same
server or keeping them separate is controlled by specifying which files to
include in the policy.cfg.  Preinstalling a policy.cfg will allow the automatic
creation of a Ceph cluster.

See the partner runner push.proposal for details.

"""

from __future__ import absolute_import
from __future__ import print_function
import salt.client
import salt.key
import salt.config
import salt.utils
import salt.utils.minions
import salt.loader
# pylint: disable=relative-import
import re
import string
import random
import yaml
import json
from os.path import dirname, basename, isdir
import os
import struct
import time
from base64 import b64encode
import errno
import uuid
import ipaddress
import logging
# pylint: disable=relative-import
import operator
import pprint

import sys
import six
from six.moves import range
from functools import reduce, cmp_to_key

try:
    import configparser
except ImportError:
    import six.moves.configparser as configparser


log = logging.getLogger(__name__)


def _cmp(x, y):
    """
    Replacement for built-in function cmp that was removed in Python 3

    Compare the two objects x and y and return an integer according to
    the outcome. The return value is negative if x < y, zero if x == y
    and strictly positive if x > y.
    """

    return (x > y) - (x < y)


class SaltWriter(object):
    """
    All salt files are essentially yaml files in the pillar by default.  The
    pillar uses sls extensions and stack.py uses yml.
    """

    def __init__(self, **kwargs):
        """
        Keep yaml human readable/editable.  Disable yaml references.
        """
        self.dumper = yaml.SafeDumper
        self.dumper.ignore_aliases = lambda self, data: True

        if 'overwrite' in kwargs:
            self.overwrite = kwargs['overwrite']
        else:
            self.overwrite = False

    def write(self, filename, contents, overwrite=False):
        """
        Write a yaml file in the conventional way
        """
        if self.overwrite or not os.path.isfile(filename) or overwrite:
            log.info("Writing {}".format(filename))
            with open(filename, "w") as yml:
                yml.write(yaml.dump(contents, Dumper=self.dumper,
                          default_flow_style=False))


class CephStorage(object):
    """
    Manage the creation of the storage related files
    """

    def __init__(self, settings, cluster, writer):
        """
        Track cluster name, writer, root directory and a keyring secret
        """
        self.cluster = cluster
        self.writer = writer

        self.root_dir = settings.root_dir
        # self.keyring = Utils.secret()

    def save(self, servers, _proposals):
        """
        Save each proposal for each server of each model
        """
        count = 0
        # log.debug("model: {}".format(model))
        for server in _proposals:
            for model in _proposals[server]:
                for proposal in _proposals[server][model]:
                    count += 1
                    name = 'profile-{}-{}'.format(model, str(count))
                    self._save_proposal(name, server, proposal)
                    self._save_roles(name, server)
            count = 0

    def _save_proposal(self, name, server, storage):
        """
        Save the storage data structure for each server
        """
        model_dir = "{}/{}/stack/default/{}/minions".format(self.root_dir, name, self.cluster)
        if not os.path.isdir(model_dir):
            _create_dirs(model_dir, self.root_dir)
        filename = model_dir + "/" +  server + ".yml"
        contents = {'storage': storage}
        self.writer.write(filename, contents, True)

    def _save_roles(self, name, server):
        """
        Save the storage role for each server
        """
        cluster_dir = "{}/{}/cluster".format(self.root_dir, name)
        if not os.path.isdir(cluster_dir):
            _create_dirs(cluster_dir, self.root_dir)
        # filename = cluster_dir + "/" +  server.split('.')[0] + ".sls"
        filename = cluster_dir + "/" +  server + ".sls"
        contents = {}
        contents['roles'] = ['storage']
        self.writer.write(filename, contents)


class HardwareProfile(object):
    """
    Create a hardware profile based on the quantity and order of drives
    """

    def __init__(self):
        """
        Track profiles, servers and rotating media
        """
        self.profiles = {}
        self.servers = {}
        self.rotates = {}
        self.nvme = {}

    def add(self, hostname, drives):
        """
        Add a profile by label
        """
        self.model = {}
        for drive in drives:
            if 'Vendor' in drive:
                label = self._label(drive['Vendor'], drive['Capacity'])
            else:
                # Virtual machines do not have vendors
                label = self._label(drive['Model'], drive['Capacity'])

            if label not in self.rotates:
                self.rotates[label] = drive['rotational']
            if label not in self.nvme:
                # lshw can't detect the driver
                self.nvme[label] = (drive['Driver'] == "nvme")

            if label in self.model:
                self.model[label].append(self._device(drive))
            else:
                self.model[label] = [self._device(drive)]
        name = self._name()
        self._profiles(name, hostname)

    def _device(self, drive):
        """
        Default to Device File value.  Use by-id if available.
        """
        device = drive['Device File']
        if 'Device Files' in drive:
            for path in drive['Device Files'].split(', '):
                if 'by-id' in path:
                    device = path
                    break
        return device

    def _label(self, vendor, capacity):
        """
        Use a single word for vendor. Strip spaces from capacity.
        """
        if ' ' in vendor:
            vendor = self._brand(vendor)
        return vendor + re.sub(' ', '', capacity)

    def _brand(self, vendor):
        """
        Some vendor strings are multiple words.
        """
        if re.search(r'intel', vendor, re.IGNORECASE):
            return "Intel"
        # Use last word for no matches
        return vendor.split()[-1]

    def _profiles(self, name, hostname):
        """
        Assign hardware profiles
        """
        # if name in self.servers:
        #     self.servers[name].append(hostname)
        # else:
        #     self.servers[name] = [hostname]
        if hostname not in self.profiles:
            self.profiles[hostname] = {}
        if name not in self.profiles[hostname]:
            self.profiles[hostname][name] = {}
        for label in self.model:
            if label not in self.profiles[hostname][name]:
                self.profiles[hostname][name][label] = {}
            self.profiles[hostname][name][label] = self.model[label]

    def _name(self):
        """
        Create a consistent name by sorting the drive types
        """
        quantities = {}
        for label in self.model:
            quantities[str(len(self.model[label])) + label] = ""
        return "-".join(sorted(quantities, key=cmp_to_key(self._model_sort)))

    # pylint: disable=invalid-name
    def _model_sort(self, a, b):
        """
        Sort by numeric, then alpha
        """
        x = re.match(r'(\d+)(\D+)', a)
        y = re.match(r'(\d+)(\D+)', b)
        if int(x.group(1)) < int(y.group(1)):
            return -1
        elif int(x.group(1)) > int(y.group(1)):
            return 1
        else:
            return _cmp(x.group(2), y.group(2))



class CephRoles(object):
    """
    Create reasonable proposals from the existing hardware
    """

    def __init__(self, settings, cluster, servers, writer):
        """
        Initialize role secrets, track parameters
        """
        self.cluster = cluster
        self.servers = servers
        self.writer = writer

        self.root_dir = settings.root_dir
        self.search = __utils__['deepsea_minions.show']()

        if self.publicnetwork_is_ipv6():
            log.info("Public IPv6 network: {}".format(self.public_networks))
            log.info("Cluster IPv6 network: {}".format(self.cluster_networks))
        else:
            log.info("Autodetecting IPv4 defaults")
            self.networks = self._networks(self.servers)
            self.public_networks, self.cluster_networks = self.public_cluster(self.networks.copy())

        self.available_roles = ['storage']

    def _rgw_configurations(self):
        """
        Use the custom names for rgw configurations specified.  Otherwise,
        default to 'rgw'.
        """

        local = salt.client.LocalClient()

        _rgws = local.cmd(self.search, 'pillar.get', ['rgw_configurations'], tgt_type="compound")
        for node in _rgws:
            if _rgws[node]:
                return _rgws[node]
        return ['rgw']

    def _ganesha_configurations(self):
        """
        Use the custom names for ganesha configurations specified.  Otherwise,
        default to 'ganesha'.
        """
        local = salt.client.LocalClient()

        _ganeshas = local.cmd(self.search, 'pillar.get',
                              ['ganesha_configurations'], tgt_type="compound")
        for node in _ganeshas:
            # Check the first one
            if _ganeshas[node]:
                return _ganeshas[node]
            else:
                return ['ganesha']

    def generate(self):
        """
        Create role named directories and create corresponding yaml files
        for every server.
        """
        self._standard_roles()
        self._client_roles()
        self._master_role()

    def _standard_roles(self):
        """
        Create role named directories and create corresponding yaml files
        for every server.
        """
        roles = ['admin', 'mon', 'mds', 'mgr', 'igw', 'grafana', 'prometheus', 'storage']
        roles += self._rgw_configurations()
        roles += self._ganesha_configurations()
        self.available_roles.extend(roles)

        for role in roles:
            role_dir = "{}/role-{}".format(self.root_dir, role)
            if not os.path.isdir(role_dir):
                _create_dirs(role_dir, self.root_dir)

            self._role_assignment(role_dir, role)

    def _client_roles(self):
        """
        Allows admins to target non-Ceph minions
        """
        roles = [ 'client-cephfs', 'client-radosgw', 'client-iscsi',
                  'client-nfs', 'benchmark-rbd', 'benchmark-blockdev',
                  'benchmark-fs' ]
        self.available_roles.extend(roles)

        for role in roles:
            role_dir = "{}/role-{}".format(self.root_dir, role)
            self._role_assignment(role_dir, role)

    def _master_role(self):
        """
        The master role can access all keyring secrets
        """
        role = 'master'
        self.available_roles.extend([role])

        role_dir = "{}/role-{}".format(self.root_dir, role)
        self._role_assignment(role_dir, role)

    def _role_mapping(self, role):
        """
        The storage role has osd keyrings.
        """
        if role == 'storage':
            return 'osd'
        return role

    def _role_assignment(self, role_dir, role):
        """
        Create role related sls files
        """
        cluster_dir = role_dir + "/cluster"
        if not os.path.isdir(cluster_dir):
            _create_dirs(cluster_dir, self.root_dir)
        for server in self.servers:
            filename = cluster_dir + "/" +  server + ".sls"
            contents = {}
            contents['roles'] = [role]
            self.writer.write(filename, contents)

    def cluster_config(self):
        """
        Provide the default configuration for a cluster
        """
        if self.cluster:
            cluster_dir = "{}/config/stack/default/{}".format(self.root_dir, self.cluster)
            if not os.path.isdir(cluster_dir):
                _create_dirs(cluster_dir, self.root_dir)
            filename = "{}/cluster.yml".format(cluster_dir)
            contents = {}
            fsid = str(uuid.uuid4())
            if os.path.isfile(filename):
                with open(filename, "r") as yml:
                    old_contents = yaml.load(yml)
                fsid = old_contents.get('fsid', fsid)
            contents['fsid'] = fsid
            public_networks_str = ", ".join([str(n) for n in self.public_networks])
            cluster_networks_str = ", ".join([str(n) for n in self.cluster_networks])

            contents['public_network'] = public_networks_str
            contents['cluster_network'] = cluster_networks_str
            contents['available_roles'] = self.available_roles

            self.writer.write(filename, contents, True)

    def publicnetwork_is_ipv6(self):
        """
        Check if public_network is an IPv6. Accept the cluster network as is
        or default it to the same value as the public_network.

        Validation of all networks occurs in validate.py
        """
        local = salt.client.LocalClient()
        data = local.cmd(self.search , 'pillar.items', [], tgt_type="compound")
        minion_values = list(data.values())[0]
        log.debug("minion_values: {}".format(pprint.pformat(minion_values)))

        if 'public_network' in minion_values:
            # Check first entry if comma delimited
            public_network = minion_values['public_network'].split(',')[0]
            try:
                network = ipaddress.ip_network(u'{}'.format(public_network))
            except ValueError as err:
                log.error("Public network {}".format(err))
                return False
            if network.version == 6:
                self.public_networks = minion_values['public_network']
                if 'cluster_network' in minion_values:
                    self.cluster_networks = minion_values['cluster_network']
                else:
                    self.cluster_networks = minion_values['public_network']
                return True
        return False

    def _networks(self, minions):
        """
        Create a dictionary of networks with tuples of minion name, network
        interface and current address.  (The network interface is not
        currently used.)
        """

        networks = {}
        local = salt.client.LocalClient()

        interfaces = local.cmd(self.search, 'network.interfaces', [], tgt_type="compound")

        for minion in interfaces:
            for nic in interfaces[minion]:
                if 'inet' in interfaces[minion][nic]:
                    for addr in interfaces[minion][nic]['inet']:
                        if addr['address'].startswith('127'):
                            # Skip loopbacks
                            continue
                        cidr = self._network(addr['address'], addr['netmask'])
                        if cidr in networks:
                            networks[cidr].append((minion, nic, addr['address']))
                        else:
                            networks[cidr] = [(minion, nic, addr['address'])]
        return networks

    def _network(self, address, netmask):
        """
        Return CIDR network
        """
        return ipaddress.ip_interface(u'{}/{}'.format(address, netmask)).network

    def public_cluster(self, networks):
        """
        Guess which network is public and which network is cluster. The
        public network should have the greatest quantity since the cluster
        network is not required for some roles.  If those are equal, pick
        the lowest numeric address.

        Other strategies could include prioritising private addresses or
        interface speeds.  However, this will be wrong for somebody.
        """
        public_networks = []
        cluster_networks = []

        priorities = []
        for network in networks:
            quantity = len(networks[network])
            priorities.append((quantity, network))

        if not priorities:
            raise ValueError("No network exists on at least 4 nodes")

        priorities = sorted(priorities, key=cmp_to_key(network_sort))

        # first step, find public networks using hostname -i in all minions
        public_addrs = []
        local = salt.client.LocalClient()
        cmd_result = local.cmd(self.search, 'cmd.run', ['hostname -i'], tgt_type="compound")
        for _, addrs in cmd_result.items():
            addr_list = addrs.split(' ')
            public_addrs.extend([ipaddress.ip_address(u'{}'.format(addr))
                                 for addr in addr_list if not addr.startswith('127.')])
        for _, network in priorities:
            if reduce(operator.__or__, [addr in network for addr in public_addrs], False):
                public_networks.append(network)
        for network in public_networks:
            networks.pop(network)

        # second step, find cluster network by checking which network salt-master does not belong
        master_addrs = []
        __opts__ = salt.config.minion_config('/etc/salt/minion')
        __grains__ = salt.loader.grains(__opts__)
        master_addrs.extend([ipaddress.ip_address(u'{}'.format(addr))
                            for addr in __grains__['ipv4'] if not addr.startswith('127.')])
        for _, network in priorities:
            if network not in networks:
                continue
            if reduce(operator.__and__, [addr not in network for addr in master_addrs], True) and \
               len(networks[network]) > 1:
                cluster_networks.append(network)
        for network in cluster_networks:
            networks.pop(network)

        # third step, map remaining networks
        priorities = []
        for network in networks:
            quantity = len(networks[network])
            priorities.append((quantity, network))
        priorities = sorted(priorities, key=cmp_to_key(network_sort))
        for idx, (quantity, network) in enumerate(priorities):
            if cluster_networks or quantity == 1:
                public_networks.append(network)
            else:
                if not public_networks:
                    public_networks.append(network)
                else:
                    cluster_networks.append(network)

        # fourth step, remove redudant public networks
        filtered_list = []
        cmd_result = local.cmd(self.search, 'grains.get', ['ipv4'], tgt_type="compound")
        for network in public_networks:
            to_remove = []
            for key, addr_list in cmd_result.items():
                if reduce(operator.__or__,
                          [ipaddress.ip_address(u'{}'.format(addr)) in network
                           for addr in addr_list],
                          False):
                    to_remove.append(key)
            for key in to_remove:
                cmd_result.pop(key)
            filtered_list.append(network)
            if not cmd_result:
                break
        public_networks = filtered_list

        if not cluster_networks:
            cluster_networks = public_networks

        return public_networks, cluster_networks


def network_sort(a, b):
    """
    Sort quantity descending and network ascending.
    """
    if a[0] < b[0]:
        return 1
    elif a[0] > b[0]:
        return -1
    else:
        return _cmp(a[1], b[1])


class CephCluster(object):
    """
    Generate cluster assignment files
    """

    monitoring_default_config = {'monitoring': {
        'prometheus': {
            'rule_files': [],
            'scrape_interval': {
                'ceph': '10s',
                'node_exporter': '10s',
                'prometheus': '10s',
                'grafana': '10s'},
            'relabel_config': {
                'ceph': [],
                'node_exporter': [],
                'prometheus': [],
                'grafana': []},
            'metric_relabel_config': {
                'ceph': [],
                'node_exporter': [],
                'prometheus': [],
                'grafana': []},
            'target_partition': {
                'ceph': '1/1',
                'node_exporter': '1/1',
                'prometheus': '1/1',
                'grafana': '1/1'}
        }}}

    def __init__(self, settings, writer, **kwargs):
        """
        Track cluster names, set minions to actively responding minions

        Allow overriding of default cluster
        """
        self.root_dir = settings.root_dir
        if 'cluster' in kwargs:
            self.names = kwargs['cluster']
        else:
            self.names = ['ceph']
        self.writer = writer

        self.search = __utils__['deepsea_minions.show']()

        local = salt.client.LocalClient()
        self.minions = local.cmd(self.search, 'grains.get', ['id'], tgt_type="compound")

        _rgws = local.cmd(self.search, 'pillar.get', ['rgw_configurations'], tgt_type="compound")
        for node in _rgws:
            self.rgw_configurations = _rgws[node]
            # Just need first
            break

    def generate(self):
        """
        Create cluster assignment for every cluster and unassigned
        """
        self._assignments()
        self._global()

    def _assignments(self):
        """
        Create cluster assignment for every cluster and unassigned
        """
        for cluster in self.names + ['unassigned']:
            for minion in self.minions:
                cluster_dir = "{}/cluster-{}/cluster".format(self.root_dir, cluster)
                if not os.path.isdir(cluster_dir):
                    _create_dirs(cluster_dir, self.root_dir)
                filename = "{}/{}.sls".format(cluster_dir, minion)
                contents = {}
                contents['cluster'] = cluster

                self.writer.write(filename, contents)

    def _global(self):
        """
        Specify global options for all clusters
        """
        stack_dir = "{}/config/stack/default".format(self.root_dir)
        if not os.path.isdir(stack_dir):
            _create_dirs(stack_dir, self.root_dir)
        filename = "{}/global.yml".format(stack_dir)

        __opts__ = salt.config.client_config('/etc/salt/master')
        __grains__ = salt.loader.grains(__opts__)
        __opts__['grains'] = __grains__
        __utils__ = salt.loader.utils(__opts__)
        __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)
        contents = {}
        contents['time_server'] = '{}'.format(__salt__['master.minion']())
        contents.update(self.monitoring_default_config)

        self.writer.write(filename, contents, True)


def _create_dirs(path, root):
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EACCES:
            log.exception('''
            ERROR: Cannot create dir {}
            Please make sure {} is owned by salt
            '''.format(path, root))
            raise err


def show(**kwargs):
    """
    Quick printing of usable disks

    Note: rearrange at some point
    """
    print ("DEPRECATION WARNING: the generation of storage profiles is now"
           " handled by the proposal runner. This function will go away in the"
           " future.")
    settings = __utils__['settings.self_']()

    salt_writer = SaltWriter(**kwargs)

    ceph_cluster = CephCluster(settings, salt_writer, **kwargs)
    ceph_cluster.generate()

    # Allow overriding of hardware profile class
    hardwareprofile = HardwareProfile()

    for name in ceph_cluster.names:
        # Common cluster configuration
        ceph_storage = CephStorage(settings, name, salt_writer)
        dc = DiskConfiguration(settings, servers=ceph_cluster.minions)
        fields = ['Capacity', 'Device File', 'Model', 'rotational']
        for minion, details in six.iteritems(dc.storage_nodes):
            print(minion + ":")
            for drive in details:
                for k, v in six.iteritems(drive):
                    if k in fields:
                        if k == 'rotational':
                            if drive[k] == '1':
                                sys.stdout.write(" rotates")
                        else:
                            sys.stdout.write(" " + v)
                print()


def help_():
    """
    Usage
    """
    usage = ('salt-run populate.proposals:\n\n'
             '    Generate the necessary configuration fragments for Salt\n'
             '\n\n')
    print(usage)
    return ""


def proposals(**kwargs):
    """
    Collect the hardware profiles, all possible role assignments and common
    configuration under /srv/pillar/ceph/proposals
    """
    settings = __utils__['settings.self_']()

    salt_writer = SaltWriter(**kwargs)

    ceph_cluster = CephCluster(settings, salt_writer, **kwargs)
    ceph_cluster.generate()

    for name in ceph_cluster.names:
        # Determine roles and save proposals
        ceph_roles = CephRoles(settings, name, ceph_cluster.minions, salt_writer)
        ceph_roles.generate()
        ceph_roles.cluster_config()
    return [True]


__func_alias__ = {
                 'help_': 'help',
                 }
