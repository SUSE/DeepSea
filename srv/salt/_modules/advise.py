# -*- coding: utf-8 -*-
"""
Some steps surprise new users.  This module should print nice messages to
explain those steps to the unwary.  There is a separate runner with the
same name and purpose but different functions.

Note: Calling subprocesses in runners does not work
"""

from __future__ import absolute_import
import logging
from subprocess import Popen, PIPE

log = logging.getLogger(__name__)


def reboot(running, installed):
    """
    Make this the last message seen when a minion reboots.
    """
    message = 'Rebooting to upgrade from kernel {} to {}.'.format(running, installed)
    log.info(message)

    proc = Popen(["/usr/bin/wall"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    proc.communicate(input=message)

    return True


def generic(message):
    """
    Used to print arbitrary text to the screen.
    """
    message = str(message)
    log.info(message)

    proc = Popen(["/usr/bin/wall"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    proc.communicate(input=message)

    return True
