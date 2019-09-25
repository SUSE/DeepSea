# -*- coding: utf-8 -*-
'''
Management of Podman Containers

:depends: Podman

.. note::
    This is a quick and dirty solution for management of Podman containers.

    Podman support is not yet available from SaltStack:
        https://github.com/saltstack/salt/issues/50624

    Likewise, the Python bindings for Podman are not yet packaged for SLE15:
        https://github.com/docker/docker-py

    This solution should be replaced when the above upstream components
    become available downstream.
'''

__docformat__ = 'restructuredtext en'

import functools
import logging
import salt.utils.path

PODMAN_BIN = salt.utils.path.which('podman')

# Set up logging
log = logging.getLogger(__name__)


def run(name, *args, **kwargs):
    '''
    Append the args to the base podman command, then execute.  Check prerequisites.  Log everything.
    '''
    ret = __utils__['ret.returnstruct'](name)

    cmd = [PODMAN_BIN, 'run', '--rm', '--net=host']

    # command args
    if args:
        cmd.extend(*args)

    ret['command'] = ' '.join([x.strip() for x in cmd])
    log.info(cmd)
    result = __salt__['cmd.run_all'](cmd, **kwargs)
    log.info(f"{result}")

    ret['stdout'] = result['stdout']
    ret['stderr'] = result['stderr']
    ret['returncode'] = result['retcode']

    if ret['returncode'] == 0:
        ret['result'] = True
    return ret
