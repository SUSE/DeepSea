# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
"""
Although similar to validate.py, the intention here is to run checks on
all minions in a cluster.  Additionally, these checks are not absolute so
a warning is more appropriate.

"""

import logging
from collections import OrderedDict
import salt.client
import salt.utils.error


log = logging.getLogger(__name__)


# pylint: disable=no-init,too-few-public-methods
class Bcolors(object):
    """
    Define escape sequences
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Checks(object):
    """
    Define a collection of checks to run Salt minions
    """

    def __init__(self, search):
        """
        Set search criteria
        """
        self.search = search
        self.passed = OrderedDict()
        self.warnings = OrderedDict()
        self.local = salt.client.LocalClient()

    def firewall(self):
        """
        Scan all minions for the default firewall settings.  Set warnings
        for any differences.
        """
        contents = self.local.cmd(self.search, 'cmd.shell',
                                  ['/usr/sbin/iptables -S'],
                                  expr_form="compound")
        for minion in contents:
            # Accept custom named chains
            if not contents[minion].startswith(("-P INPUT ACCEPT\n"
                                                "-P FORWARD ACCEPT\n"
                                                "-P OUTPUT ACCEPT")):
                msg = "enabled on minion {}".format(minion)
                if 'firewall' in self.warnings:
                    self.warnings['firewall'].append(msg)
                else:
                    self.warnings['firewall'] = [msg]
        if 'firewall' not in self.warnings:
            self.passed['firewall'] = "disabled"

    def apparmor(self):
        """
        Scan minions for apparmor settings.
        """
        contents = self.local.cmd(self.search, 'cmd.shell',
                                  [('/usr/sbin/apparmor_status --enabled '
                                    '2>/dev/null; echo $?')],
                                  expr_form="compound")
        for minion in contents:
            if contents[minion] and int(contents[minion]) == 0:
                msg = "enabled on minion {}".format(minion)
                if 'apparmor' in self.warnings:
                    self.warnings['apparmor'].append(msg)
                else:
                    self.warnings['apparmor'] = [msg]
        if 'apparmor' not in self.warnings:
            self.passed['apparmor'] = "disabled"

    def report(self):
        """
        Produce nicely colored output
        """
        for attr in self.passed.keys():
            print "{:25}: {}{}{}{}".format(attr, Bcolors.BOLD, Bcolors.OKGREEN,
                                           self.passed[attr], Bcolors.ENDC)
        for attr in self.warnings.keys():
            print "{:25}: {}{}{}{}".format(attr, Bcolors.BOLD, Bcolors.WARNING,
                                           self.warnings[attr], Bcolors.ENDC)


def help_():
    """
    Usage
    """
    usage = ('salt-run ready.check:\n'
             'salt-run ready.check search=target:\n'
             'salt-run ready.check fail_on_warning=False:\n\n'
             '    Check for firewall and apparmor configurations\n'
             '\n\n')
    print usage
    return ""


def check(cluster, fail_on_warning=True, search=None, **kwargs):
    """
    Check a cluster for runtime configurations that may cause issues for an
    installation.
    """
    if cluster is None:
        cluster = kwargs['cluster']

    # Restrict search to this cluster, but allow caller to set search directly.
    # Setting search by caller is needed when DeepSea is engulfing a cluster it
    # did not deploy.  At that point, "I@cluster:ceph" does not contain any
    # minions.
    search = "I@cluster:{}".format(cluster) if not search else search

    _check = Checks(search)
    _check.firewall()
    _check.apparmor()
    _check.report()

    if _check.warnings and fail_on_warning:
        return False
    return True

__func_alias__ = {
                 'help_': 'help',
                 }
