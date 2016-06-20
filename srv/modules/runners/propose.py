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
import uuid

from layouts import *



class SaltOptions(object):
    """
    Assign salt __opts__ and stack configuration

    TBD: support multiple stack configurations
    """

    def __init__(self):
        __opts__ = salt.config.client_config('/etc/salt/master')
        self.__opts__ = __opts__

        for ext in __opts__['ext_pillar']:
            if 'stack' in ext:
                self.stack = ext['stack']

class CephStorage(object):
    """
    Default case is that all salt minions are for Ceph use
    """

    def __init__(self, options, dumper, servers):
        """
        Assign all minions to servers, track yaml dumper and ext_pillar stack
        """
        #key = salt.key.Key(options.__opts__)
        #keys = key.list_keys()
        #self.servers = keys['minions'] 
        self.servers = servers

        self.dumper = dumper
        self.stack = options.stack
        self.keyring = self._secret()


    def _secret(self):
        """
        """
        cmd = [ "ceph-authtool", "--gen-print-key", "/dev/null" ]
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        for line in proc.stdout:
            return line.rstrip()

    def save(self, servers, proposals):
        """
        Save each proposal for each server of each model
        """
        count = 0
        for model in servers.keys():
            for proposal in proposals[model]:
                count += 1
                for server in servers[model]:
                    self._save_proposal(model, count, server, proposal)
            count = 0


    def _save_proposal(self, model, count, server, storage):
        """
        Dump yaml contents to file
        """
        model_dir = dirname(self.stack) + "/storage/" + model + "/" + str(count)
        if not os.path.isdir(model_dir):
            os.makedirs(model_dir)
        filename = model_dir + "/" +  server + ".yml"
        contents = { 'storage': storage }
        contents['keyring'] =  [ { 'osd': self.keyring } ]
        contents['roles'] =  [ 'storage' ]
        with open(filename, "w") as yml:
            yml.write(yaml.dump(contents, Dumper=self.dumper))



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

    def add(self, hostname, drives):
        """
        Add a profile by label
        """
        self.model = {}
        for drive in drives:
            if 'Vendor' in drive:
                label = self._label(drive['Vendor'], drive['Capacity'])
            else:
                label = self._label(drive['Model'], drive['Capacity'])
            if not label in self.rotates:
                self.rotates[label] = drive['rotational']
            if label in self.model:
                self.model[label].append(drive['Device File'])            
            else:
                self.model[label] = [ drive['Device File'] ]            
        name = self._name()
        self._profiles(name, hostname)


    def _label(self, model, capacity):
        """
        Strip vowels from model and spaces from capacity for a shorter label
        """
        return re.sub(r'[AEIOUaeiou]', '', model) + re.sub(' ', '', capacity)

    def _profiles(self, name, hostname):
        """
        Create a profile and track all storage servers that match that profile.
        if the name already exists, verify that the order matches.  If so, add
        to list.  If not, create a new name and try again.

        Hardware profiles with a single server will alert the sysadmin to 
        missing/failed drives or servers with disks out of order.
        """
        if name in self.profiles:
            # ensure the device list is the same
            for model in self.profiles[name]:
                devices = self.profiles[name][model]
                if self.model[model] != devices:
                    parts = name.split('#')
                    if len(parts) == 1:
                        number = int(parts[1])
                        new_name = name + "#" + str(number + 1)
                    else:
                        new_name = name + "#2"
                    self._profiles(new_name, hostname)
                    return

            self.servers[name].append(hostname)
        else:
            self.servers[name] = [ hostname ]
            self.profiles[name] = {}
            for label in self.model.keys():
                self.profiles[name][label] = self.model[label]
        
        
    def _name(self):
        """
        Create a consistent name by sorting the drive types
        """
        quantities = {}
        for label in self.model.keys():
            quantities[str(len(self.model[label])) + label] = ""
        return "-".join(sorted(quantities.keys()))


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
                ret = salt.utils.minions.mine_get(server, 'freedisks.list', 'glob', options.__opts__)
                self.storage_nodes.update(ret)
        else:
            # salt-call mine.get '*' freedisks.list
            self.storage_nodes = salt.utils.minions.mine_get('*', 'freedisks.list', 'glob', options.__opts__)

#        self.storage_nodes = { 'data5.ceph' : [
#{'Attached to': '#14 (SATA controller)',
#  'Device': 'SSD 850',
#  'Device File': '/dev/sda',
#  'Model': 'Samsung SSD 850',
#  'Vendor': 'Samsung',
#  'device': 'sda',
#  'Capacity': '465 GB',
#  'Bytes': '500107862016 bytes',
#  'rotational': '0'},
#{'Attached to': '#14 (SATA controller)',
#  'Device': 'SSD 850',
#  'Device File': '/dev/sdy',
#  'Model': 'Samsung SSD 850',
#  'Vendor': 'Samsung',
#  'device': 'sdy',
#  'Capacity': '465 GB',
#  'Bytes': '500107862016 bytes',
#  'rotational': '0'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sdb',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sdb',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sdc',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sdc',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sdd',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sdd',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sde',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sde',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sdf',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sdf',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sdg',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sdg',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sdh',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sdh',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sdi',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sdi',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sdj',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sdj',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'},
# {'Attached to': '#14 (SATA controller)',
#  'Device': 'HTS721010A9',
#  'Device File': '/dev/sdk',
#  'Model': 'HGST HTS721010A9',
#  'Vendor': 'HGST',
#  'device': 'sdk',
#  'Capacity': '931 GB',
#  'Bytes': '1000204886016 bytes',
#  'rotational': '1'}
#] 
#}

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

        for configuration in self.hardware.profiles:
            if not configuration in self.proposals:
                self.proposals[configuration] = []
            drives = self.hardware.profiles[configuration]
            self.proposals[configuration].append(self._assignments(drives))
            for drive_model in drives.keys():
                # How many types of drives are SSDs
                if self.hardware.rotates[drive_model] == '0':
                    proposal = self._assignments(drives, drive_model)
                    if proposal:
                        self.proposals[configuration].append(proposal)
        
        
    def _assignments(self, drives, journal=None):
        """
        For a set of drives and designated journals (including none), assign
        the devices to the various drive types.  The types are

            osds = data + journal on same device
            data+journals = data + journal on separate devices
            small = under 11G
        """
        assignments = { 'osds': [], 'data+journals': [], 'small': [] }
        data = []
        journals = []
        for drive_model in drives.keys():
            # check capacity
            if drive_model == journal:
                journals.extend(drives[drive_model])
            else:
                if self.hardware.rotates[drive_model]:
                    if journal:
                        data.extend(drives[drive_model])
                    else:
                        assignments['osds'].extend(drives[drive_model])
                else:
                    # SSD for caching
                    assignments['osds'].extend(drives[drive_model])

        # check that data drives can be evenly divided by 6-3
        if journal:
            for partitions in range(6, 2, -1):
                if (len(data) % partitions == 0):
                    if (len(journals) >= len(data)/partitions):
                        print "partitions: ", partitions
                        print "journals: ", journals
                        index = 0
                        count = 1
                        for device in data:
                            print "device: ", device
                            assignments['data+journals'].extend([ { "{}1".format(device):  "{}{}".format(journals[index], count) } ]) 
                            count += 1
                            if (count - 1) % partitions == 0:
                                print "resetting"
                                count = 1
                                index += 1
                        # Add unused journal drives as OSDs
                        assignments['osds'].extend(journals[index:])
                        return assignments
            # No suggestion
            return {}
        else:
            return assignments
            


class CephRoles(object):
    """
    Create reasonable proposals from the existing hardware
    """

    def __init__(self, options, cluster, servers, storage, dumper):
        """
        Track storage and free servers.  Free servers are what remains
        after removing storage and admin nodes.  Set yaml dumper and
        ext_pillar stack.
        """
        #master = re.sub('_master', '', options.__opts__['id'])
        self.cluster = cluster
        self.storage = storage
        free = sorted(list(set(servers) - set(storage)))
        self.free = free

        self.dumper = dumper
        self.stack = options.stack
        self.keyring_roles = { 'admin': self._secret(), 
                               'mon': self._secret(), 
                               'mds': self._secret(),
                               'rgw': self._secret() }

    def _secret(self):
        """
        """
        cmd = [ "ceph-authtool", "--gen-print-key", "/dev/null" ]
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        for line in proc.stdout:
            return line.rstrip()


    def propose(self, layout):
        """
        Use the selected layout strategy to get a list of proposals
        """
        layouts = layout(self.storage, self.free)
        switch = {
            0: layouts.zero_free,
            1: layouts.one_free,
            2: layouts.two_free,
            3: layouts.three_free,
            4: layouts.four_free,
            5: layouts.five_free,
            6: layouts.six_free,
            7: layouts.seven_free
        }
        func = switch.get(len(self.free), None)
        if func:
            self.proposals = func()
        else:
            # should call default instead
            raise RuntimeError("Hardware configuration not supported")


    def save(self):
        """
        Save each proposal in a stack.py friendly manner.  One role per
        file under its respective named proposal.  Rely on stack.py to 
        merge contents for pillar data.
        """
        for proposal in self.proposals:
            for role in proposal.keys():
                if role == 'name':
                    continue
                # Skip misconfigurations
                if not self.cluster:
                    continue
                role_dir = "{}/layouts/{}/{}".format(dirname(self.stack), self.cluster, role)
                if not os.path.isdir(role_dir):
                    os.makedirs(role_dir)
                config_dir = role_dir + "/" + proposal['name']
                if not os.path.isdir(config_dir):
                    os.makedirs(config_dir)
                for server in proposal[role]:
                    filename = config_dir + "/" +  server + ".yml"
                    contents = {}
                    contents['roles'] = [ role ]
                    if role in self.keyring_roles:
                        contents['keyring'] = [ { role: self.keyring_roles[role] } ]
                    with open(filename, "w") as yml:
                        yml.write(yaml.dump(contents, Dumper=self.dumper, 
                                            default_flow_style=False))
                
    def save_admin(self):
        """
        Save the admin keyring globally for the cluster.  This is bad in
        the general sense, but not quick to resolve without reworking the 
        current process for adding osds.
        """
        if self.cluster:
            filename = "{}/cluster/{}.yml".format(dirname(self.stack), self.cluster)
            contents = {}
            contents['keyring'] = [ { 'admin': self.keyring_roles['admin'] } ]
            contents['fsid'] = str(uuid.uuid3(uuid.NAMESPACE_DNS, self.keyring_roles['admin']))
            with open(filename, "w") as yml:
                yml.write(yaml.dump(contents, Dumper=self.dumper, 
                                    default_flow_style=False))


class Keyrings(object):
    """
    Unused class... might go this way
    """
    def __init__(self, options, cluster):
        self.stack = options.stack
        self.cluster = cluster
            


    def save(self):
        """
        Save each keyring in a stack.py friendly manner.  One role per
        file under its respective role.  Rely on stack.py to 
        merge contents for pillar data.
        """
        for role in self.roles:
            role_dir = "{}/keyrings/{}/{}".format(dirname(self.stack), self.cluster, role)
            if not os.path.isdir(role_dir):
                if not os.path.isdir(role_dir):
                    os.makedirs(role_dir)
            config_dir = role_dir 
            if not os.path.isdir(config_dir):
                os.makedirs(config_dir)
            for server in proposal[role]:
                filename = config_dir + "/" +  server + ".yml"
                contents = {}
                contents['keyring'] = [ { role: self._secret } ]
                with open(filename, "w") as yml:
                    yml.write(yaml.dump(contents, Dumper=self.dumper, 
                                        default_flow_style=False))

def layouts():
    """
    Free servers are identical.  Think cattle.
    """
    _common(DefaultLayouts)
    return True

def byhostname():
    """
    Free servers have role based hostnames.
    """
    _common(LayoutsByHostname)
    return True

def custom():
    """
    Unsatisfied with role based hostnames or missing proposals, create your own.
    """
    from custom import custom_layout
    _common(custom_layout())
    return True

def _common(layouts):
    """
    Steps for all layout generation
    """
    salt_options = SaltOptions()

    # Keep yaml human readable/editable
    friendly_dumper = yaml.SafeDumper
    friendly_dumper.ignore_aliases = lambda self, data: True

    local = salt.client.LocalClient()
    minions = local.cmd('*' , 'pillar.get', [ 'cluster' ])
    
    clusters = {}
    for minion in minions.keys():
        cluster = minions[minion]
        if not cluster in clusters:
            clusters[cluster] = []
        clusters[cluster].extend([ minion ])

    pprint.pprint(clusters)

    # Allow overriding of hardware profile class
    hardwareprofile = HardwareProfile()

    for name in clusters.keys():
        if name == "unassigned":
            continue
        servers = clusters[name]
        # Common cluster configuration
        ceph_storage = CephStorage(salt_options, friendly_dumper, servers)

        # Determine storage nodes and save proposals
        disk_configuration = DiskConfiguration(salt_options, servers)
        disk_configuration.generate(hardwareprofile)
        ceph_storage.save(hardwareprofile.servers, disk_configuration.proposals)

        # Determine roles and save proposals
        ceph_roles = CephRoles(salt_options, name, servers, 
                               disk_configuration.servers, friendly_dumper)
        ceph_roles.propose(layouts)
        ceph_roles.save()
        ceph_roles.save_admin()
        
    return [ True ]

