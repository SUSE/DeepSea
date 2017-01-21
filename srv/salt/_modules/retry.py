#!/usr/bin/python

import os
import sys
from subprocess import Popen, PIPE
import time
import logging


log = logging.getLogger(__name__)


def cmd(**kwargs):
    """
    Retry commands with a backoff delay
    """
    defaults = { 'retry': 3, 'sleep': 6 }
    defaults.update(kwargs)

    cmd = defaults['cmd']
    retry = defaults['retry']
    sleep = defaults['sleep']

    for attempt in range(1, retry + 1):
        log.debug("Running {} on attempt {}".format(cmd, attempt))
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        for line in proc.stdout:
            print line
        for line in proc.stderr:
            sys.stderr.write(line)
        if proc.returncode != 0:
            if attempt < retry:
                wait_time = sleep * attempt
                log.warn("Waiting {} seconds to try {} again".format(wait_time, cmd))
                time.sleep(wait_time)
            continue
        else:
            return

    log.warn("command {} failed {} retries".format(cmd, retry))
    raise RuntimeError("cmd {} failed {} retries".format(cmd, retry))

def pkill(**kwargs):
    """
    Continually kill respawning processes until the pattern fails to match or
    the retries are exhausted
    """
    defaults = { 'retry': 3, 'sleep': 1 }
    defaults.update(kwargs)

    if 'signal' in kwargs:
      cmd = "pkill -{} {}".format(kwargs['signal'], kwargs['pattern'])
    else:
      cmd = "pkill {}".format(kwargs['pattern'])
    retry = defaults['retry']
    sleep = defaults['sleep']

    for attempt in range(1, retry + 1):
        log.debug("Running {} on attempt {}".format(cmd, attempt))
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        for line in proc.stdout:
            print line
        for line in proc.stderr:
            sys.stderr.write(line)
        if proc.returncode == 0:
            if attempt < retry:
                wait_time = sleep * attempt
                log.warn("Waiting {} seconds to try {} again".format(wait_time, cmd))
                time.sleep(wait_time)
            continue
        else:
            return

    log.warn("command {} failed {} retries".format(cmd, retry))
    raise RuntimeError("cmd {} failed {} retries".format(cmd, retry))
