import logging
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
