# -*- coding: utf-8 -*-
# vim: ts=8 et sw=4 sts=4
# pylint: disable=too-few-public-methods,modernize-parse-error
"""
Runner endpoints for integration specifically with the ceph-mgr orchestrator
"""

from __future__ import absolute_import
import logging
import ipaddress
import os
import sys
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client

log = logging.getLogger(__name__)


def _run_master_module_function(function, *args, **kwargs):
    """
    Used internally by this module to run master.find_pool.  Could also be
    used to run master.minion if it turns out we need that.
    """
    __opts__ = salt.config.client_config('/etc/salt/master')
    __grains__ = salt.loader.grains(__opts__)
    __opts__['grains'] = __grains__
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)
    return __salt__[function](*args, **kwargs)


def get_inventory(nodes=None, roles=None):
    """
    Return an inventory of all devices on all nodes, optionally limited
    to nodes with particular hostnames or roles.  Criteria are OR'd, e.g.
    if multiple roles are passed in, this will inventory all nodes assigned
    to _any_ of the listed roles.  Likewise if multiple nodes are passed,
    all those nodes will be inventoried.

    Examples:

    salt-run mgr_orch.get_inventory roles=mon
    salt-run mgr_orch.get_inventory roles=[mgr,mds]
    salt-run mgr_orch.get_inventory nodes=data1.example.com
    salt-run mgr_orch.get_inventory nodes=[data1.example.com,data5.example.com]
    """

    # The cluster is always named 'ceph'
    search = "I@cluster:ceph"

    if nodes is None:
        nodes = []
    if roles is None:
        roles = []

    # Syntactic sugar (allows passing nodes=foo or roles=bar for single items,
    # rather than having to add the square brackets around one-item lists)
    if not isinstance(nodes, list):
        nodes = [nodes]
    if not isinstance(roles, list):
        roles = [roles]

    criteria = nodes
    for role in roles:
        criteria.append("I@roles:{}".format(role))
    if criteria:
        search = "{} and ( {} )".format(search, " or ".join(criteria))

    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    local = salt.client.LocalClient()
    minions = local.cmd(search, 'cephdisks.all', [], tgt_type="compound")

    sys.stdout = _stdout

    return minions


def describe_service(role=None, service_id=None, node=None):
    """
    Returns a mapping of hostnames to services and daemon IDs for the given
    role and/or service ID and/or node.  Works for mon, mgr, mds and rgw, but
    not for osd (ceph itself already knows what host a given OSD is running on).
    If multiple criteria are specified, they are AND'ed e.g. if a role and a
    service ID are passed in, this will return only the service with that role
    and that service ID.

    The eventual intent of the service_id parameter is to allow querying which
    mds instances are used for a given filesystem, or which rgw instances are
    used for a given zone/realm, but this is not implemented yet (right now,
    if service_id is passed, it will just match against daemon IDs).

    Examples:

    salt-run mgr_orch.describe_service role=mon
    salt-run mgr_orch.describe_service role=rgw service_id=data1
    salt-run mgr_orch.describe_service node=data1
    """

    search = "I@cluster:ceph"

    supported_roles = ['mon', 'mgr', 'mds', 'rgw', 'ganesha', 'igw']

    if role:
        search += " and I@roles:{}".format(role)
    else:
        search += " and ( {} )".format(
                  " or ".join(["I@roles:{}".format(sr) for sr in supported_roles]))

    if node:
        search += " and {}".format(node)

    result = {}

    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    _stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')

    local = salt.client.LocalClient()

    # This is very simple so far; DeepSea always uses short hostnames for
    # daemon IDs, so the mapping is trivial.
    daemon_ids = local.cmd(search, 'grains.item', ['host'], tgt_type="compound")

    minion_roles = local.cmd(search, 'pillar.get', ['roles'], tgt_type="compound")

    nfs_pool = None

    for minion, roles in minion_roles.items():
        minion_result = {}
        for minion_role in roles:
            if minion_role not in supported_roles:
                # skips unsupported roles
                continue
            if role and minion_role != role:
                # skips roles we don't care about if a role was passed in
                continue
            if service_id and daemon_ids[minion]['host'] != service_id:
                # skips IDs we don't care about if one was passed in
                continue
            # pylint: disable=fixme
            # TODO: consider wrapping this in a list if it's possible for DeepSea
            # to deploy multiple services of the same type but with different IDs
            # on the same node.  Of course, DeepSea will deploy mutiple OSDs on
            # the same node, but describe_service doesn't support querying OSDs,
            # so that example doesn't count ;-)
            minion_result[minion_role] = {
                'service_instance': daemon_ids[minion]['host']
            }
            if minion_role == 'ganesha':
                if not nfs_pool:
                    nfs_pool = _run_master_module_function('master.find_pool', ['cephfs', 'rgw'])
                minion_result[minion_role]['rados_config_location'] = (
                    'rados://{}/ganesha/conf-{}'.format(nfs_pool, daemon_ids[minion]['host']))
            if minion_role == 'igw':
                igw_address = local.cmd(minion, 'public.address', [])[minion]
                if isinstance(ipaddress.ip_address(igw_address), ipaddress.IPv6Address):
                    # IPv6 addresses need to be in square brackets in URLs
                    igw_address = "[{}]".format(igw_address)
                igw_username = local.cmd(minion, 'pillar.get',
                                         ['ceph_iscsi_username'])[minion] or 'admin'
                igw_password = local.cmd(minion, 'pillar.get',
                                         ['ceph_iscsi_password'])[minion] or 'admin'
                igw_port = local.cmd(minion, 'pillar.get',
                                     ['ceph_iscsi_port'])[minion] or '5000'
                igw_ssl = local.cmd(minion,
                                    'pillar.get', ['ceph_iscsi_ssl'])[minion] or False
                protocol = 'https' if igw_ssl else 'http'
                minion_result[minion_role]['service_url'] = (
                    '{}://{}:{}@{}:{}'.format(protocol, igw_username, igw_password,
                                              igw_address, igw_port))
        if minion_result:
            result[minion] = minion_result

    sys.stdout = _stdout

    return result
