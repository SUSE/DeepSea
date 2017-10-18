# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
"""
Display the sharedsecret for the Salt API
"""
import os


def help_():
    """
    Usage
    """
    usage = ('salt-run sharedsecret.show:\n\n'
             '    Shows the shared secret for the Salt API\n'
             '\n\n')
    print usage
    return ""


def show():
    '''
    This function reads the contents of the sharedsecret.conf file and parses the secret key.
    This file has the following structure:

    ``sharedsecret: <secret_key>``

    Returns:
        str: the secret key used by salt-api sharedsecret eauth

    '''
    filename = '/etc/salt/master.d/sharedsecret.conf'
    if not os.path.exists(filename):
        return None
    with open(filename, 'r') as fhandler:
        line = fhandler.readline()
        idx = line.find(':')
        if idx == -1:
            return None
        return line[idx+2:]

__func_alias__ = {
                 'help_': 'help',
                 }
