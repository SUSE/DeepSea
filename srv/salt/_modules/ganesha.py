#!/usr/bin/python

import salt.config
import logging
from subprocess import call, Popen, PIPE

log = logging.getLogger(__name__)

def configurations():
    """
    Return the ganesha configurations.  The three answers are

    ganesha_configurations as defined in the pillar
    ganesha if defined
    [] for no ganesha
    """
    if 'roles' in __pillar__:
        if 'ganesha_configurations' in __pillar__:
            return list(set(__pillar__['ganesha_configurations']) &
                        set(__pillar__['roles']))
        if 'ganesha' in __pillar__['roles']:
            return [ 'ganesha' ]
    return []


