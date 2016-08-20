#!/usr/bin/python

import os
import sys
from subprocess import Popen, PIPE
import time
import logging


log = logging.getLogger(__name__)
       
    
def ready(**kwargs):
    """
    """
    defaults = { 'sleep': 6 }
    defaults.update(kwargs)

    cmd = 'zypper locks'
    sleep = defaults['sleep']

    while True:
        log.debug("Running {}".format(cmd))
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        proc.wait()
        for line in proc.stdout:
            print line
        for line in proc.stderr:
            sys.stderr.write(line)
        if proc.returncode != 0:
            wait_time = sleep
            log.warn("Locked - Waiting {} seconds".format(wait_time))
            time.sleep(wait_time)
            continue
        else:
            log.warn("Unlocked")
            return
        

