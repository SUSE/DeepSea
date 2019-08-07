# -*- coding: utf-8 -*-

"""
The need for this module is that the roles show the intended state and not
the current state.  Once the admin unassigns the monitor role, the pillar
reflects that configuration.
"""

from __future__ import absolute_import
import logging
# pylint: disable=import-error,3rd-party-module-not-gated
from subprocess import check_output, CalledProcessError
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
