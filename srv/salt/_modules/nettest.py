#!/usr/bin/python

import time
import logging

log = logging.getLogger(__name__)

def ping( node ):
    '''
    Ping a client node 4 times and return result

    CLI Example:
    .. code-block:: bash
    salt 'node' check.ping
    '''
    ping_out = __salt__['cmd.run']('/usr/bin/ping -c 4 ' + node , output_loglevel='debug')


    return ping_out
