#!/usr/bin/python

import salt.config as salt_config
import salt.key as salt_key
import salt.runner as salt_runner
import salt.utils as salt_utils

import copy
import logging
import os
import re
import socket
import time

log = logging.getLogger(__name__)


def _get_all_minions():
    '''
    *Master* internal function to get all accepted minions 
    '''
    pki_dir = __salt__['config.get']('pki_dir', '')
    pki_dir = pki_dir.replace('minion', 'master')
    minion_path = os.path.join(pki_dir, salt_key.Key.ACC)
    minion_list = []
    #minion_list[os.path.basename(minion_path)] = []
    try:
        for keys in salt_utils.isorted(os.listdir(minion_path)):
            if not keys.startswith('.'):
                if os.path.isfile(os.path.join(minion_path, keys)):
                    minion_list.append(keys)
    except (OSError, IOError):
    # if key dir is not created skip
        minion_list = "No Minions"
    return minion_list

def _get_master():
    master_host = __salt__['pillar.get']('master_minion')
    if not master_host:
        master_host = 'Not master config!'
    return master_host

def ping( node ):
    '''
    Ping a client node 4 times and return result

    CLI Example:
    .. code-block:: bash
    salt 'node' nettest.ping <hostname>|<ip>
    '''
    if not node:
        node = socket.gethostname()
    ping_out = __salt__['cmd.run']('/usr/bin/ping -c 4 ' + node , output_loglevel='debug')
    return ping_out

def multi_ping( ping_from, *nodes ):
    '''
    *This function mean for master only. *
    Ping a list of client nodes with nettest.ping async and return result

    CLI Example:
    .. code-block:: bash
    salt 'salt-master' nettest.multi_ping <ping_from_hostname>|<ip> <ping_to_hostname>|<ip>...
    '''
    master_host = _get_master()
    local_host = socket.gethostname()
    if local_host != master_host:
        return "Master is :" + master_host + "\nThis function need to run in the salt master!\n"
    if len(nodes) < 1:
        return "\n Multi_ping need a client nodes list\n"
    ping_jid = []
    ping_log = []
    for i, node in enumerate( nodes ):
        ping_jid.append( __salt__['cmd.run']('/usr/bin/salt --async ' + ping_from + ' nettest.ping ' + node, output_loglevel='debug'))
    time.sleep(2)
    for log in ping_jid:
        m = re.match(r'Executed command with job ID: (\d+)', log,  re.DOTALL)
        if m :
            ping_log.append( __salt__['cmd.run']('/usr/bin/salt-run jobs.lookup_jid ' + m.group(1), output_loglevel='debug') )
        else:
            ping_log.append( 'Fail to ping ' + node) 
    return ping_log

def ping_all_minions():
    '''
    Ping all minions except itself 4 times and return result

    CLI Example:
    .. code-block:: bash
    salt 'node' nettest.ping_all_minions
    '''
    master_host = _get_master()
    minion_list = _get_all_minions()
    ping_jid = []
    ping_log = []
    for minion in minion_list:
        #call_list = dict((k, v) for k, v in minion_list.iteritems() if v !=minion)
        call_list = copy.deepcopy(minion_list)
        call_list.remove(minion)
        #ping_log.append('/usr/bin/salt --async ' + master_host + '  nettest.multi_ping ' + minion + ' ' + ' '.join(call_list))
        ping_jid.append(__salt__['cmd.run']('/usr/bin/salt --async ' + master_host + '  nettest.multi_ping ' + minion + ' ' + ' '.join(call_list)))
    time.sleep(len(minion_list) + 4)
    for log in ping_jid:
        m = re.match(r'Executed command with job ID: (\d+)', log,  re.DOTALL)
        if m :
            ping_log.append( __salt__['cmd.run']('/usr/bin/salt-run jobs.lookup_jid ' + m.group(1), output_loglevel='debug') )
        #ping_log.append(call_list)
	
    return ping_log

