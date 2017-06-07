# -*- coding: utf-8 -*-

import logging
from subprocess import check_output
import salt.runner

"""
Runner to remove a single osd
"""

log = logging.getLogger(__name__)


def osd(id_, drain=True):
    runner_cli = salt.runner.RunnerClient()

    if not runner_cli.cmd('disengage.check'):
        log.error(('Safety is not disengaged...refusing to remove OSD\nrun',
                  '"salt-run disengage.safety" first'
                   'THIS WILL CAUSE DATA LOSS.'))
        return False

    if id_ < 0:
        log.error('Bogus id supplied...OSDs have IDs >= 0')
        return False

    local_cli = salt.client.LocalClient()

    osds = local_cli.cmd('I@roles:storage', 'osd.list', expr_form='compound')

    host = ''
    for osd in osds:
        if id_ in osds[osd]:
            host = osd
            break
    else:
        log.error('No OSD with ID {} found...giving up'.format(id_))
        return False

    if drain:
        log.info('Draining OSD {} now'.format(id_))
        ret = local_cli.cmd(host, 'osd.zero_weight', [id_])

    log.info('Setting OSD {} out'.format(id_))

    check_output(['ceph', 'osd', 'rm', '{}'.format(id_)])

    log.info('Stoping and wiping OSD {} now'.format(id_))

    ret = local_cli.cmd(host, 'osd.remove', [id_])

    if ret is not "":
        log.error('osd.remove returned {}'.format(ret))
        return False

    check_output(['ceph', 'osd', 'crush', 'remove', 'osd.{}'.format(id_)])
    check_output(['ceph', 'auth', 'del', 'osd.{}'.format(id_)])
    check_output(['ceph', 'osd', 'rm', '{}'.format(id_)])

    return True
