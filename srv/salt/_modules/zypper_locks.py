# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
"""
Normally, this would not be needed.  The logic for detecting zypper locks
is in the zypper.py module.  However, that module has had other issues
resulting in stack traces.  The workaround is to specify the zypper command
directly and this module is then necessary.
"""

import sys
from subprocess import Popen, PIPE
import time
import logging


log = logging.getLogger(__name__)


def ready(**kwargs):
    """
    Wait until zypper has no locks
    """
    defaults = {'sleep': 6}
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
