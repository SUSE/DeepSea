# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4
'''
Library for Salt runner to scan minions for mgmt, public and cluster networks.
'''
from __future__ import absolute_import
import logging
import ipaddress
import pprint
import operator
from functools import reduce, cmp_to_key
import yaml
import salt.client

log = logging.getLogger(__name__)

DEEPSEA_MINIONS = "/srv/pillar/ceph/deepsea_minions.sls"


class DeepSeaNetwork(object):
    """
    Discover networks
    """

    def __init__(self):
        """
        Initialize role secrets, track parameters
        """
        self.target = ""
        self.error = ""
        self.networks = None
        self.public_networks = []
        self.cluster_networks = []
        self.minions = []

    def scan(self):
        ''' Guess likely IPv4 public and cluster networks '''
        self.deepsea_minions()
        if self.error:
            return False

        if self.target:
            self.networks = self._find_networks()
            self.public_networks, self.cluster_networks = self.public_cluster(self.networks.copy())
            log.info(f"public: {self.public_networks}")
            log.info(f"cluster: {self.cluster_networks}")
            return True
        return False

    def deepsea_minions(self, filename=DEEPSEA_MINIONS):
        ''' Reads target for deepsea minions'''
        with open(filename, 'r') as sls:
            content = yaml.load(sls)
        if 'deepsea_minions' in content:
            log.info(f"content: {content}")
            self.target = content['deepsea_minions']
        else:
            self.error = f"deepsea_minions missing from {DEEPSEA_MINIONS}"

    def minions(self):
        ''' Expands target to minions '''
        local = salt.client.LocalClient()
        try:
            data = local.cmd(self.target, 'test.true', [], tgt_type="compound")
        except SaltClientError as error:
            log.error(f"salt '{self.target}' test.true failed... {error}")
        self.minions = list(data.keys())

    def mgmt(self):
        ''' Default to public network '''
        return ", ".join([str(n) for n in self.public_networks])

    def public(self):
        ''' Return a comma separated string of CIDR networks '''
        return ", ".join([str(n) for n in self.public_networks])

    def cluster(self):
        ''' Return a comma separated string of CIDR networks '''
        return ", ".join([str(n) for n in self.cluster_networks])

    def publicnetwork_is_ipv6(self):
        '''
        Check if public_network is an IPv6. Accept the cluster network as is
        or default it to the same value as the public_network.

        Validation of all networks occurs in validate.py
        '''
        local = salt.client.LocalClient()
        data = local.cmd(self.target, 'pillar.items', [], tgt_type="compound")
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

    def _find_networks(self):
        '''
        Create a dictionary of networks with tuples of minion name, network
        interface and current address.  (The network interface is not
        currently used.)
        '''
        networks = {}
        local = salt.client.LocalClient()

        interfaces = local.cmd(self.target, 'network.interfaces', [], tgt_type="compound")

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
        ''' Return CIDR network '''
        return ipaddress.ip_interface(u'{}/{}'.format(address, netmask)).network

    def public_cluster(self, networks):
        '''
        Guess which network is public and which network is cluster. The
        public network should have the greatest quantity since the cluster
        network is not required for some roles.  If those are equal, pick
        the lowest numeric address.

        Other strategies could include prioritising private addresses or
        interface speeds.  However, this will be wrong for somebody.
        '''
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
        cmd_result = local.cmd(self.target, 'cmd.run', ['hostname -i'], tgt_type="compound")
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
        for _, (quantity, network) in enumerate(priorities):
            if cluster_networks or quantity == 1:
                public_networks.append(network)
            else:
                if not public_networks:
                    public_networks.append(network)
                else:
                    cluster_networks.append(network)

        # fourth step, remove redudant public networks
        filtered_list = []
        cmd_result = local.cmd(self.target, 'grains.get', ['ipv4'], tgt_type="compound")
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


# pylint: disable=invalid-name,no-else-return
def network_sort(a, b):
    ''' Sort quantity descending and network ascending. '''
    if a[0] < b[0]:
        return 1
    elif a[0] > b[0]:
        return -1
    else:
        return _cmp(a[1], b[1])


# pylint: disable=invalid-name
def _cmp(x, y):
    '''
    Replacement for built-in function cmp that was removed in Python 3

    Compare the two objects x and y and return an integer according to
    the outcome. The return value is negative if x < y, zero if x == y
    and strictly positive if x > y.
    '''
    return (x > y) - (x < y)
