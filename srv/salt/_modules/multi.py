# -*- coding: utf-8 -*-
"""
Collection of running multiple processes from a minion in parallel, typically
for network related tasks such as ping and iperf.
"""

from __future__ import absolute_import
import logging
import multiprocessing.dummy
import multiprocessing
import re
import socket
from subprocess import Popen, PIPE
# pylint: disable=incompatible-py3-code
log = logging.getLogger(__name__)

try:
    from salt.utils import which
# pylint: disable=bare-except
except:
    from distutils.spawn import which

IPERF_PATH = which('iperf3')

LOCALHOST_NAME = socket.gethostname()

'''
multi is the module to call subprocess in minion host

Ping is a simple test to check if point to point nodes are connected

CLI Example:
.. code-block:: bash
    sudo salt 'node' multi.ping_cmd <hostname>|<ip>
    sudo salt 'node' multi.ping <hostname>|<ip> <hostname>|<ip>....
'''


def _all(func, hosts):
    '''
    Internal function that allow function to perform in all hosts
    '''
    all_instances = []
    # threads should likely scale with cores or interfaces
    cpus = multiprocessing.cpu_count()
    threads = 4 * cpus
    log.debug('multi._all cpus count={}, thread count={}'.format(cpus, threads))
    pool = multiprocessing.dummy.Pool(threads)
    for instance in pool.map(func, hosts):
        all_instances.append(instance)

    return all_instances


def _summarize_iperf(result):
    '''
    Scan the results and summarize for iperf result
    '''
    # pylint: disable=invalid-name,unused-variable
    host, rc, out, err = result
    msg = {}
    msg['server'] = host
    if rc == 0:
        msg['succeeded'] = True
        msg['speed'] = out
        try:
            msg['filter'] = re.match(
                r'.*0.00-10.00.*sec\s(.*Bytes)\s+(.*Mbits/sec)',
                out, re.DOTALL).group(2)
        # pylint: disable=bare-except
        except:
            msg['filter'] = '0 Mbits/sec'
        msg['failed'] = False
        msg['errored'] = False
    if rc == 1:
        msg['succeeded'] = False
        msg['failed'] = True
        msg['errored'] = False
    if rc == 2:
        msg['succeeded'] = False
        msg['failed'] = False
        msg['errored'] = True
    return msg


def _summarize_ping(results):
    '''
    Scan the results and summarize
    '''
    success = []
    failed = []
    errored = []
    slow = []
    avg = []
    for result in results:
        # pylint: disable=invalid-name,unused-variable
        host, rc, out, err = result
        if rc == 0:
            success.append(host)
            rtt = re.match(
                r'.*rtt min/avg/max/mdev = \d+\.?\d+/(\d+\.?\d+)/',
                out, re.DOTALL)
            if rtt:
                avg.append({'avg': float(rtt.group(1)), 'host': host})
        if rc == 1:
            failed.append(host)
        if rc == 2:
            errored.append(host)

    log.debug('multi._summarize_ping average={}'.format(avg))

    if avg:
        avg_sum = sum(i.get('avg') for i in avg) / len(avg)
        if len(avg) > 2:
            for i in avg:
                if (avg_sum * len(avg) / 2) < i.get('avg'):
                    log.debug('_summarize_ping: slow host = {} avg = {}, s'.
                              format(i.get('avg'), avg_sum))
                    slow.append(i.get('host'))
    else:
        avg_sum = 0

    msg = {}
    msg['succeeded'] = len(success)
    if failed:
        msg['failed'] = " ".join(failed)
    if errored:
        msg['errored'] = " ".join(errored)
    if slow:
        msg['slow'] = " ".join(slow)
    msg['avg'] = avg_sum
    return msg


def iperf(server, cpu, port):
    '''
    iperf test to a specific server

    CLI Example:
    .. code-block:: bash
        sudo salt 'node' multi.iperf <hostname>|<ip> <cpu_core> <port>
    '''
    log.debug('iperf server ={}'.format(server))
    return _summarize_iperf(iperf_client_cmd(server, cpu, port))


def iperf_client_cmd(server, cpu=0, port=5200):
    '''
    Use iperf to test minion to server

    CLI Example:
    .. code-block:: bash
    salt 'node' multi.iperf_client_cmd <server_name/ip>
            cpu=<which_cpu_core default 0> port=<default 5200>
    '''
    if IPERF_PATH is None or not server:
        if not server:
            return [LOCALHOST_NAME, 2, "0", "Server name is empty"]
        else:
            return [LOCALHOST_NAME, 2, "0",
                    "iperf3 not found in path, please install"]
    iperf_cmd = ["/usr/bin/iperf3", "-fm", "-A"+str(cpu),
                 "-t10", "-c"+server, "-p"+str(port)]
    log.debug('iperf_client_cmd: cmd {}'.format(iperf_cmd))
    proc = Popen(iperf_cmd, stdout=PIPE, stderr=PIPE)
    proc.wait()
    return server, proc.returncode, proc.stdout.read(), proc.stderr.read()


def iperf_server_cmd(cpu=0, port=5200):
    '''
    Use iperf to test minion to server

    CLI Example:
    .. code-block:: bash
    salt 'node' multi.iperf_server_cmd <server_name/ip>
        cpu=<which_cpu_core default 0> port=<default 5200>
    '''
    if IPERF_PATH is None:
        return LOCALHOST_NAME + ": iperf3 not found in path, please install"
    iperf_cmd = ["/usr/bin/iperf3", "-s", "-D", "-A"+str(cpu), "-p"+str(port)]
    log.debug('iperf_server_cmd: cmd {}'.format(iperf_cmd))
    Popen(iperf_cmd)
    # it doesn't report fail so no need to check
    return LOCALHOST_NAME + ": iperf3 started at cpu " + str(cpu) + " port " + str(port) + "\n"


def kill_iperf_cmd():
    '''
    Clean up all the iperf3 server and clean it.
    '''
    kill_cmd = ["/usr/bin/killall", "-9", "iperf3"]
    log.debug('kill_iperf_cmd: cmd {}'.format(kill_cmd))
    Popen(kill_cmd)
    return True


def ping(*hosts):
    '''
    Ping a list of hosts and summarize the results

    CLI Example:
    .. code-block:: bash
        sudo salt 'node' multi.ping <hostname>|<ip> <hostname>|<ip>....
    '''
    # I should be filter all the localhost here?
    log.debug('ping hostlist={}'.format(list(hosts)))
    results = _all(ping_cmd, list(hosts))
    return _summarize_ping(results)


def ping_cmd(host):
    '''
    Ping a host with 1 packet and return the result

    CLI Example:
    .. code-block:: bash
        sudo salt 'node' multi.ping_cmd <hostname>|<ip>
    '''
    cmd = ["/usr/bin/ping", "-c1", "-q", "-W1", host]
    log.debug('ping_cmd hostname={}'.format(host))
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    proc.wait()
    return host, proc.returncode, proc.stdout.read(), proc.stderr.read()


def jumbo_ping(*hosts):
    '''
    Ping a list of hosts and summarize the results

    CLI Example:
    .. code-block:: bash
        sudo salt 'node' multi.ping <hostname>|<ip> <hostname>|<ip>....
    '''
    # I should be filter all the localhost here?
    log.debug('jumbo_ping hostlist={}'.format(list(hosts)))
    results = _all(jumbo_ping_cmd, list(hosts))
    return _summarize_ping(results)


def jumbo_ping_cmd(host):
    '''
    Ping a host with 1 packet and return the result

    CLI Example:
    .. code-block:: bash
        sudo salt 'node' multi.ping_cmd <hostname>|<ip>
    '''
    cmd = ["/usr/bin/ping", "-Mdo", "-s8972", "-c1", "-q", "-W1", host]
    log.debug('ping_cmd hostname={}'.format(host))
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    proc.wait()
    return host, proc.returncode, proc.stdout.read(), proc.stderr.read()


def prepare_iperf_server():
    '''
    Create N server base on the total core number of your cpu count

    CLI Example:
    .. code-block:: bash
    salt 'node' multi.prepare_iperf_server

    '''
    cpus = multiprocessing.cpu_count()
    iperf_log = ""
    for cpu in range(cpus):
        iperf_log += iperf_server_cmd(cpu, 5200+cpu)
    return iperf_log
