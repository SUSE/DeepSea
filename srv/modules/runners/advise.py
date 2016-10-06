#!/usr/bin/python

import time
import logging
import os

log = logging.getLogger(__name__)


"""
Some steps surprise new users.  This runner should print nice messages to
explain those steps to the unwary.  There is a module with the same name
and purpose but different functions.

Note: a runner's output displays immediately unlike a module
"""


def salt_run():
    """
    The salt-run commands report when complete.  This can be unnerving to
    the first time salt user.
    """
    message = '''
###########################################################
The salt-run command reports when all minions complete.
The command may appear to hang.  Interrupting (e.g. Ctrl-C) 
does not stop the command.

In another terminal, try 'salt-run jobs.active' or
'salt-run state.event pretty=True' to see progress.
###########################################################
    '''

    return message


