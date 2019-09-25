# -*- coding: utf-8 -*-
"""
The need for this module is that the roles show the intended state and not
the current state.  Once the admin unassigns the monitor role, the pillar
reflects that configuration.
"""

from __future__ import absolute_import
import logging
import os
# pylint: disable=import-error,3rd-party-module-not-gated
from subprocess import check_output, CalledProcessError
import salt.utils


log = logging.getLogger(__name__)


def already_running():
    # check if a container is already running.
    # Check the higher-level instance - systemd.

    ## there needs to be a second check for existence..
    ## we might have the case where a mon is down, but still exists
    ## check for directory existence? or for podman image existance?

    # TODO: refine the logic when to return false/true..

    # is /host/ fine?
    mon_name = __grains__.get('host', '')
    if not mon_name:
        log.error("Could not retrieve host grain. Aborting")
        return False
    # yapf: disable
    try:
        status = check_output(
            ['systemctl', 'is-active',
            f'ceph-mon@{mon_name}.service']).decode('utf-8').strip()
    except CalledProcessError as e:
        log.info(f'{e}')
        return False
    if status == 'active':
        return True
    elif status == 'inactive' or os.path.exists(f'/var/lib/ceph/mon/ceph-{mon_name}'):
        return False
    else:
        log.error(f"Could not determine state of {mon_name}")
        return False
    # yapf: enable


# These contstants may be simpler to maintain in __utils__ as a single
# function over using the pillar
CEPH_ETC_DIR = "/etc/ceph"
CEPH_BASE_DIR = "/var/lib/ceph"
CEPH_TMP_DIR = "/var/lib/ceph/tmp"
CEPH_LOG_DIR = "/var/log/ceph"
CEPH_RUN_DIR = "/var/run/ceph"
CEPH_MON = "/usr/bin/ceph-mon"


def _chown_ceph(pathname):
    '''
    Set the ceph user
    '''
    try:
        os.chown(pathname, 167, -1)  # ceph user
    except FileNotFoundError:
        pass


def createdb(**kwargs):
    '''
    Creating the mon db is similar to creating keyrings.  The ceph mon command
    creates a directory tree where the ceph-authtool creates individual text
    files.
    '''
    container_image = __pillar__.get('container_image', None)
    node_name = __grains__.get('host', None)

    ret = __utils__['ret.returnstruct'](kwargs['__pub_fun'])
    if not container_image:
        return __utils__['ret.err'](
            ret,
            "Container image not set - check `salt-call pillar.get container_image`"
        )
    if not node_name:
        return __utils__['ret.err'](
            ret, "Grains 'host' is empty - check `salt-call grains.get host`")

    # yapf: disable
    cmd_args = [
        "-e", f"CONTAINER_IMAGE={container_image}",
        "-e", f"NODE_NAME={node_name}",
        "-v", f"{CEPH_ETC_DIR}:{CEPH_ETC_DIR}",
        "-v", f"{CEPH_BASE_DIR}:{CEPH_BASE_DIR}",
        "--entrypoint", f"{CEPH_MON}", f"{container_image}",
        "--mkfs",
        "-i", node_name,
        "--keyring", f"{CEPH_TMP_DIR}/keyring",
        "--monmap", f"{CEPH_TMP_DIR}/monmap",
    ]
    # yapf: enable

    # pylint: disable=broad-except
    try:
        os.makedirs(f"{CEPH_BASE_DIR}/mon/ceph-{node_name}", exist_ok=True)
        os.makedirs(f"{CEPH_LOG_DIR}", exist_ok=True)
        _chown_ceph(f"{CEPH_BASE_DIR}/mon/ceph-{node_name}")
        _chown_ceph(f"{CEPH_LOG_DIR}")

        output = kwargs.get('out', None)
        if 'output' in __opts__:
            output = "raw"  # prevent double processing
        ret = __salt__['podman-ng.run'](kwargs['__pub_fun'], cmd_args)
        return __utils__['ret.outputter'](ret, out_type=output)
    except Exception as exc:
        log.error(exc)
        return {
            'name': kwargs['__pub_fun'],
            'result': False,
            'comment': exc.args[0]
        }


# The cmd is an example of why the simplest approach is also the easiest to
# maintain.  Using a Salt template for the monitor service file requires the
# entire podman command as a string.  While the command is large, it's easy
# to understand without compartmentalizing each option or argument.

PODMAN_BIN = salt.utils.path.which('podman')


def cmd():
    '''
    Container command for systemd service file
    '''
    container_image = __pillar__.get('container_image', None)
    node_name = __grains__.get('host', None)

    ret = __utils__['ret.returnstruct']('mon.cmd')
    if not container_image:
        return __utils__['ret.err'](
            ret,
            "Container image not set - check `salt-call pillar.get container_image`"
        )
    if not node_name:
        return __utils__['ret.err'](
            ret, "Grains 'host' is empty - check `salt-call grains.get host`")

    # yapf: disable
    podman_cmd = [
        PODMAN_BIN, 'run', '--rm', '--net=host',
        "-e", f"CONTAINER_IMAGE={container_image}",
        "-e", f"NODE_NAME={node_name}",
        "-v", f"{CEPH_BASE_DIR}:{CEPH_BASE_DIR}:z",
        "-v", f"{CEPH_RUN_DIR}:{CEPH_RUN_DIR}:z",
        "-v", f"{CEPH_ETC_DIR}:{CEPH_ETC_DIR}",
        "-v", f"/etc/localtime:/etc/localtime:ro",
        "-v", f"{CEPH_LOG_DIR}:{CEPH_LOG_DIR}",
        "--entrypoint", f"{CEPH_MON}", f"{container_image}",
        "-i", node_name,
        "-f", #  foreground
        "-d"  #  log to stderr
    ]
    # yapf: enable

    return ' '.join([x.strip() for x in podman_cmd])
