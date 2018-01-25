# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods,modernize-parse-error
"""
Runner to remove a single osd
"""

from __future__ import absolute_import
from __future__ import print_function
import logging
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
import salt.client
import salt.runner

log = logging.getLogger(__name__)


def help_():
    """
    Usage
    """
    usage = ('salt-run remove.osd id:\n\n'
             '    Removes an OSD\n'
             '\n\n')
    print(usage)
    return ""


def osd(id_, drain=False):
    """
    Removes an OSD gracefully
    """
    runner_cli = salt.runner.RunnerClient(
        salt.config.client_config('/etc/salt/master'))

    if not runner_cli.cmd('disengage.check'):
        log.error(('Safety is not disengaged...refusing to remove OSD',
                  ' run "salt-run disengage.safety" first'
                   ' THIS WILL CAUSE DATA LOSS.'))
        return False

    if id_ < 0:
        log.error('Bogus id supplied...OSDs have IDs >= 0')
        return False

    local_cli = salt.client.LocalClient()

    osds = local_cli.cmd('I@roles:storage', 'osd.list', tgt_type='compound')

    host = ''
    for _osd in osds:
        if '{}'.format(id_) in osds[_osd]:
            host = _osd
            break
    else:
        log.error('No OSD with ID {} found...giving up'.format(id_))
        return False

    master_minion = list(local_cli.cmd('I@roles:master', 'pillar.get',
                                       ['master_minion'],
                                       tgt_type='compound').items())[0][1]

    if drain:
        log.info('Draining OSD {} now'.format(id_))
        ret = local_cli.cmd(host, 'osd.zero_weight', [id_])

    log.info('Setting OSD {} out'.format(id_))

    ret = local_cli.cmd(master_minion, 'cmd.run',
                        ['ceph osd out {}'.format(id_)])

    log.info('Stopping and wiping OSD {} now'.format(id_))

    ret = local_cli.cmd(host, 'osd.remove', [id_])
    log.info(ret)

    ret = local_cli.cmd(master_minion, 'cmd.run',
                        ['ceph osd crush remove osd.{}'.format(id_)])
    log.info(ret)
    ret = local_cli.cmd(master_minion, 'cmd.run',
                        ['ceph auth del osd.{}'.format(id_)])
    log.info(ret)
    ret = local_cli.cmd(master_minion, 'cmd.run',
                        ['ceph osd rm {}'.format(id_)])
    log.info(ret)

    return True

__func_alias__ = {
                 'help_': 'help',
                 }
