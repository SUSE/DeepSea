# -*- coding: utf-8 -*-
# pylint: disable=C0111

from __future__ import absolute_import


def show_low_sls(*states):
    result = {}
    for state in states:
        if isinstance(state, dict):
            for key, states2 in state.items():
                res = {}
                for state2 in states2:
                    res[state] = __salt__['state.show_low_sls'](state)
                result[key] = res
        else:
            result[state] = __salt__['state.show_low_sls'](state)
    return result


def user():
    """
    Returns the system user name for running the salt-master and own files
    """
    if __grains__.get('os_family', '') == 'Suse':
        return 'salt'
    return 'root'


def group():
    """
    Returns the system group name used for running the salt-master and own files
    """
    if __grains__.get('os_family', '') == 'Suse':
        return 'salt'
    return 'root'
