# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error

"""
"""

from __future__ import absolute_import
from __future__ import print_function
import sys
from subprocess import Popen, PIPE
import time
import logging
import os
import pprint
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin
from salt.ext.six.moves import range

# If we had python3-systemd available on SLE15SP1, then this is what I am
# wanting.  Each entry gets logged with a timestamp as info, so debug can
# stay debug.  This also works `journalctl -t deepsea -f`.
#
#from systemd.journal import JournalHandler
#
#log = logging.getLogger(__name__)
#journal_handler = JournalHandler(SYSLOG_IDENTIFIER="deepsea")
#journal_handler.setFormatter(logging.Formatter(
#    '[%(levelname)s] %(message)s'
#))
#log.addHandler(journal_handler)
#log.setLevel(logging.INFO)


log = logging.getLogger(__name__)


CEPH_TMP_DIR = "/var/lib/ceph/tmp"
MONMAPTOOL = "/usr/bin/monmaptool"


def _podman(name, authtool_args, **kwargs):
    '''
    Call podman with arguments and return desired output.  Gracefully, handle
    exceptions.
    '''
    container_image = __pillar__.get('container_image', None)
    node_name = __grains__.get('host', None)

    if not container_image:
        return __utils__['ret.err']("Container image not set - check `salt-call pillar.get container_image`")
    if not node_name:
        return __utils__['ret.err']("Grains 'host' is empty - check `salt-call grains.get host`")

    common_args = [
           "-e", f"CONTAINER_IMAGE={container_image}",
           "-e", f"NODE_NAME={node_name}",
           "-v", f"{CEPH_TMP_DIR}:{CEPH_TMP_DIR}",
           "--entrypoint", f"{MONMAPTOOL}", f"{container_image}"]

    cmd_args = common_args + authtool_args
    try:
        output = kwargs.get('out', None)
        if 'output' in __opts__:
            output = "raw" # prevent double processing
        ret = __salt__['podman-ng.run'](name, cmd_args)
        return __utils__['ret.outputter'](ret, out_type=output)
    except Exception as exc:
        log.error(exc)
        return {'name': name,
                'result': False,
                'comment': exc.args[0]}


def create(**kwargs):
    '''
    '''
    node_name = __grains__.get('host', None)
    monmaptool_args = [
           "--create",
           "--add", node_name, __salt__['public.address'](),
           "--fsid", __pillar__.get('fsid', None), f"{CEPH_TMP_DIR}/monmap",
           "--clobber"]

    ret = _podman(kwargs['__pub_fun'], monmaptool_args, **kwargs)
    return ret
