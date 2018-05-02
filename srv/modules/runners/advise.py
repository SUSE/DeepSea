# -*- coding: utf-8 -*-

import salt.client
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

def help():
    """
    Usage
    """
    usage = ('salt-run advise.salt_run:\n\n'
             '    Passive message about the salt-run command\n'
             '\n\n'
             'salt-run advise.salt_upgrade:\n\n'
             '    Passive message about upgrading the Salt master\n'
             '\n\n'
             'salt-run advise.networks:\n\n'
             '    Passive message about public and cluster networks\n'
             '\n\n'
    )
    print usage
    return ""

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


def salt_upgrade():
    """
    Advise the installer that if the upgrade fails, rerun the orchestration.
    """
    message = '''
        *************** PLEASE READ ***********************
        Upgrading the salt master may result in an initial
        failure.  Rerun the orchestration a second time to
        continue the upgrade.
        ***************************************************'''

    print message
    return message


def no_cluster_detected():
    """
    Advise the installer that if the upgrade fails, rerun the orchestration.
    """
    message = '''
        *************** PLEASE READ ***********************
        You triggered an update but we couldn't find any
        trace of a ceph cluster. Please make sure to have
        setup DeepSea correctly and start the upgrade again.
        ***************************************************'''

    print message
    return message


def networks():
    """
    Advise the installer the current network settings.
    """
    local = salt.client.LocalClient()
    public = set(local.cmd('*' , 'pillar.get', [ 'public_network' ]).values())
    cluster = set(local.cmd('*' , 'pillar.get', [ 'cluster_network' ]).values())

    bold = '\033[1m'
    endc = '\033[0m'

    print "{:25}: {}{}{}".format('public network', bold, ", ".join(filter(None, public)), endc)
    print "{:25}: {}{}{}".format('cluster network', bold, ", ".join(filter(None, cluster)), endc)
    return ""


def osds():
    """
    Inform the admin of pending changes and appropriate actions

    Note: I went with the mapping here such as 'unconfigured' implies
    'deploy'.  This is more about communicating with the maintainers
    although picking the "best" name and propogating may be a solution.

    The deploy and redeploy are osd methods.
    """
    local = salt.client.LocalClient()
    report = local.cmd('I@roles:storage', 'osd.report',
                       ['human=False'], tgt_type="compound")

    bold = '\033[1m'
    endc = '\033[0m'

    unconfigured = _tidy('unconfigured', report)
    changed = _tidy('changed', report)
    unmounted = _tidy('unmounted', report)

    messages = {'deploy': {'header': '\nThese devices will be deployed',
                           'footer': "Run 'salt-run state.orch ceph.stage.3'"},
                'redeploy': {'header': "\nThe devices will be redeployed",
                             'footer': "Run 'salt-run state.orch ceph.migrate.osds'"},
                'stale': {'header': "\nVerify that these devices are in the desired state",
                          'footer': "Run 'salt MINION osd.delete_grain ID' for a stale entry"}}

    if unconfigured:
        print(messages['deploy']['header'])
        print("{}{}{}".format(bold, unconfigured, endc))
        print(messages['deploy']['footer'])

    if changed:
        print(messages['redeploy']['header'])
        print("{}{}{}".format(bold, changed, endc))
        print(messages['redeploy']['footer'])

    if unmounted:
        print(messages['stale']['header'])
        print("{}{}{}".format(bold, unmounted, endc))
        print(messages['stale']['footer'])

    return ""


def _tidy(key, report):
    """
    Return a line of minion followed by comma separated devices if present
    """
    line = ""
    for minion in sorted(report):
        if report[minion][key]:
            if len(minion) + len(", ".join(report[minion][key])) < 80:
                line += "{}: {}\n".format(minion, ", ".join(sorted(report[minion][key])))
            else:
                line += "\n{}:\n  {}\n".format(minion, "\n  ".join(sorted(report[minion][key])))
    return line

__func_alias__ = {
                 'help_': 'help',
                 }

