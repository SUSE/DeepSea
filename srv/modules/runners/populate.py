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

import salt.client
import salt.key
import salt.config
import salt.utils
import salt.utils.minions
# pylint: disable=relative-import
import ready

import re
import pprint
import string
import random
from subprocess import call, Popen, PIPE
import yaml
import json
from os.path import dirname, basename, isdir
import os
import struct
import time
import base64
import errno
import uuid
import ipaddress
import logging
# pylint: disable=relative-import
import deepsea_minions
import operator

import sys

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
from cStringIO import StringIO


log = logging.getLogger(__name__)


class Settings(object):
    """
    Common settings
    """

    def __init__(self):
        """
        Assign root_dir, salt __opts__ and stack configuration.  (Stack
        configuration is not used currently.)
        """
        __opts__ = salt.config.client_config('/etc/salt/master')
        self.__opts__ = __opts__

        for ext in __opts__['ext_pillar']:
            if 'stack' in ext:
                self.stack = ext['stack']
        self.root_dir = "/srv/pillar/ceph/proposals"


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

    def write(self, filename, contents):
        """
        Write a yaml file in the conventional way
        """
        if self.overwrite or not os.path.isfile(filename):
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
        self.writer.write(filename, contents)

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
        return "-".join(sorted(quantities, cmp=self._model_sort))

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
            return cmp(x.group(2), y.group(2))


class DiskConfiguration(object):
    """
    All servers with free disks will become storage nodes
    """

    def __init__(self, options, servers=None):
        """
        Track proposals, default server list to mine data.
        """
        self.proposals = {}
        self.storage_nodes = {}
        if servers:
            for server in servers:
                ret = salt.utils.minions.mine_get(server, 'cephdisks.list',
                                                  'glob', options.__opts__)
                # what if server of servers returns anything -> no profile, no notification
                self.storage_nodes.update(ret)
        else:
            ret = salt.utils.minions.mine_update('*', '', 'glob',
                                                 options.__opts__)
            self.storage_nodes = salt.utils.minions.mine_get('*',
                                                             'cephdisks.list',
                                                             'glob',
                                                             options.__opts__)

        self.servers = self.storage_nodes

    def generate(self, hardwareprofile):
        """
        Add a hardware profile for each server.  Create proposals for each
        profile. Create a proposal of all OSDs and OSDs with journals if
        possible.
        """
        self.hardware = hardwareprofile
        for server in self.storage_nodes:
            self.hardware.add(server, self.storage_nodes[server])

        for server in self.hardware.profiles:
            if server not in self.proposals:
                self.proposals[server] = {}
            for configuration in self.hardware.profiles[server]:
                if configuration not in self.proposals[server]:
                    self.proposals[server][configuration] = []

                drives = self.hardware.profiles[server][configuration]

                log.debug("configuration {} with no journals".format(configuration))
                self.proposals[server][configuration].append(self._assignments(drives))
                for drive_model in drives:
                    # How many types of drives are SSDs, NVMes
                    if self.hardware.rotates[drive_model] == '0':
                        log.debug(("configuration {} with {} "
                                   "journal".format(configuration, drive_model)))
                        proposal = self._assignments(drives, drive_model)
                        if proposal:
                            self.proposals[server][configuration].append(proposal)
                        else:
                            log.warning(("No proposal for {} as journal on "
                                         "{}".format(drive_model,
                                                     configuration)))

    def _log_results(self, label, results):
        """
        """
        log.debug("{}:".format(label))
        for k in results:
            log.debug(" {}:".format(k))
            if k == 'data+journals':
                for entry in results[k]:
                    for d in entry:
                        log.debug("  {}:".format(d))
                        log.debug("   {}".format(entry[d]))
            else:
                for d in results[k]:
                    log.debug("  {}".format(d))

    def _assignments(self, drives, journal=None):
        """
        For a set of drives and designated journals (including none), assign
        the devices to the various drive types.  The types are

            osds = data + journal on same device
            data+journals = data + journal on separate devices
        """
        assignments, data, journals = self._separate_drives(drives, journal)

        log.debug("osds:")
        for osd in assignments['osds']:
            log.debug(" {}".format(osd))
        log.debug("data:")
        for d in data:
            log.debug(" {}".format(d))
        log.debug("journals:")
        for j in journals:
            log.debug(" {}".format(j))

        # check that data drives can be evenly divided by 6-3
        if journal:
            # How to make this configurable, where to retrieve any
            # configuration, etc. - placeholder for customization

            results = self._nice_ratio(assignments, data, journals)
            if results:
                self._log_results("nice ratio", results)
                return results

            results = self._rounding(assignments, data, journals)
            if results:
                self._log_results("rounding", results)
                return results

            # No suggestion
            return {}
        else:
            return assignments

    def _separate_drives(self, drives, journal):
        """
        Put a drive in one of three queues: osd, data or journal
        """
        assignments = {'osds': [], 'data+journals': []}
        data = []
        journals = []
        for drive_model in drives:
            # check capacity
            if drive_model == journal:
                journals.extend(drives[drive_model])
            else:
                if self.hardware.rotates[drive_model] == '1':
                    if journal:
                        data.extend(drives[drive_model])
                    else:
                        assignments['osds'].extend(drives[drive_model])
                else:
                    if journal and self.hardware.nvme[journal]:
                        data.extend(drives[drive_model])
                    else:
                        # SSD, NVMe for tier caching
                        assignments['osds'].extend(drives[drive_model])
        return assignments, data, journals

    def _nice_ratio(self, assignments, data, journals):
        """
        Check if data drives are divisible by 6, 5, 4 or 3 and that we have
        sufficient journal drives.  Add unused journal drives as standalone
        osds.

        """
        for partitions in range(6, 2, -1):
            if data and len(data) % partitions == 0:
                if len(journals) >= len(data)/partitions:
                    log.debug("Using {} partitions on {}".format(partitions, journals))

                    return self._assign(partitions, assignments, data, journals)
                else:
                    log.debug("Not enough journals for {} partitions".format(partitions))
            else:
                log.debug("Skipping {} partitions".format(partitions))

    def _rounding(self, assignments, data, journals):
        """
        Divide the data drives by the journal drives and round up. Use if
        partitions are 3-6 inclusive.

        """
        partitions = len(data)/len(journals) + 1
        if partitions > 2 and partitions < 7:
            log.debug("Rounding... using {} partitions on {}".format(partitions, journals))
            return self._assign(partitions, assignments, data, journals)

    def _assign(self, partitions, assignments, data, journals):
        """
        Create the data+journal assignment from the data and journals arrays
        """
        index = 0
        count = 1
        for device in data:
            log.debug("device: {}".format(device))
            assignments['data+journals'].extend([{"{}".format(device):
                                                  "{}".format(journals[index])}])
            count += 1
            if (count - 1) % partitions == 0:
                log.debug("next journal")
                count = 1
                index += 1

        # Add unused journal drives as OSDs
        assignments['osds'].extend(journals[index:])
        return assignments


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
        target = deepsea_minions.DeepseaMinions()
        self.search = target.deepsea_minions

        self.networks = self._networks(self.servers)
        self.public_networks, self.cluster_networks = self.public_cluster(self.networks.copy())

        self.available_roles = ['storage']

    def _rgw_configurations(self):
        """
        Use the custom names for rgw configurations specified.  Otherwise,
        default to 'rgw'.
        """

        local = salt.client.LocalClient()

        _rgws = local.cmd(self.search, 'pillar.get', ['rgw_configurations'], expr_form="compound")
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
                              ['ganesha_configurations'], expr_form="compound")
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
        roles = ['admin', 'mon', 'mds', 'mgr', 'igw', 'openattic']
        roles += self._rgw_configurations()
        roles += self._ganesha_configurations()
        self.available_roles.extend(roles)

        for role in roles:
            role_dir = "{}/role-{}".format(self.root_dir, role)
            if not os.path.isdir(role_dir):
                _create_dirs(role_dir, self.root_dir)

            # All minions are not necessarily storage - see CephStorage
            if role != 'storage':
                self._role_assignment(role_dir, role)

    def _client_roles(self):
        """
        Allows admins to target non-Ceph minions
        """
        roles = [ 'client-cephfs', 'client-radosgw', 'client-iscsi', 'client-nfs', 'benchmark-rbd'  ]
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

    def monitor_members(self):
        """
        Create a file for mon_host and mon_initial_members
        """
        minion_dir = "{}/role-mon/stack/default/{}/minions".format(self.root_dir, self.cluster)
        self._add_pub_interface(minion_dir)

    def igw_members(self):
        """
        Create a file for igw hosts.

        Note: identical to above
        """
        minion_dir = "{}/role-igw/stack/default/{}/minions".format(self.root_dir, self.cluster)
        self._add_pub_interface(minion_dir)

    def _add_pub_interface(self, minion_dir):
        if not os.path.isdir(minion_dir):
            _create_dirs(minion_dir, self.root_dir)
        for server in self.servers:
            filename = minion_dir + "/" +  server + ".yml"
            contents = {}
            contents['public_address'] = self._public_interface(server)
            self.writer.write(filename, contents)

    def _public_interface(self, server):
        """
        Find the public interface for a server
        """
        for public_network in self.public_networks:
            public_net = ipaddress.ip_network(u'{}'.format(public_network))
            for entry in self.networks[public_net]:
                if entry[0] == server:
                    log.debug("Public interface for {}: {}".format(server, entry[2]))
                    return entry[2]
        return ""

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
            contents['fsid'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, os.urandom(32)))

            public_networks_str = ", ".join([str(n) for n in self.public_networks])
            cluster_networks_str = ", ".join([str(n) for n in self.cluster_networks])

            contents['public_network'] = public_networks_str
            contents['cluster_network'] = cluster_networks_str
            contents['available_roles'] = self.available_roles

            self.writer.write(filename, contents)

    def _networks(self, minions):
        """
        Create a dictionary of networks with tuples of minion name, network
        interface and current address.  (The network interface is not
        currently used.)
        """

        networks = {}
        local = salt.client.LocalClient()

        interfaces = local.cmd(self.search, 'network.interfaces', [], expr_form="compound")

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

        priorities = sorted(priorities, cmp=network_sort)

        # first step, find public networks using hostname -i in all minions
        public_addrs = []
        local = salt.client.LocalClient()
        cmd_result = local.cmd(self.search, 'cmd.run', ['hostname -i'], expr_form="compound")
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
        master_minion = None
        cmd_result = local.cmd(self.search, 'pillar.get', ['master_minion'], expr_form="compound")
        for _, value in cmd_result.items():
            master_minion = value
            break
        if not master_minion:
            raise Exception("No master_minion found in pillar")
        cmd_result = local.cmd(master_minion, 'grains.get', ['ipv4'], expr_form="compound")
        for _, addr_list in cmd_result.items():
            master_addrs.extend([ipaddress.ip_address(u'{}'.format(addr))
                                for addr in addr_list if not addr.startswith('127.')])
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
        priorities = sorted(priorities, cmp=network_sort)
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
        cmd_result = local.cmd(self.search, 'grains.get', ['ipv4'], expr_form="compound")
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
        return cmp(a[1], b[1])


class CephCluster(object):
    """
    Generate cluster assignment files
    """

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

        target = deepsea_minions.DeepseaMinions()
        search = target.deepsea_minions

        local = salt.client.LocalClient()
        self.minions = local.cmd(search, 'grains.get', ['id'], expr_form="compound")

        _rgws = local.cmd(search, 'pillar.get', ['rgw_configurations'], expr_form="compound")
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
        contents = {}
        contents['time_server'] = '{{pillar.get("master_minion")}}'
        contents['time_init'] = 'ntp'

        self.writer.write(filename, contents)


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
    settings = Settings()

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
        for minion, details in dc.storage_nodes.iteritems():
            print minion + ":"
            for drive in details:
                for k, v in drive.iteritems():
                    if k in fields:
                        if k == 'rotational':
                            if drive[k] == '1':
                                sys.stdout.write(" rotates")
                        else:
                            sys.stdout.write(" " + v)
                print


def help_():
    """
    Usage
    """
    usage = ('salt-run populate.proposals:\n\n'
             '    Generate the necessary configuration fragments for Salt\n'
             '\n\n'
             'salt-run populate.engulf_existing_cluster:\n\n'
             '    Convert an existing Ceph cluster to DeepSea\n'
             '\n\n')
    print usage
    return ""


def proposals(**kwargs):
    """
    Collect the hardware profiles, all possible role assignments and common
    configuration under /srv/pillar/ceph/proposals
    """
    settings = Settings()

    salt_writer = SaltWriter(**kwargs)

    ceph_cluster = CephCluster(settings, salt_writer, **kwargs)
    ceph_cluster.generate()

    for name in ceph_cluster.names:
        # Determine roles and save proposals
        ceph_roles = CephRoles(settings, name, ceph_cluster.minions, salt_writer)
        ceph_roles.generate()
        ceph_roles.cluster_config()
        ceph_roles.monitor_members()
        ceph_roles.igw_members()
    return [True]


def _replace_key_in_cluster_yml(key, val):
    """
    Replace proposed key/val in
    /srv/pillar/ceph/proposals/config/stack/default/ceph/cluster.yml
    Returns True/False.
    Appends the key/val if it doesn't already exist.
    """
    filename = "/srv/pillar/ceph/proposals/config/stack/default/ceph/cluster.yml"

    # Read in cluster.yml
    try:
        with open(filename) as f:
            cluster_yml = f.readlines()
            f.close()
    except:
        log.error("Failed to open {} for reading.".format(filename))
        return False

    # Replace the old fsid entry.
    cluster_yml = [key + ": " + val if key + ":" in line else line.strip() for line in cluster_yml]

    # Write out the new version.
    try:
        with open(filename, "w") as f:
            written = False
            for line in cluster_yml:
                print >> f, line
                if key + ":" in line:
                    written = True
            if not written:
                print >> f, key + ": " + val
            f.close()
    except:
        log.error("Failed to open {} for writing.".format(filename))
        return False

    return True


def _get_existing_cluster_network(addrs, public_network=None):
    """
    Based on the addrs dictionary { minion: [ipaddress] }, this function
    returns an address consisting of network prefix followed by the cidr
    prefix (ie. 10.0.0.0/24), or None.
    """
    target = deepsea_minions.DeepseaMinions()
    search = target.deepsea_minions

    local = salt.client.LocalClient()
    # Stores the derived network addresses (in CIDR notation) of all addresses contained in addrs.
    minion_networks = []
    # The network address (in CIDR notation) that we return after collapsing minion_networks,
    # or None.
    network = None

    # Grab network interfaces from salt.
    minion_network_interfaces = local.cmd(search, "network.interfaces", [], expr_form="compound")
    # Remove lo.
    for entry in minion_network_interfaces:
        try:
            del minion_network_interfaces[entry]["lo"]
        except:
            pass

    for minion, ipaddr in addrs.items():
        # Only continue if ipaddr is present.
        for i in ipaddr:
            for intf, data in minion_network_interfaces[minion].items():
                if "inet" in data:
                    for inet_data in data["inet"]:
                        if i == "0.0.0.0":
                            # If running on 0.0.0.0, assume we can use public_network
                            if public_network:
                                ip = ipaddress.ip_interface(u"{}".format(public_network))
                            else:
                                ip = ipaddress.ip_interface(u"{}/{}".format(i,
                                                                            inet_data["netmask"]))
                            minion_networks.append(str(ip.network))
                        elif inet_data["address"] == i:
                            ip = ipaddress.ip_interface(u"{}/{}".format(inet_data["address"],
                                                                        inet_data["netmask"]))
                            minion_networks.append(str(ip.network))

    # Check for consistency across all entries.
    if len(set(minion_networks)) == 1:
        # We have equal entries.
        network = minion_networks[0]
    else:
        # We have multiple possible networks.  This is liable to happen with OSDs
        # when there is a private cluster network.  Let's try to remove the public
        # network.
        minion_networks = [n for n in minion_networks if n != public_network]
        network = minion_networks[0] if len(set(minion_networks)) == 1 else None

    return network


def _replace_fsid_with_existing_cluster(fsid):
    """
    Replace proposed fsid with fsid of running cluster.
    Returns True/False.
    """
    return _replace_key_in_cluster_yml("fsid", fsid)


def _replace_public_network_with_existing_cluster(mon_addrs):
    """
    Replace proposed public_network with public_network of the running cluster.
    Returns { 'ret': True/False, 'public_network': string/None }
    """
    public_network = _get_existing_cluster_network(mon_addrs)
    if not public_network:
        log.error("Failed to determine cluster's public_network.")
        return {'ret': False, 'public_network': None}
    else:
        return {'ret': _replace_key_in_cluster_yml("public_network",
                                                   public_network),
                'public_network': public_network}


def _replace_cluster_network_with_existing_cluster(osd_addrs, public_network=None):
    """
    Replace proposed cluster_network with cluster_network of the running cluster.
    If a public_network is already provided, pass that along as a fallback for
    _get_existing_cluster_network() to use when cluster_network is found to
    be 0.0.0.0, and to filter the public_network from the derived cluster_network.
    Returns { 'ret': True/False, 'cluster_network': string/None }
    """
    cluster_network = _get_existing_cluster_network(osd_addrs, public_network)
    if not cluster_network:
        log.error("Failed to determine cluster's cluster_network.")
        return {'ret': False, 'cluster_network': None}
    else:
        return {'ret': _replace_key_in_cluster_yml("cluster_network",
                                                   cluster_network),
                'cluster_network': cluster_network}


def engulf_existing_cluster(**kwargs):
    """
    Assuming proposals() has already been run to collect hardware profiles and
    all possible role assignments and common configuration, this will generate
    a policy.cfg with roles and assignments reflecting whatever cluster is
    currently deployed.  It will also suck in all the keyrings so that they're
    present when the configure stage is run.

    This assumes your cluster is named "ceph".  If it's not, things will break.
    """
    local = salt.client.LocalClient()
    settings = Settings()
    salt_writer = SaltWriter(**kwargs)

    # Make sure deepsea_minions contains valid minions before proceeding with engulf.
    minions = deepsea_minions.DeepseaMinions()
    search = minions.deepsea_minions
    import validate
    validator = validate.Validate("ceph", local.cmd(search, 'pillar.items', [],
                                                    expr_form="compound"),
                                  [], validate.get_printer())
    validator.deepsea_minions(minions)
    if validator.errors:
        validator.report()
        return False

    policy_cfg = []

    # Check for firewall/apparmor.
    if not ready.check("ceph", True, search):
        return False

    # First, hand apply select Stage 0 functions
    local.cmd(search, "saltutil.sync_all", [], expr_form="compound")
    local.cmd(search, "state.apply", ["ceph.mines"], expr_form="compound")

    # Run proposals gathering directly.
    proposals()

    # Our imported hardware profile proposal path
    imported_profile = "profile-import"
    imported_profile_path = settings.root_dir + "/" + imported_profile

    # Used later on to compute cluster and public networks.
    mon_addrs = {}
    osd_addrs = {}

    ceph_conf = None
    previous_minion = None
    admin_minion = None

    mon_minions = []
    mgr_instances = []
    mds_instances = []
    rgw_instances = []

    for minion, info in local.cmd(search, "cephinspector.inspect", [],
                                  expr_form="compound").items():

        if type(info) is not dict:
            print "cephinspector.inspect failed on %s: %s" % (minion, info)
            return False

        if info["ceph_conf"] is not None:
            if ceph_conf is None:
                ceph_conf = info["ceph_conf"]
            else:
                if info["ceph_conf"] != ceph_conf:
                    # TODO: what's the best way to report errors from a runner?
                    print ("ceph.conf on {} doesn't match ceph.conf on "
                           "{}").format(minion, previous_minion)
                    return False
            previous_minion = minion

        is_admin = info["has_admin_keyring"]

        if admin_minion is None and is_admin:
            # We'll talk to this minion later to obtain keyrings
            admin_minion = minion

        is_master = local.cmd(minion, "pillar.get", ["master_minion"],
                              expr_form="compound")[minion] == minion

        if not info["running_services"] and not is_admin and not is_master:
            # No ceph services running, no admin key, not the master_minion,
            # don't assign it to the cluster
            continue

        policy_cfg.append("cluster-ceph/cluster/" + minion + ".sls")

        if is_master:
            policy_cfg.append("role-master/cluster/" + minion + ".sls")
        elif is_admin:
            policy_cfg.append("role-admin/cluster/" + minion + ".sls")

        if "ceph-mon" in info["running_services"]:
            mon_minions.append(minion)
            policy_cfg.append("role-mon/cluster/" + minion + ".sls")
            policy_cfg.append("role-mon/stack/default/ceph/minions/" + minion + ".yml")
            for minion, ipaddrs in local.cmd(minion,
                                             "cephinspector.get_minion_public_networks",
                                             [], expr_form="compound").items():
                mon_addrs[minion] = ipaddrs

        if "ceph-osd" in info["running_services"]:
            # Needs a storage profile assigned (which may be different
            # than the proposals deepsea has come up with, depending on
            # how things were deployed)
            ceph_disks = local.cmd(minion, "cephinspector.get_ceph_disks_yml",
                                   [], expr_form="compound")
            if not ceph_disks:
                log.error("Failed to get list of Ceph OSD disks.")
                return [False]

            for minion, store in ceph_disks.items():
                minion_yml_dir = imported_profile_path + "/stack/default/ceph/minions"
                minion_yml_path = minion_yml_dir + "/" + minion + ".yml"
                _create_dirs(minion_yml_dir, "")
                salt_writer.write(minion_yml_path, store)

                minion_sls_data = {"roles": ["storage"]}
                minion_sls_dir = imported_profile_path + "/cluster"
                minion_sls_path = minion_sls_dir + "/" + minion + ".sls"
                _create_dirs(minion_sls_dir, "")
                salt_writer.write(minion_sls_path, minion_sls_data)

                policy_cfg.append(minion_sls_path[minion_sls_path.find(imported_profile):])
                policy_cfg.append(minion_yml_path[minion_yml_path.find(imported_profile):])

            for minion, ipaddrs in local.cmd(minion,
                                             "cephinspector.get_minion_cluster_networks",
                                             [], expr_form="compound").items():
                osd_addrs[minion] = ipaddrs

        if "ceph-mgr" in info["running_services"]:
            policy_cfg.append("role-mgr/cluster/" + minion + ".sls")
            for i in info["running_services"]["ceph-mgr"]:
                mgr_instances.append(i)

        if "ceph-mds" in info["running_services"]:
            policy_cfg.append("role-mds/cluster/" + minion + ".sls")
            for i in info["running_services"]["ceph-mds"]:
                mds_instances.append(i)

        if "ceph-radosgw" in info["running_services"]:
            policy_cfg.append("role-rgw/cluster/" + minion + ".sls")
            for i in info["running_services"]["ceph-radosgw"]:
                rgw_instances.append(i)

        # TODO: what else to do for rgw?  Do we need to do something to
        # populate rgw_configurations in pillar data?

    if not admin_minion:
        print "No nodes found with ceph.client.admin.keyring"
        return False

    # TODO: this is really not very DRY...
    admin_keyring = local.cmd(admin_minion, "cephinspector.get_keyring",
                              ["key=client.admin"],
                              expr_form="compound")[admin_minion]
    if not admin_keyring:
        print "Could not obtain client.admin keyring"
        return False

    mon_keyring = local.cmd(admin_minion, "cephinspector.get_keyring",
                            ["key=mon."], expr_form="compound")[admin_minion]
    if not mon_keyring:
        print "Could not obtain mon keyring"
        return False

    osd_bootstrap_keyring = local.cmd(admin_minion, "cephinspector.get_keyring",
                                      ["key=client.bootstrap-osd"],
                                      expr_form="compound")[admin_minion]
    if not osd_bootstrap_keyring:
        print "Could not obtain osd bootstrap keyring"
        return False

    # If there's no MGR instances, add MGR roles automatically to all the MONs
    # (since Luminous, MGR is a requirement, so it seems reasonable to add this
    # role automatically for imported clusters)
    if not mgr_instances:
        print "No MGRs detected, automatically assigning role-mgr to MONs"
        for minion in mon_minions:
            policy_cfg.append("role-mgr/cluster/" + minion + ".sls")

    with open("/srv/salt/ceph/admin/cache/ceph.client.admin.keyring", 'w') as keyring:
        keyring.write(admin_keyring)

    with open("/srv/salt/ceph/mon/cache/mon.keyring", 'w') as keyring:
        # following srv/salt/ceph/mon/files/keyring.j2, this includes both mon
        # and admin keyrings
        keyring.write(mon_keyring)
        keyring.write(admin_keyring)

    with open("/srv/salt/ceph/osd/cache/bootstrap.keyring", 'w') as keyring:
        keyring.write(osd_bootstrap_keyring)

    for i in mgr_instances:
        mgr_keyring = local.cmd(admin_minion, "cephinspector.get_keyring",
                                ["key=mgr." + i],
                                expr_form="compound")[admin_minion]
        if not mgr_keyring:
            print "Could not obtain mgr." + i + " keyring"
            return False
        with open("/srv/salt/ceph/mgr/cache/" + i + ".keyring", 'w') as keyring:
            keyring.write(mgr_keyring)

    for i in mds_instances:
        mds_keyring = local.cmd(admin_minion, "cephinspector.get_keyring",
                                ["key=mds." + i], expr_form="compound")[admin_minion]
        if not mds_keyring:
            print "Could not obtain mds." + i + " keyring"
            return False
        with open("/srv/salt/ceph/mds/cache/" + i + ".keyring", 'w') as keyring:
            keyring.write(mds_keyring)

    for i in rgw_instances:
        rgw_keyring = local.cmd(admin_minion, "cephinspector.get_keyring",
                                ["key=client." + i], expr_form="compound")[admin_minion]
        if not rgw_keyring:
            print "Could not obtain client." + i + " keyring"
            return False
        with open("/srv/salt/ceph/rgw/cache/client." + i + ".keyring", 'w') as keyring:
            keyring.write(rgw_keyring)

    # Now policy_cfg reflects the current deployment, make it a bit legible...
    policy_cfg.sort()

    # ...but inject the unassigned line first so it takes precendence,
    # along with the global config bits (because they're prettier early)...
    policy_cfg = ["cluster-unassigned/cluster/*.sls",
                  "config/stack/default/ceph/cluster.yml",
                  "config/stack/default/global.yml"] + policy_cfg

    # ...and write it out (this will fail with EPERM if someone's already
    # created a policy.cfg as root, BTW)
    with open("/srv/pillar/ceph/proposals/policy.cfg", 'w') as policy:
        policy.write("\n".join(policy_cfg) + "\n")

    # We've also got a ceph.conf to play with
    cp = configparser.RawConfigParser()
    # This little bit of natiness strips whitespace from all the lines, as
    # Python's configparser interprets leading whitespace as a line continuation,
    # whereas ceph itself is happy to have leading whitespace.
    cp.readfp(StringIO("\n".join([line.strip() for line in ceph_conf.split("\n")])))

    if not cp.has_section("global"):
        print "ceph.conf is missing [global] section"
        return False
    if not cp.has_option("global", "fsid"):
        print "ceph.conf is missing fsid"
        return False

    if not _replace_fsid_with_existing_cluster(cp.get("global", "fsid")):
        log.error("Failed to replace derived fsid with fsid of existing cluster.")
        return [False]

    p_net_dict = _replace_public_network_with_existing_cluster(mon_addrs)
    if not p_net_dict['ret']:
        log.error(("Failed to replace derived public_network with "
                   "public_network of existing cluster."))
        return [False]

    c_net_dict = _replace_cluster_network_with_existing_cluster(osd_addrs,
                                                                p_net_dict['public_network'])
    if not c_net_dict['ret']:
        log.error(("Failed to replace derived cluster_network with "
                   "cluster_network of existing cluster."))
        return [False]

    # write out the imported ceph.conf
    with open("/srv/salt/ceph/configuration/files/ceph.conf.import", 'w') as conf:
        conf.write(ceph_conf)

    # ensure the imported config will be used
    _replace_key_in_cluster_yml("configuration_init", "default-import")

    return True

__func_alias__ = {
                 'help_': 'help',
                 }
