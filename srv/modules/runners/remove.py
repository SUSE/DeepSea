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
    # Specifically for Salt integration testing
    # The 'arg' keyword is passed as a kwarg to the salt.runner
    # See delay.sls and multiple.sls for examples
    if not args:
        if 'arg' in kwargs and kwargs['arg']:
            args = kwargs['arg']

    if not args:
        help()
        return ""
    kwargs['remove'] = 'remove'
    result = __salt__['replace.osd'](*args, called=True, **kwargs)

    if result == "":
        return ""

    master_minion = result['master_minion']

    local = salt.client.LocalClient()


    for osd_id in args:
        # All of these commands return success whether the operation succeeds
        # or fails.  For addressing race conditions and slow responding
        # clusters, run each twice.
        cmds = ['ceph osd crush remove osd.{}'.format(osd_id),
                'ceph osd crush remove osd.{}'.format(osd_id),
                'ceph auth del osd.{}'.format(osd_id),
                'ceph auth del osd.{}'.format(osd_id),
                'ceph osd rm {}'.format(osd_id),
                'ceph osd rm {}'.format(osd_id)]

        print("Removing osd {} from Ceph".format(osd_id))
        for cmd in cmds:
            local.cmd(master_minion, 'cmd.run', [cmd], expr_form='compound')

    return ""


__func_alias__ = {
                 'help_': 'help',
                 }
