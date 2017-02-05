#!/usr/bin/python

from subprocess import call, Popen, PIPE
import logging
import multiprocessing.dummy
import multiprocessing

log = logging.getLogger(__name__)


def _all(func, hosts):
    '''
    Apply function to all hosts
    '''
    all_instances = []
    # threads should likely scale with cores or interfaces
    threads = 4
    pool = multiprocessing.dummy.Pool(threads)
    for instance in pool.map(func, hosts):
        all_instances.append(instance)
    
    return all_instances


def ping_cmd(host):
    '''
    Ping a host and return the result
    '''
    cmd = [ "/usr/bin/ping", "-c1", "-q", host ]
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    proc.wait()
    return host, proc.returncode, proc.stdout.read(), proc.stderr.read()
    
def _summarize(results):
    '''
    Scan the results and summarize
    '''
    success = []
    failed = []
    errored = []
    for result in results:
        host, rc, out, err = result
        if rc == 0:
            success.append(host)
        if rc == 1:
            failed.append(host)
        if rc == 2:
            errored.append(host)

    msg = {}
    msg['succeeded'] = len(success)
    if failed:
        msg['failed'] = " ".join(failed)
    if errored:
        msg['errored'] = " ".join(errored)
    return msg

def ping(*hosts):
    '''
    Ping all hosts
    '''
    results = _all(ping_cmd, list(hosts))
    return _summarize(results)

