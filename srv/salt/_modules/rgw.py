#!/usr/bin/python

from sets import Set
import salt.config

def configurations():
    """
    Return the rgw configurations.  The three answers are

    rgw_configurations as defined in the pillar
    rgw if defined
    [] for no rgw
    """
    if 'roles' in __pillar__:
        if 'rgw_configurations' in __pillar__:
            return list(Set(__pillar__['rgw_configurations']) &
                        Set(__pillar__['roles']))
        if 'rgw' in __pillar__['roles']:
            return [ 'rgw' ]
    return []
