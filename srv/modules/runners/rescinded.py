# -*- coding: utf-8 -*-
# pylint: disable=visually-indented-line-with-same-indent-as-next-logical-line
# pylint: disable=modernize-parse-error
#
# The salt-api calls functions with keywords that are not needed
# pylint: disable=unused-argument
"""
The collection of functions for OSDs that are no longer present.
"""

import logging
import salt.client

log = logging.getLogger(__name__)


def help_():
    """
    Usage
    """
    usage = ('salt-run rescinded.ids cluster:\n\n'
             '    Returns the list of OSDs for minions that are no longer storage nodes\n'
             '\n\n'
             'salt-run rescinded.osds:\n\n'
             '    Returns the list of OSDs for minions that are no longer mounted\n'
             '\n\n')
    print usage
    return ""


def ids(cluster, **kwargs):
    """
    List the OSD ids of a minion that is not a storage node
    """

    local = salt.client.LocalClient()

    # Restrict search to this cluster
    search = "I@cluster:{}".format(cluster)

    pillar_data = local.cmd(search, 'pillar.items', [], expr_form="compound")
    _ids = []
    for minion in pillar_data:
        if ('roles' in pillar_data[minion] and
            'storage' in pillar_data[minion]['roles']):
            continue
        data = local.cmd(minion, 'osd.list', [], expr_form="glob")
        _ids.extend(data[minion])
    return _ids


def osds(cluster='ceph'):
    """
    List the OSD ids that are no longer mounted
    """
    search = "I@cluster:{} and I@roles:storage".format(cluster)

    local = salt.client.LocalClient()
    data = local.cmd(search, 'osd.rescinded', [], expr_form="compound")
    _ids = []
    for minion in data:
        if isinstance(data[minion], list):
            _ids.extend(data[minion])
        else:
            log.debug(data[minion])
    return list(set(_ids))

__func_alias__ = {
                 'help_': 'help',
                 }
