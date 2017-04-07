# -*- coding: utf-8 -*-

import salt.client
import pprint
import os
import sys
import logging
import salt.utils
import salt.utils.master

log = logging.getLogger(__name__)

"""
The original purpose of this runner is to verify that proceeding with an
upgrade is safe.  All expected processes are running.

A secondary purpose is a utility to check the current state of all processes.
"""


def check(cluster='ceph', roles=[]):
    """
    Query the status of running processes for each role.  Also, verify that
    all minions assigned roles do respond.  Return False if any fail.
    """
    search = "I@cluster:{}".format(cluster)

    if not roles:
        roles = _cached_roles(search)

    status = _status(search, roles)
    
    log.debug("roles: {}".format(pprint.pformat(roles)))
    log.debug("status: {}".format(pprint.pformat(status)))

    ret = True
    for role in roles:
        for minion in roles[role]:
            if minion not in status[role]:
                log.error("ERROR: {} minion did not respond".format(minion))
                ret = False

    for role in status.keys():
        for minion in status[role]:
            if status[role][minion] is False:
                log.error("ERROR: {} process on {} is not running".format(role, minion))
                ret = False

    return ret

def _status(search, roles):
    """
    Return a structure of roles with module results
    """
    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    status = {}
    local = salt.client.LocalClient()

    for role in roles:
        role_search = search + " and I@roles:{}".format(role)
        status[role] = local.cmd(role_search,
                                 'cephprocesses.check',
                                 [roles.keys()],
                                 expr_form="compound")

    log.debug(pprint.pformat(status))

    sys.stdout = _stdout
    return status

def _cached_roles(search):
    """
    Return the cached roles in a convenient structure.  Trust the cached
    values from the master pillar since a downed minion will be absent
    from any dynamic query.  Also, do not worry about downed minions that
    are outside of the search criteria.
    """
    pillar_util = salt.utils.master.MasterPillarUtil(search, "compound",
                                                     use_cached_grains=True,
                                                     grains_fallback=False,
                                                     opts=__opts__)

    cached = pillar_util.get_minion_pillar()
    roles = {}
    for minion in cached.keys():
        if 'roles' in cached[minion]:
            for role in cached[minion]['roles']:
                roles.setdefault(role, []).append(minion)

    log.debug(pprint.pformat(roles))
    return roles


def wait(cluster='ceph', **kwargs):
    """
    Wait for all processes to be up or until the timeout expires.
    """
    settings = {
        'timeout': _timeout(cluster=cluster),
        'delay': 3
    }
    settings.update(kwargs)
    search = "I@cluster:{}".format(cluster)

    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    status = {}
    local = salt.client.LocalClient()
    status = local.cmd(search,
                       'cephprocesses.wait',
                       [ 'timeout={}'.format(settings['timeout']),
                         'delay={}'.format(settings['delay']) ],
                       expr_form="compound")


    sys.stdout = _stdout
    log.debug("status: ".format(pprint.pformat(status)))
    if False in status.values():
        for minion in status.keys():
            if status[minion] == False:
                log.error("minion {} failed".format(minion))
        return False
    return True


def _timeout(cluster='ceph'):
    """
    Assume 15 minutes for physical hardware since some hardware has long
    shutdown/reboot times.  Assume 2 minutes for complete virtual environments.
    """
    local = salt.client.LocalClient()
    search = "I@cluster:{}".format(cluster)
    virtual = local.cmd(search, 'grains.get', [ 'virtual' ], expr_form="compound")
    if 'physical' in  virtual.values():
        return 900
    else:
        return 120
