#!/usr/bin/python

import salt.client
import salt.config
import salt.loader

import select
import logging
import socket

log = logging.getLogger(__name__)

def ping():
    """
    Return True if any node is not being connected. 
    """
    local = salt.client.LocalClient()
    return local.cmd(socket.gethostname(), 'nettest.ping_all_minions', ['filter_type=fail'])

