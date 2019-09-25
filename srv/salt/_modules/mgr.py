# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
import salt.utils
# pylint: disable=import-error,3rd-party-module-not-gated
from subprocess import check_output, CalledProcessError
log = logging.getLogger(__name__)


def already_running():

    # TODO:
    # This code is almost identical with mon.already_running.
    # refactor and share it!

    # check if a container is already running.
    # Check the higher-level instance - systemd.

    # there needs to be a second check for existence..
    # we might have the case where a mon is down, but still exists
    # check for directory existence? or for podman image existance?

    # TODO: refine the logic when to return false/true..

    # is /host/ fine?
    mgr_name = __grains__.get('host', '')
    if not mgr_name:
        log.error("Could not retrieve host grain. Aborting")
        return False
    try:
        status = check_output(
            ['systemctl', 'is-active',
             f'ceph-mgr@{mgr_name}.service']).decode('utf-8').strip()
    except CalledProcessError as e:
        log.info(f'{e}')
        return False
    if status == 'active':
        return True
    elif status == 'inactive' or os.path.exists(
            f'/var/lib/ceph/mgr/ceph-{mgr_name}'):
        return False
    else:
        log.error(f"Could not determine state of {mgr_name}")
        return False


CEPH_ETC_DIR = "/etc/ceph"
CEPH_BASE_DIR = "/var/lib/ceph"
CEPH_TMP_DIR = "/var/lib/ceph/tmp"
CEPH_LOG_DIR = "/var/log/ceph"
CEPH_RUN_DIR = "/var/run/ceph"
CEPH_MGR = "/usr/bin/ceph-mgr"

PODMAN_BIN = salt.utils.path.which('podman')


def cmd():
    '''
    Container command for systemd service file
    '''
    container_image = __pillar__.get('container_image', None)
    node_name = __grains__.get('host', None)

    ret = __utils__['ret.returnstruct']('mgr.cmd')
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
        "--entrypoint", f"{CEPH_MGR}", f"{container_image}",
        "-i", node_name,
        "-f", #  foreground
        "-d"  #  log to stderr
    ]
    # yapf: enable

    return ' '.join([x.strip() for x in podman_cmd])
