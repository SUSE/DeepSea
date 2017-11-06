# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
"""
The original purpose of this runner is to verify that proceeding with an
upgrade is safe.  All expected processes are running.

A secondary purpose is a utility to check the current state of all processes.
"""

import pprint
import os
import sys
import logging
import salt.client
import salt.utils
import salt.utils.master

log = logging.getLogger(__name__)


def help_():
    """
    Usage
    """
    usage = ('salt-run cephprocesses.check:\n\n'
             '    Checks the process status according to assigned role\n'
             '\n\n'
             'salt-run cephprocesses.mon:\n\n'
             '    Query monitors to determine if Ceph cluster is active\n'
             '\n\n'
             'salt-run cephprocesses.wait:\n\n'
             '    Wait for all processes to be up according to assigned roles\n'
             '\n\n')
    print usage
    return ""


# pylint: disable=dangerous-default-value
def check(cluster='ceph', roles=[], tolerate_down=0, verbose=True):
    """
    Query the status of running processes for each role.  Also, verify that
    all minions assigned roles do respond.  Return False if any fail.
    """
    search = "I@cluster:{}".format(cluster)

    if not roles:
        roles = _cached_roles(search)

    status = _status(search, roles, verbose)

    log.debug("roles: {}".format(pprint.pformat(roles)))
    log.debug("status: {}".format(pprint.pformat(status)))

    ret = True

    for role in status:
        for minion in status[role]:
            if status[role][minion] is False:
                if tolerate_down == 0:
                    log.error("ERROR: {} process on {} is not running".format(role, minion))
                    ret = False
                tolerate_down -= 1

    return ret


def mon(cluster='ceph'):
    """
    Query all monitors.  If any are running, assume cluster is running and
    return true.  The purpose of this function is to act as a conditional
    to determines whether minion steps should happen serially or in parallel.
    """
    status = _status("I@cluster:{}".format(cluster), ['mon'], False)
    for minion in status['mon']:
        if status['mon'][minion]:
            return True
    return False


def _status(search, roles, verbose):
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
                                 roles=roles,
                                 verbose=verbose,
                                 expr_form="compound")

    sys.stdout = _stdout
    log.debug(pprint.pformat(status))
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
    for minion in cached:
        if 'roles' in cached[minion]:
            for role in cached[minion]['roles']:
                roles.setdefault(role, []).append(minion)

    log.debug(pprint.pformat(roles))
    return roles.keys()


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
                       ['timeout={}'.format(settings['timeout']),
                        'delay={}'.format(settings['delay'])],
                       expr_form="compound")

    sys.stdout = _stdout
    log.debug("status: {}".format(pprint.pformat(status)))
    if False in status.values():
        for minion in status:
            if status[minion] is False:
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
    virtual = local.cmd(search, 'grains.get', ['virtual'], expr_form="compound")
    if 'physical' in virtual.values():
        return 900
    else:
        return 120

__func_alias__ = {
                 'help_': 'help',
                 }
