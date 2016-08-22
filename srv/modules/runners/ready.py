#!/usr/bin/python

import salt.client
import salt.utils.error
import logging
import ipaddress
import pprint
import yaml
import os
import re
from subprocess import call, Popen, PIPE
from os.path import dirname

from collections import OrderedDict

log = logging.getLogger(__name__)


"""
Although similar to validate.py, the intention here is to run checks on
all minions in a cluster.  Additionally, these checks are not absolute so
a warning is more appropriate.

"""

class bcolors:
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
        contents = self.local.cmd(self.search , 'cmd.run', [ '/usr/sbin/iptables -S' ], expr_form="compound")
        for minion in contents.keys():
            if contents[minion] != "-P INPUT ACCEPT\n-P FORWARD ACCEPT\n-P OUTPUT ACCEPT":
                msg = "enabled on minion {}".format(minion)
                if 'firewall' in self.warnings:
                    self.warnings['firewall'].append(msg)
                else:
                    self.warnings['firewall'] = [ msg ]
        if 'firewall' not in self.warnings:
            self.passed['firewall'] = "disabled"


    def report(self):
        """
        Produce nicely colored output
        """
        for attr in self.passed.keys():
            print "{:25}: {}{}{}{}".format(attr, bcolors.BOLD, bcolors.OKGREEN, self.passed[attr], bcolors.ENDC)
        for attr in self.warnings.keys():
            print "{:25}: {}{}{}{}".format(attr, bcolors.BOLD, bcolors.WARNING, self.warnings[attr], bcolors.ENDC)


def check(name, fail_on_warning=True, **kwargs):
    """
    Check a cluster for runtime configurations that may cause issues for an
    installation.
    """
    print "fow: ", fail_on_warning

    if name == None:
        name = kwargs['name']

    # Restrict search to this cluster
    search = "I@cluster:{}".format(name)

    c = Checks(search)
    c.firewall()
    c.report()

    if c.warnings and fail_on_warning:
        return False
    return True


