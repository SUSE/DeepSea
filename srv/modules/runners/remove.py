# -*- coding: utf-8 -*-

import logging
import salt.client
import salt.runner

"""
Runner to remove a single osd
"""

log = logging.getLogger(__name__)

def help():
    """
    """
    usage = ('salt-run remove.osd id [id ...][force=True]:\n\n'
             '    Removes an OSD\n'
             '\n\n'
    )
    print usage
    return ""


def osd(*args, **kwargs):
    """
    Remove an OSD gracefully or forcefully.  Always attempt to remove
    ID from Ceph even if OSD has been removed from the minion.
    """
    kwargs['remove'] = 'remove'
    result = __salt__['replace.osd'](*args, called=True, **kwargs)

    # Replace OSD exited early
    if not result:
        return ""

    master_minion = result['master_minion']
    osds = result['osds']

    local = salt.client.LocalClient()

    all_osds = local.cmd(master_minion,
                         'cmd.run',
                         ['ceph osd ls -f json'],
                         # backport trap -> expr_form
                         tgt_type='compound')
    all_osds = all_osds[master_minion].strip()

    for osd_id in osds:
        if osd_id not in all_osds:
            print("Couldn't find osd {} in cluster".format(osd_id))
            continue
        cmds = ['ceph osd crush remove osd.{}'.format(osd_id),
                'ceph auth del osd.{}'.format(osd_id),
                'ceph osd rm {}'.format(osd_id)]

        print("Removing osd {} from Ceph".format(osd_id))
        for cmd in cmds:
            local.cmd(master_minion, 'cmd.run', [cmd], expr_form='compound')

    return ""


__func_alias__ = {
                 'help_': 'help',
                 }
