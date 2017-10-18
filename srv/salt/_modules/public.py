# -*- coding: utf-8 -*-
# pylint: disable=visually-indented-line-with-same-indent-as-next-logical-line
"""
Functions related to the public network
"""

from __future__ import absolute_import
import ipaddress
import logging
import pprint
import re

log = logging.getLogger(__name__)


def address():
    """
    Find the public address for a minion
    """

    if 'public_network' not in __pillar__:
        return ""

    log.debug("pillar: {}".format(type(__pillar__['public_network'])))
    if isinstance(__pillar__['public_network'], str):
        networks = re.split(', *', __pillar__['public_network'])
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
                    _address = entry['address']
                    log.info("Checking address {}".format(_address))
                    if (ipaddress.ip_address(u'{}'.format(_address)) in
                        ipaddress.ip_network(u'{}'.format(public_network))):
                        return _address
    return ""
