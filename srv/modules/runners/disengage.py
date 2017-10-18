# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods,modernize-parse-error

"""
Some operations are inherently dangerous, but still necessary.  Allow
the modification timestamp of a file to give a window in which to run.
"""

import os
import time


class SafetyFile(object):
    """
    Common filename between functions
    """

    def __init__(self, cluster):
        self.filename = "/run/salt/master/safety.{}".format(cluster)


def help_():
    """
    Usage
    """
    usage = ('salt-run disengage.safety:\n\n'
             '    Touches a file to signify imminent dangerous operations\n'
             '\n\n'
             'salt-run disengage.check:\n\n'
             '    Check whether the timestamp is less than a minute old\n'
             '\n\n')
    print usage
    return ""


def safety(cluster='ceph'):
    """
    Touch a file.  Need to allow cluster setting from environment.
    """
    sff = SafetyFile(cluster)
    with open(sff.filename, "w") as safe_file:
        safe_file.write("")
        return "safety is now disabled for cluster {}".format(cluster)


def check(cluster='ceph'):
    """
    Check that time stamp of file is less than one minute
    """
    sff = SafetyFile(cluster)
    if os.path.exists(sff.filename):
        stamp = os.stat(sff.filename).st_mtime
        return stamp + 60 > time.time()
    else:
        return False

__func_alias__ = {
                 'help_': 'help',
                 }
