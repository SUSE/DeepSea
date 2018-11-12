# -*- coding: utf-8 -*-
"""
Module for functional tests that need to be invokved on individual minions.
"""

from __future__ import absolute_import
import yaml


def verify_engulf():
    """
    Compare pillar data pre-engulf and post-engulf to ensure the engulfed
    policy.cfg has the same effect as the original.  Requires pillar data
    saved as /tmp/pillar-pre-engulf.yml and /tmp/pillar-post-engulf.yml.
    """

    with open('/tmp/pillar-pre-engulf.yml') as file:
        old_pillar = yaml.safe_load(file)
    with open('/tmp/pillar-post-engulf.yml') as file:
        new_pillar = yaml.safe_load(file)

    # ensure configuration_init is set correctly post-engulf
    if 'configuration_init' not in new_pillar['local']:
        raise RuntimeError("configuration_init not set after engulf")
    if new_pillar['local']['configuration_init'] != 'default-import':
        raise RuntimeError("configuration_init is {}".format(
                           new_pillar['local']['configuration_init']))

    # if both master and admin roles are assigned to the same node, the engulf
    # will only detect the master role (it's redundant to specify both), so
    # remove the admin role if it was present else the later comparison will fail
    if 'master' in old_pillar['local']['roles'] and 'admin' in old_pillar['local']['roles']:
        old_pillar['local']['roles'].remove('admin')

    # need to sort the role lists, as they can be in different orderes
    old_pillar['local']['roles'].sort()
    new_pillar['local']['roles'].sort()

    if new_pillar['local']['roles'] != old_pillar['local']['roles']:
        raise RuntimeError("role mismatch ({} vs {})".format(
                           old_pillar['local']['roles'], new_pillar['local']['roles']))

    # need to remove configuration_init so final comparison will work
    del new_pillar['local']['configuration_init']

    if new_pillar != old_pillar:
        raise RuntimeError("unexpected pillar mismatch after engulf")
