# -*- coding: utf-8 -*-
"""
Several orchestrations must target the minion running on the Salt master.
Currently, the Salt master and admin node are one in the same.  Originally, the
installation process would populate /srv/pillar/ceph/master_minion.sls.  This
fails in environments where an entire server is built prior to assigning a
 hostname or configuring Salt.

On the off chance that we may have multiple Salt masters or separate the admin
node from the Salt master, keep /srv/pillar/ceph/master_minion.sls to allow the
administrator to override the setting in /etc/salt/minion_id.

Note that this is a module that only runs on the master.
"""

from __future__ import absolute_import
import os
import logging

log = logging.getLogger(__name__)


def minion():
    """
    Return the name of the minion running on the master.  Default to
    reading the minion_id file, but allow overriding with the pillar.
    """
    if __salt__['pillar.get']('master_minion'):
        log.info("Returning pillar value")
        return __salt__['pillar.get']('master_minion')

    id_file = "/etc/salt/minion_id"
    with open(id_file, 'r') as id_fd:
        minion_id = id_fd.readline().rstrip()
        return minion_id
    return ""

