# -*- coding: utf-8 -*-

import os
import time

class SafetyFile(object):
    """
    Common filename between functions
    """

    def __init__(self, cluster):
        self.filename = "/run/salt/master/safety.{}".format(cluster)

def safety(cluster = 'ceph'):
    """
    Touch a file.  Need to allow cluster setting from environment.
    """
    s = SafetyFile(cluster)
    with open(s.filename, "w") as safe_file:
        safe_file.write("")
        return "safety is now disabled for cluster {}".format(cluster)


def check(cluster = 'ceph'):
    """
    Check that time stamp of file is less than one minute
    """
    s = SafetyFile(cluster)
    stamp = os.stat(s.filename).st_mtime
    return stamp + 60 > time.time()


    
