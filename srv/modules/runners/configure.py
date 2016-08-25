#!/usr/bin/python

import salt.client
import ipaddress
import pprint
import yaml
import os
from os.path import dirname


"""
For Ceph, the generation of ceph.conf requires additional information.
Although this information can be determined from Salt itself, the 
prerequisite is monitor assignment. This step is more of a post configuration
before deployment.

Eventually, root assignment within the crushmap may live here.  The similar
prerequisite is that osd assignment must be decided before segregating types
of hardware.
"""

# Until I figure out the "right way" for managing common routines between
# Salt runners, SaltWriter is a duplicate from populate.pillars.  (And yes, I 
# know I can make a library, but what do you expect as the user?)
class SaltWriter(object):
    """
    All salt files are essentially yaml files in the pillar by default.  The 
    pillar uses sls extensions and stack.py uses yml.
    """

    def __init__(self):
        """
        Keep yaml human readable/editable.  Disable yaml references.
        """
        self.dumper = yaml.SafeDumper
        self.dumper.ignore_aliases = lambda self, data: True


    def write(self, filename, contents):
        """
        Write a yaml file in the conventional way
        """
        with open(filename, "w") as yml:
            yml.write(yaml.dump(contents, Dumper=self.dumper,
                                          default_flow_style=False))

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
    
def cluster(**kwargs):
    """
    Generate the ceph.conf data and populate the pillar.  Use the filename
    ceph_conf.yml to convey the contents.
    """

    salt_writer = SaltWriter()

    options = SaltOptions()
    local = salt.client.LocalClient()

    cluster = ClusterAssignment(local)

    for name in cluster.names:
        # Restrict search to monitors for this cluster
        search = "I@cluster:{} and I@roles:mon".format(name)

        # mon create fails on FQDN at the moment
        #mon_host = local.cmd(search , 'pillar.get', [ 'mon_host' ], expr_form="compound")
        mon_host = local.cmd(search , 'pillar.get', [ 'public_address' ], expr_form="compound")
        mon_initial_members = local.cmd(search , 'grains.get', [ 'host' ], expr_form="compound")
        
        contents = {}
        contents['mon_host'] = mon_host.values()
        contents['mon_initial_members'] = mon_initial_members.values()

        if not contents['mon_host']:
            raise RuntimeError("public_address missing from mon_host")
        if not contents['mon_initial_members']:
            raise RuntimeError("No results for {}".format(search))
        #pprint.pprint(contents)

        #contents = _contents(local, minions)

        cluster_dir = "{}/default/{}".format(options.stack_dir, name)
        if not os.path.isdir(cluster_dir):
             os.makedirs(cluster_dir)
        filename = "{}/ceph_conf.yml".format(cluster_dir, name)

        salt_writer.write(filename, contents)



    return True

#def _contents(local, minions):
#    """
#    This strategy relies on retrieving a network interface for public and
#    cluster networks.  This can be problematic in some sites.
#
#    Another strategy is to take a best guess as to the public and cluster
#    network based on a combination of private networks and physical connections.
#    This has not been implemented.
#    """
#
#    contents = {}
#    contents['mon_initial_members'] = minions.values()
#
#    contents['mon_host'] = []
#    for minion in minions.keys():
#        # Find interface names for each minion
#        public_interface_name = local.cmd(minion , 'pillar.get', [ 'public_interface' ])[minion]
#        cluster_interface_name = local.cmd(minion , 'pillar.get', [ 'cluster_interface' ])[minion]
#
#        # Find the address for that interface
#        public_address = local.cmd(minion , 'network.interface', [ public_interface_name ])[minion][0]
#        cluster_address = local.cmd(minion , 'network.interface', [ cluster_interface_name ])[minion][0]
#
#        # Build list of public addresses
#        contents['mon_host'].append(public_address['address'])
#
#        # Generate the corresponding networks
#        public = ipaddress.ip_interface(u'{}/{}'.format(public_address['address'], public_address['netmask']))
#        contents['public_network'] = str(public.network)
#        cluster = ipaddress.ip_interface(u'{}/{}'.format(cluster_address['address'], cluster_address['netmask']))
#        contents['cluster_network'] = str(cluster.network)
#
#    return contents

