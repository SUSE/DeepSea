#!/usr/bin/python

import salt.client
import ipaddress
import pprint
import yaml
import os
from os.path import dirname

def cluster(**kwargs):
    """
    Generate the ceph.conf data and populate the pillar
    """
    local = salt.client.LocalClient()
    minions = local.cmd('*' , 'pillar.get', [ 'cluster' ])

    __opts__ = salt.config.client_config('/etc/salt/master')
    for ext in __opts__['ext_pillar']:
        if 'stack' in ext:
            stack_dir = dirname(ext['stack'])


    # Keep yaml human readable/editable
    friendly_dumper = yaml.SafeDumper
    friendly_dumper.ignore_aliases = lambda self, data: True

    clusters = {}
    for minion in minions.keys():
        cluster = minions[minion]
        if not cluster in clusters:
            clusters[cluster] = []
        clusters[cluster].extend([ minion ])


    for name in clusters.keys():
        if name == "unassigned":
            continue
        #print "cluster: ", name
        search = "I@cluster:{} and I@roles:mon".format(name)

        # mon create fails on FQDN at the moment
        #minions = local.cmd(search , 'pillar.get', [ 'id' ], expr_form="compound")
        minions = local.cmd(search , 'grains.get', [ 'host' ], expr_form="compound")
        contents = {}
        contents['mon_initial_members'] = minions.values()

        contents['mon_host'] = []
        for minion in minions.keys():
            public_interface_name = local.cmd(minion , 'pillar.get', [ 'public_interface' ])[minion]
            cluster_interface_name = local.cmd(minion , 'pillar.get', [ 'cluster_interface' ])[minion]

            public_address = local.cmd(minion , 'network.interface', [ public_interface_name ])[minion][0]
            cluster_address = local.cmd(minion , 'network.interface', [ cluster_interface_name ])[minion][0]

            contents['mon_host'].append(public_address['address'])

            public = ipaddress.ip_interface(u'{}/{}'.format(public_address['address'], public_address['netmask']))
            #print public.network
            contents['public_network'] = str(public.network)
            cluster = ipaddress.ip_interface(u'{}/{}'.format(cluster_address['address'], cluster_address['netmask']))
            #print cluster.network
            contents['cluster_network'] = str(cluster.network)

        pprint.pprint(contents)
        cluster_dir = "{}/cluster".format(stack_dir)
        if not os.path.isdir(cluster_dir):
             os.makedirs(cluster_dir)
        filename = "{}/{}.conf.yml".format(cluster_dir, name)
        with open(filename, "w") as yml:
            yml.write(yaml.dump(contents, Dumper=friendly_dumper, default_flow_style=False))



    return True

