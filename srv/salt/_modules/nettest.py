#!/usr/bin/python

import salt.config as salt_config
import salt.key as salt_key
import salt.runner as salt_runner
import salt.utils as salt_utils

import copy
import logging
import netifaces
import os
import re
import socket
import time

log = logging.getLogger(__name__)

'''
   nettest is the module to test network configuration before state 0 
   to understand what node may be not connecting to the other correctly
   
   Ping is a simple test to check if point to point nodes are connected
   All ping function reply with a default filter type 'full' which is 
   the default log reply from ping command itself. 
   
   filter_type:
    'full' - default ping log 
    'success' - if 4 ping all successfully reply
    'fail' - if 4 ping has any fail to reply
    'avg' - average reply time 
   
   CLI Example:
   .. code-block:: bash
   sudo salt 'node' nettest.ping <hostname>|<ip> <filter_type=[full,success,fail,avg]>
   sudo salt 'salt-master' nettest.multi_ping <ping_from_hostname>|<ip> 
       <ping_to_hostname>|<ip>... <filter_type=[full,success,fail,avg]>
   sudo salt 'salt-master' nettest.ping_all_minions <filter_type=[full,success,fail,avg]>

'''

def _get_all_minions():
    '''
    *Master* internal function to get all accepted minions 
    '''
    pki_dir = __salt__['config.get']('pki_dir', '')
    pki_dir = pki_dir.replace('minion', 'master')
    minion_path = os.path.join(pki_dir, salt_key.Key.ACC)
    minion_list = []
    log.debug('internal function _get_all_minion: check path {}'.format(minion_path))
    try:
        for keys in salt_utils.isorted(os.listdir(minion_path)):
            if not keys.startswith('.'):
                if os.path.isfile(os.path.join(minion_path, keys)):
                    minion_list.append(keys)
    except (OSError, IOError):
    # if key dir is not created skip
        log.debug('key dir is not create')
    return minion_list

def _get_master():
    '''
    internal function to get salt master 
    '''
    master_host = __salt__['pillar.get']('master_minion')
    log.debug('internal function _get_master: {}'.format(master_host))
    if not master_host or master_host == '_REPLACE_ME_':
        master_host = False
    return master_host

def _is_master():
    '''
    internal function to make sure called node is salt-master 
    '''
    master_host = _get_master()
    localhost = socket.gethostname()
    log.debug('internal function _is_master: localhost {}'.format(localhost))
    if not master_host:
        return False
    else:
        try:
            master_ip = socket.gethostbyname(master_host)
            local_ip = socket.gethostbyname(localhost)
        except socket.gaierror:
            log.exception('Error hostname not find: master/{}, localhost hostname/{}'.format(master_host,localhost))
            print('Error hostname not find: master/{}, localhost hostname/{}'.format(master_host,localhost))
            print(socket.gaierror)
            return False
    if local_ip != master_ip:
        return False
    else:
        return True

def _ping_log_avg( ping_log ):
    '''
    internal filter function to grab the average reply speed
    '''
    if _ping_log_success(ping_log):
        m = re.match(r'.*rtt min/avg/max/mdev = \d+\.?\d+/(\d+\.?\d+)/', ping_log, re.DOTALL)
        if m:
            return m.group(1) +' ms'
        else:
            return False
    else:
        return False

def _ping_log_fail( ping_log ):
    '''
    internal filter function to if there is any package lost 
    '''
    m = re.match(r'.*4 received, 0% packet loss', ping_log, re.DOTALL)
    if m:
        return False
    else:
        return True

def _ping_log_filter(ping_log, filter_type='full'): 
    '''
    internal function to filter log result base on filter type
    'full' - default ping log 
    'success' - if 4 ping all successfully reply
    'fail' - if 4 ping has any fail to reply
    'avg' - average reply time 
    '''
    filtering = {
        'success': lambda: _ping_log_success(ping_log),
        'fail': lambda: _ping_log_fail(ping_log),
        'avg': lambda: _ping_log_avg(ping_log), 
    } 
    func = filtering.get(filter_type, lambda: ping_log)
    return func()

def _ping_log_success( ping_log ):
    '''
    internal filter function to if all package get received 
    '''
    m = re.match(r'.*4 received, 0% packet loss', ping_log, re.DOTALL)
    if m:
        return True
    else:
        return False

def get_all_ipv4():
    '''
    Return all available ipv4 address with local interface. 
    '''
    ip_list = []
    for interface in netifaces.interfaces():
        log.debug('get_all_ipv4: interface {}'.format(interface))
        if interface != 'lo':
            try:
                for link in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                    ip_list.append(link['addr'])
            except KeyError:
                log.debug( 'interface {} has no link'.format(interface))
    return ip_list

def iperf_client( server, run_time=100, cpu_num=1, port_num=5201 ):
    '''
    Use iperf to test minion to server
        
    CLI Example:
    .. code-block:: bash
    salt 'node' ceph_sles.iperf cpu_number port_number server
    '''
    if not server:
        return False
    iperf_cmd = '/usr/bin/iperf3 -f M -t {} -A {} -c {} -p {}'.format(run_time, cpu_num, server, port_num)
    log.debug('iperf: cmd {}'.format(iperf_cmd))
    iperf_log = __salt__['cmd.run'](iperf_cmd, output_loglevel='debug')
    return iperf_log

def multi_ping( ping_from, *nodes, **kwargs):
    '''
    *This function mean for master only. *
    Ping a list of client nodes with nettest.ping async and return result

    CLI Example:
    .. code-block:: bash
    salt 'salt-master' nettest.multi_ping <ping_from_hostname>|<ip> <ping_to_hostname>|<ip>...
    '''
    filter_type = kwargs.get('filter_type', 'full')
    if not _is_master():
        return "This function need to run in the salt master!\n"

    localhost = socket.gethostname()
    master_host = _get_master()

    log.debug('multi_ping: ping_from {}'.format(ping_from))
    log.debug('node_list {}'.format(nodes))
    log.debug('filter_type {}'.format(filter_type))
    if len(nodes) < 1:
        return "\n Multi_ping need a client nodes list\n"
    ping_jid = []
    temp_log = []
    ping_log = []
    for i, node in enumerate( nodes ):
        ping_jid.append( __salt__['cmd.run']('/usr/bin/salt --async ' + ping_from + ' nettest.ping ' + node + ' filter_type=' + filter_type, output_loglevel='debug'))
    #time.sleep(3)
    for jid_log in ping_jid:
        log.debug('jid_log {}'.format(jid_log))
        m = re.match(r'Executed command with job ID: (\d+)', jid_log,  re.DOTALL)
        if m :
            m_log = {}
            while not m_log:
                time.sleep(1) 
                m_log = __salt__['cmd.run']('/usr/bin/salt-run jobs.lookup_jid ' + m.group(1), output_loglevel='debug')
            not_fail = re.match(r'.*False', m_log, re.DOTALL)
            if not not_fail: 
                temp_log.append( m_log )
    if len(temp_log) == 0:
        return False
    for line in temp_log:
        ping_log.append(re.sub(r'(' + ping_from + ':\n\s)' , '', line))
    return ping_log

def ping( node, filter_type='full'):
    '''
    Ping a client node 4 times and return result

    CLI Example:
    .. code-block:: bash
    salt 'node' nettest.ping <hostname>|<ip>
    '''
    if not node:
        return "\n ping need a client node\n"
    log.debug('ping: to {}'.format(node))
    log.debug('filter_type {}'.format(filter_type))

    ping_out = __salt__['cmd.run']('/usr/bin/ping -c 4 ' + node , output_loglevel='debug')
    if( _ping_log_filter(ping_out, filter_type) ):
        return node + ': ' + str(_ping_log_filter(ping_out, filter_type))
    else:
        return False

def ping_all_minions(filter_type='full'):
    '''
    *This function mean for master only. *
    Ping all minions except itself 4 times and return result

    CLI Example:
    .. code-block:: bash
    salt 'node' nettest.ping_all_minions
    '''
    if not _is_master():
        return "This function need to run in the salt master!\n"
    master_host = _get_master()
    minion_list = _get_all_minions()
    log.debug('ping_all_minions: master {}'.format(master_host))
    log.debug('minion_list {}'.format(minion_list))
    log.debug('filter_type {}'.format(filter_type))
    ping_jid = []
    temp_log = []
    ping_log = []
    for minion in minion_list:
        call_list = copy.deepcopy(minion_list)
        call_list.remove(minion)
        mp_jid = __salt__['cmd.run']('/usr/bin/salt --async ' + master_host + '  nettest.multi_ping ' + minion + ' ' + ' '.join(call_list) + ' filter_type=' + filter_type, output_loglevel='debug')
        ping_jid.append({'jid':mp_jid, 'ping_from':minion})
    #time.sleep(len(minion_list) + 4)
    for jid_log in ping_jid:
        log.debug('jid_log {}'.format(jid_log['jid']))
        m = re.match(r'Executed command with job ID: (\d+)', jid_log['jid'],  re.DOTALL)
        if m:
            m_log = {}
            while not m_log:
                time.sleep(1) 
                m_log = __salt__['cmd.run']('/usr/bin/salt-run jobs.lookup_jid ' + m.group(1), output_loglevel='debug')
            not_fail = re.match(r'.*False', m_log, re.DOTALL)
            if not not_fail:
                temp_log.append(m_log)
    if len(temp_log) == 0 and filter_type == 'fail':
        return 'Nothing fail!\n'
    for i, t_log in enumerate(temp_log):
        ping_log.append(re.sub(r'(' + master_host + ':\n)' , ping_jid[i]['ping_from'] + ':\n' , t_log))
    return ping_log

