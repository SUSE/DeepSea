# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error

"""
Normally, this would not be needed.  The logic for detecting zypper locks
is in the zypper.py module.  However, that module has had other issues
resulting in stack traces.  The workaround is to specify the zypper command
directly and this module is then necessary.
"""

from __future__ import absolute_import
from __future__ import print_function
import sys
from subprocess import Popen, PIPE
import time
import logging
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin


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
            line = __salt__['helper.convert_out'](line)
            print(line)
        for line in proc.stderr:
            line = __salt__['helper.convert_out'](line)
            sys.stderr.write(line)
        if proc.returncode != 0:
            wait_time = sleep
            log.warning("Locked - Waiting {} seconds".format(wait_time))
            time.sleep(wait_time)
            continue
        else:
            log.warning("Unlocked")
            return
