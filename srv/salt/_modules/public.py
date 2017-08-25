# -*- coding: utf-8 -*-

import ipaddress
import time
import logging
import pprint

log = logging.getLogger(__name__)

"""
"""

def address():
    """
    Find the public address for a minion
    """

    if 'public_network' not in __pillar__:
        return ""

    log.debug("pillar: {}".format(type(__pillar__['public_network'])))
    if type(__pillar__['public_network']) is str:
        networks = [ __pillar__['public_network'] ]
    else:
        networks = __pillar__['public_network']

    log.debug("networks: {}".format(pprint.pformat(networks)))
    for public_network in networks:
        log.info('public_network: {}'.format(public_network))
        interfaces = __salt__['network.interfaces']()

        log.debug("interfaces: {}".format(pprint.pformat(interfaces)))
        for interface in interfaces:
            log.info("interface: {}".format(pprint.pformat(interface)))
            if 'inet' in interfaces[interface]:
                for entry in interfaces[interface]['inet']:
                    address = entry['address']
                    log.info("Checking address {}".format(address))
                    if (ipaddress.ip_address(u'{}'.format(address)) in
                        ipaddress.ip_network(u'{}'.format(public_network))):
                        return address
    return ""
