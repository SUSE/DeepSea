#!/usr/bin/python

import time
import logging
import os
from subprocess import call, Popen, PIPE

log = logging.getLogger(__name__)


"""
Some steps surprise new users.  This runner should print nice messages to
explain those steps to the unwary.
"""


def reboot(running, installed):
    """
    Make this the last message seen when a minion reboots.
    """
    message = 'Rebooting to upgrade from kernel {} to {}.'.format(running, installed)
    log.info(message)

    proc = Popen([ "/usr/bin/wall" ], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = proc.communicate(input=message)

    return True


def salt_run():
    """
    The salt-run commands report when complete.  This can be unnerving to
    the first time salt user.
    """
    message = '''
###########################################################################
The salt-run command reports when all minions complete.  Until then, the
command may appear to hang.  Interrupting (e.g. Ctrl-C) does not stop
the command.

In another terminal, try 'salt-run jobs.active' or
'salt-run state.event pretty=True' to see progress.
###########################################################################
    '''

    return message


