# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods,modernize-parse-error
"""
Runner to remove a single osd
"""

from __future__ import absolute_import
from __future__ import print_function
import time
import logging
import os
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client
import salt.runner

log = logging.getLogger(__name__)


def help_():
    """
    Usage
    """
    usage = ('salt-run replace.osd id [id ...][force=True][timeout=value][delay=value]:\n\n'
             '    Removes an OSD from a minion\n'
             '\n\n')
    print(usage)
    return ""


def osd(*args, **kwargs):
    """
    Remove an OSD gracefully or forcefully on the minion

    Note: If I were not in Salt, this whole routine would become a library.
    This runner can be called by remove.osd and is only different by three
    commands.  However, we have one runner call and multiple module calls below.
    Trying to refactor these module calls into a __utils__ would require yet
    another module.  Debugging all of this at runtime would be add to the fun,
    so I didn't.
    """
    # Parameters for osd.remove module
    supported = ['force', 'timeout', 'delay']
    passed = ["{}={}".format(k, v) for k, v in kwargs.items() if k in supported]
    log.debug("Converted kwargs: {}".format(passed))

    # OSDs to remove
    if args:
        osds = list(str(arg) for arg in args)
    if 'arg' in kwargs:
        # for orchestrations
        osds = list(str(arg) for arg in kwargs['arg'])

    if _checks_failed(osds, kwargs):
        return ""

    local = salt.client.LocalClient()
    master_minion = _master_minion(local)
    host_osds = local.cmd('I@roles:storage', 'osd.list', expr_form='compound')

    completed = osds
    for osd_id in osds:
        host = _find_host(osd_id, host_osds)
        if host:
            msg = _remove_osd(local, master_minion, osd_id, passed, host)
            if msg:
                print("{}\nFailed to remove osd {}".format(msg, osd_id))
                completed.remove(osd_id)
                continue

            # Rename minion profile
            minion_profile(host)

    if 'called' in kwargs and kwargs['called']:
        # Return for remove.osd
        return {'master_minion': master_minion, 'osds': completed}
    return ""


def _checks_failed(osds, kwargs):
    """
    Check the safety, argument length.  Pause when multiple arguments are
    passed to allow the admin to abort incorrect shell expansions
    """
    # Checks
    if not __salt__['disengage.check']():
        log.error('Safety engaged...run "salt-run disengage.safety"')
        return True

    if len(osds) < 1:
        help_()
        return True

    if len(osds) > 1:
        # Pause for a moment, let the admin see what they passed
        print("Removing osds {} from minions\nPress Ctrl-C to abort".format(", ".join(osds)))
        pause = 5
        if 'pause' in kwargs and kwargs['pause']:
            pause = kwargs['pause']
        time.sleep(pause)

    return False


def _remove_osd(local, master_minion, osd_id, passed, host):
    """
    Set OSD to out, remove OSD from minion
    """
    local.cmd(master_minion, 'cmd.run',
              ['ceph osd out {}'.format(osd_id)],
              expr_form='compound')

    print("Removing osd {} from minion {}".format(osd_id, host))
    msg = local.cmd(host, 'osd.remove', [osd_id] + passed)[host]
    while msg.startswith("Timeout"):
        print("  {}\nRetrying...".format(msg))
        msg = local.cmd(host, 'osd.remove', [osd_id] + passed)[host]
    return msg


def _master_minion(local):
    """
    Return the master minion
    """
    return local.cmd('I@roles:master', 'pillar.get',
                                  ['master_minion'],
                                  expr_form='compound').items()[0][1]


def _find_host(osd_id, host_osds):
    """
    Search lists for ID, return host
    """
    for host in host_osds:
        if str(osd_id) in host_osds[host]:
            return host
    return ""


def minion_profile(minion):
    """
    Rename a minion profile to indicate that the minion profile needs to be
    recreated.

    Note: Nobody is required to have profile entries in the policy.cfg.  Some
    might be modifying their pillar data directly.  Also, the file will
    not exist when called for multiple replacements.  Lastly, minions may
    belong to more than one hardware profile.  Each must be renamed.
    """
    files = __salt__['push.organize']()

    yaml_file = 'stack/default/ceph/minions/{}.yml'.format(minion)
    if yaml_file in files:
        for filename in files[yaml_file]:
            if os.path.exists(filename):
                print("Renaming minion {} profile".format(minion))
                os.rename(filename, "{}-replace".format(filename))
    return ""


__func_alias__ = {
                 'help_': 'help',
                 }
