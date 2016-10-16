#!/usr/bin/python

import salt.client
import salt.key
import salt.config
import salt.utils
import salt.utils.minions

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


"""
WHY THIS RUNNER EXISTS:

For a set of servers, multiple Ceph configurations are possible.  Enumerating
all of them would generate so many that the useful would be lost in the noise.
Rather than following a template of a contrived example, this utility creates
all the possible configuration files for each server of the existing equipment.  This should help those that can never seem to get their YAML indentation correct.

Second, all the complexity of combining these files is kept in a policy.cfg at
the root of /srv/pillar/ceph/proposals.  Assigning multiple roles to the same
server or keeping them separate is controlled by specifying which files to 
include in the policy.cfg.  Preinstalling a policy.cfg will allow the automatic
creation of a Ceph cluster.

See the partner runner push.proposal for details.

"""

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


#class Utils(object):
#    """
#    Class for common methods
#    """
#
#    @staticmethod
#    def secret():
#        """
#        Generate a secret
#        """
#        #cmd = [ "/usr/bin/ceph-authtool", "--gen-print-key", "/dev/null" ]
#        #
#        #if not os.path.isfile(cmd[0]):
#        #    raise RuntimeError("Missing {} - install ceph package".format(cmd[0]))
#        #proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
#        #for line in proc.stdout:
#        #    return line.rstrip()
#        key = os.urandom(16) 
#        header = struct.pack('<hiih',1,int(time.time()),0,len(key)) 
#        return base64.b64encode(header + key) 

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
        #self.keyring = Utils.secret()


    def save(self, servers, proposals):
        """
        Save each proposal for each server of each model
        """
        count = 0
            #log.debug("model: {}".format(model))
        for server in proposals.keys():
            count += 1
            for model in proposals[server]:
                name = model + "-" + str(count)
                proposal = proposals[server][model]
                self._save_proposal(name, server, proposal)
                self._save_roles(name, server)
                #self._save_keyring(name)
            count = 0


    def _save_proposal(self, name, server, storage):
        """
        Save the storage data structure for each server
        """
        model_dir = "{}/{}/stack/default/{}/minions".format(self.root_dir, name, self.cluster)
        if not os.path.isdir(model_dir):
            create_dirs(model_dir, self.root_dir)
        filename = model_dir + "/" +  server + ".yml"
        contents = { 'storage': storage }
        self.writer.write(filename, contents)

    def _save_roles(self, name, server):
        """
        Save the storage role for each server
        """
        cluster_dir = "{}/{}/cluster".format(self.root_dir, name)
        if not os.path.isdir(cluster_dir):
            create_dirs(cluster_dir, self.root_dir)
        #filename = cluster_dir + "/" +  server.split('.')[0] + ".sls"
        filename = cluster_dir + "/" +  server + ".sls"
        contents = {}
        contents['roles'] =  [ 'storage' ]
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

            if not label in self.rotates:
                self.rotates[label] = drive['rotational']
            if not label in self.nvme:
                self.nvme[label] = (drive['Driver'] == "nvme")


            if label in self.model:
                self.model[label].append(self._device(drive))
            else:
                self.model[label] = [ self._device(drive) ]
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
        return  vendor + re.sub(' ', '', capacity)

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
        """
        #if name in self.servers:
        #    self.servers[name].append( hostname )
        #else:
        #    self.servers[name] = [ hostname ]
        if hostname not in self.profiles:
            self.profiles[hostname] = {}
        if name not in self.profiles[hostname]:
            self.profiles[hostname][name] = {}
        for label in self.model.keys():
            if label not in self.profiles[hostname][name]:
                self.profiles[hostname][name][label] = {}
            self.profiles[hostname][name][label] = self.model[label]

        
        
    def _name(self):
        """
        Create a consistent name by sorting the drive types
        """
        quantities = {}
        for label in self.model.keys():
            quantities[str(len(self.model[label])) + label] = ""
        return "-".join(sorted(quantities.keys(), cmp=self._model_sort))

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
                ret = salt.utils.minions.mine_get(server, 'cephdisks.list', 'glob', options.__opts__)
                self.storage_nodes.update(ret)
        else:
            # salt-call mine.get '*' freedisks.list
            ret = salt.utils.minions.mine_update('*', '', 'glob', options.__opts__)
            self.storage_nodes = salt.utils.minions.mine_get('*', 'cephdisks.list', 'glob', options.__opts__)


        self.servers = self.storage_nodes.keys()
        

    def generate(self, hardwareprofile):
        """
        Add a hardware profile for each server.  Create proposals for each
        profile. Create a proposal of all OSDs and OSDs with journals if
        possible.
        """
        self.hardware = hardwareprofile
        for server in self.storage_nodes:
            self.hardware.add(server, self.storage_nodes[server])

        for server in self.hardware.profiles.keys():
            if server not in self.proposals:
                self.proposals[server] = {}
            for configuration in self.hardware.profiles[server]:
                if configuration not in self.proposals[server]:
                    self.proposals[server][configuration] = []

                drives = self.hardware.profiles[server][configuration]

                log.debug("configuration {} with no journals".format(configuration))
                self.proposals[server][configuration].append(self._assignments(drives))
                for drive_model in drives.keys():
                    # How many types of drives are SSDs, NVMes
                    if self.hardware.rotates[drive_model] == '0':
                        log.debug("configuration {} with {} journal".format(configuration, drive_model))
                        proposal = self._assignments(drives, drive_model)
                        if proposal:
                            self.proposals[server][configuration].append(proposal)
                        else:
                            log.warning("No proposal for {} as journal on {}".format(drive_model, configuration))
        
       
        
    def _assignments(self, drives, journal=None):
        """
        For a set of drives and designated journals (including none), assign
        the devices to the various drive types.  The types are

            osds = data + journal on same device
            data+journals = data + journal on separate devices
        """
        assignments, data, journals = self._separate_drives(drives, journal)

        log.debug("osds: {}".format(assignments['osds']))
        log.debug("data: {}".format(data))
        log.debug("journals: {}".format(journals))
        # check that data drives can be evenly divided by 6-3
        if journal:
            # How to make this configurable, where to retrieve any 
            # configuration, etc. - placeholder for customization

            results = self._nice_ratio(journal, assignments, data, journals)
            if results:
                return results

            results = self._rounding(journal, assignments, data, journals)
            if results:
                return results

            # No suggestion
            return {}
        else:
            return assignments
            

    def _separate_drives(self, drives, journal):
        """
        Put a drive in one of three queues: osd, data or journal
        """
        assignments = { 'osds': [], 'data+journals': [] }
        data = []
        journals = []
        for drive_model in drives.keys():
            # check capacity
            if drive_model == journal:
                journals.extend(drives[drive_model])
            else:
                if self.hardware.rotates[drive_model] == 1:
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

    def _nice_ratio(self, journal, assignments, data, journals):
        """
        Check if data drives are divisible by 6, 5, 4 or 3 and that we have
        sufficient journal drives.  Add unused journal drives as standalone
        osds.
        
        """
        for partitions in range(6, 2, -1):
            if (data and len(data) % partitions == 0):
                if (len(journals) >= len(data)/partitions):
                    log.debug("Using {} partitions on {}".format(partitions, journal))

                    assignments.update(self._assign(partitions, assignments, data, journals))
                    # Add unused journal drives as OSDs
                    assignments['osds'].extend(journals[index:])
                    return assignments
                else:
                    log.debug("Not enough journals for {} partitions".format(partitions))
            else:
                log.debug("Skipping {} partitions".format(partitions))

    def _rounding(self, journal, assignments, data, journals):
        """
        Divide the data drives by the journal drives and round up. Use if
        partitions are 3-6 inclusive.
   
        """
        partitions = len(data)/len(journals) + 1
        if (partitions > 2 and partitions < 7):
            log.debug("Rounding... using {} partitions on {}".format(partitions, journal))
            return self._assign(partitions, assignments, data, journals)

    def _assign(self, partitions, assignments, data, journals):
        """
        Create the data+journal assignment from the data and journals arrays
        """
        index = 0
        count = 1
        for device in data:
            log.debug("device: {}".format(device))
            assignments['data+journals'].extend([ { "{}1".format(device):  "{}{}".format(journals[index], count) } ]) 
            count += 1
            if (count - 1) % partitions == 0:
                log.debug("next journal")
                count = 1
                index += 1
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
        self.networks = self._networks(self.servers)
        self.public_network, self.cluster_network = self.public_cluster(self.networks) 

        #self.master_contents = {}
        self.available_roles = []

    def _rgw_configurations(self):
        """
        Use the custom names for rgw configurations specified.  Otherwise,
        default to 'rgw'.
        """
        local = salt.client.LocalClient()

        # Should we add a master_minion lookup and have two calls instead?
        _rgws = local.cmd('*' , 'pillar.get', [ 'rgw_configurations' ])
        for node in _rgws.keys():
            # Check the first one
            if _rgws[node]:
                return _rgws[node]
            else:
                return [ 'rgw' ]

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
        roles = [ 'admin', 'mon', 'storage', 'mds', 'igw' ] + self._rgw_configurations()
        self.available_roles.extend(roles)

        for role in roles:
            role_dir = "{}/role-{}".format(self.root_dir, role)
            if not os.path.isdir(role_dir):
                create_dirs(role_dir, self.root_dir)

            # All minions are not necessarily storage - see CephStorage
            if role != 'storage':
                self._role_assignment(role_dir, role)

    def _client_roles(self):
        """
        Allows admins to target non-Ceph minions
        """
        roles = [ 'mds-client', 'rgw-client', 'igw-client', 'mds-nfs', 'rgw-nfs' ]
        self.available_roles.extend(roles)

        for role in roles:
            role_dir = "{}/role-{}".format(self.root_dir, role)
            self._role_assignment(role_dir, role)


    def _master_role(self):
        """
        The master role can access all keyring secrets
        """
        role = 'master'
        self.available_roles.extend([ role ])

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
            create_dirs(cluster_dir, self.root_dir)
        for server in self.servers:
            filename = cluster_dir + "/" +  server + ".sls"
            contents = {}
            contents['roles'] = [ role ]
            self.writer.write(filename, contents)

    def monitor_members(self):
        """
        Create a file for mon_host and mon_initial_members
        """
        minion_dir = "{}/role-mon/stack/default/{}/minions".format(self.root_dir, self.cluster)
        if not os.path.isdir(minion_dir):
            create_dirs(minion_dir, self.root_dir)
        for server in self.servers:
            filename = minion_dir + "/" +  server + ".yml"
            contents = {}
            contents['public_address'] = self._public_interface(server) 
            self.writer.write(filename, contents)

    def igw_members(self):
        """
        Create a file for igw hosts.

        Note: identical to above
        """
        minion_dir = "{}/role-igw/stack/default/{}/minions".format(self.root_dir, self.cluster)
        if not os.path.isdir(minion_dir):
            create_dirs(minion_dir, self.root_dir)
        for server in self.servers:
            filename = minion_dir + "/" +  server + ".yml"
            contents = {}
            contents['public_address'] = self._public_interface(server) 
            self.writer.write(filename, contents)

    def _public_interface(self, server):
        """
        Find the public interface for a server
        """
        public_net = ipaddress.ip_network(u'{}'.format(self.public_network))
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
                 create_dirs(cluster_dir, self.root_dir)
            filename = "{}/cluster.yml".format(cluster_dir)
            contents = {}
            contents['fsid'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, os.urandom(32)))
            contents['admin_method'] = "default"
            contents['configuration_method'] = "default"
            contents['mds_method'] = "default"
            contents['mon_method'] = "default"
            contents['osd_method'] = "default"
            contents['package_method'] = "default"
            contents['pool_method'] = "default"
            contents['repo_method'] = "default"
            contents['rgw_method'] = "default"
            contents['update_method'] = "default"

            contents['public_network'] = self.public_network
            contents['cluster_network'] = self.cluster_network
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

        interfaces = local.cmd('*' , 'network.interfaces')

        for minion in interfaces.keys():
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
                            networks[cidr] = [ (minion, nic, addr['address']) ]
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
        priorities = []
        for network in networks:
            quantity = len(networks[network])
            # Minimum number of nodes, ignore other networks 
            if quantity > 3:
                priorities.append( (len(networks[network]), network) )
                log.debug("Including network {}".format(network))
            else:
                log.warn("Ignoring network {}".format(network))

        if not priorities:
            raise ValueError("No network exists on at least 4 nodes")

        priorities = sorted(priorities, cmp=network_sort)
        if len(priorities) == 1:
            return str(priorities[0][1]), str(priorities[0][1])
        else:
            return str(priorities[0][1]), str(priorities[1][1])
        
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
            self.names = [ 'ceph' ]
        self.writer = writer

        local = salt.client.LocalClient()
        self.minions = local.cmd('*' , 'grains.get', [ 'id' ])

        # Should we add a master_minion lookup and have two calls instead?
        _rgws = local.cmd('*' , 'pillar.get', [ 'rgw_configurations' ])
        for node in _rgws.keys():
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
        for cluster in self.names + [ 'unassigned' ]:
            for minion in self.minions:
                cluster_dir = "{}/cluster-{}/cluster".format(self.root_dir, cluster)
                if not os.path.isdir(cluster_dir):
                     create_dirs(cluster_dir, self.root_dir)
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
             create_dirs(stack_dir, self.root_dir)
        filename = "{}/global.yml".format(stack_dir)
        contents = {}
        contents['time_server'] = '{{ pillar.get("master_minion") }}'
        contents['time_service'] = 'ntp'

        self.writer.write(filename, contents)

def create_dirs(path, root):
    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == errno.EACCES:
            print "ERROR: Cannot create dir {}".format(path)
            print "       Please make sure {} is owned by salt".format(root)
            raise err

def proposals(**kwargs):
    """
    Collect the hardware profiles, all possible role assignments and common
    configuration under /srv/pillar/ceph/proposals
    """
    settings = Settings()

    salt_writer = SaltWriter(**kwargs)

    ceph_cluster = CephCluster(settings, salt_writer, **kwargs)
    ceph_cluster.generate()

    # Allow overriding of hardware profile class
    hardwareprofile = HardwareProfile()

    for name in ceph_cluster.names:
        # Common cluster configuration
        ceph_storage = CephStorage(settings, name, salt_writer)

        ## Determine storage nodes and save proposals
        disk_configuration = DiskConfiguration(settings, ceph_cluster.minions)
        disk_configuration.generate(hardwareprofile)
        ceph_storage.save(hardwareprofile.servers, disk_configuration.proposals)

        # Determine roles and save proposals
        ceph_roles = CephRoles(settings, name, ceph_cluster.minions, salt_writer)
        ceph_roles.generate()
        ceph_roles.cluster_config()
        ceph_roles.monitor_members()
        ceph_roles.igw_members()
        
    return [ True ]

