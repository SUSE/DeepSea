# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
"""
An example of structured and human friendly returns.  Additionally, ideal
logging if we can get the packages in place.
"""

from __future__ import absolute_import
from __future__ import print_function
import logging
import os
import podman_ng
import rs

# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin

# If we had python3-systemd available on SLE15SP1, then this is what I am
# wanting.  Each entry gets logged with a timestamp as info, so debug can
# stay debug.  This also works `journalctl -t deepsea -f`.
#
# from systemd.journal import JournalHandler
#
# log = logging.getLogger(__name__)
# journal_handler = JournalHandler(SYSLOG_IDENTIFIER="deepsea")
# journal_handler.setFormatter(logging.Formatter(
#     '[%(levelname)s] %(message)s'
# ))
# log.addHandler(journal_handler)
# log.setLevel(logging.INFO)

log = logging.getLogger(__name__)

BOOTSTRAP_DIR = "/srv/salt/ceph/bootstrap"
CEPH_AUTHTOOL = "/usr/bin/ceph-authtool"


def _ceph_authtool(podman):
    ''' Common podman options for ceph_authtool '''

    podman.env(f"CONTAINER_IMAGE={podman.container_image}") \
          .env(f"NODE_NAME={podman.node_name}") \
          .vol(f"{BOOTSTRAP_DIR}:{BOOTSTRAP_DIR}") \
          .entrypoint([f"{CEPH_AUTHTOOL}", f"{podman.container_image}"])
    # Without chaining nor backslashes
    # podman.env(f"NODE_NAME={podman.node_name}")
    # podman.vol(f"{BOOTSTRAP_DIR}:{BOOTSTRAP_DIR}")
    # podman.entrypoint([f"{CEPH_AUTHTOOL}", f"{podman.container_image}"])
    return podman


def _podman(name, command, keyring):
    '''
    Podman returns usable return codes.  Augment the return structure and
    correct the ownership of the generated keyring
    '''
    ret = rs.returnstruct(name, command=command)
    ret.update(__salt__['cmd.run_all'](command))
    if ret['retcode'] == 0:
        ret['result'] = True
    _chown_salt(keyring)
    return ret


def mon(**kwargs):
    ''' Generates mon keyring '''

    keyring = f"{BOOTSTRAP_DIR}/files/keyring"
    try:
        podman = podman_ng.Podman(__pillar__)
        podman = _ceph_authtool(podman)
        # yapf: disable
        podman.args([
            "--create-keyring", keyring,
            "--gen-key",
            "-n", "mon.",
            "--cap", "mon", "'allow *'"
        ])
        # yapf: enable
        log.info(podman.command)

        ret = _podman(kwargs['__pub_fun'], podman.command, keyring)
        return rs.outputter(ret, out=kwargs.get('out', None), opts=__opts__)
    except Exception as exc:
        log.error(exc)
        return {
            'name': kwargs['__pub_fun'],
            'result': False,
            'comment': exc.args
        }


def _chown_salt(keyring):
    ''' Set the salt user '''
    try:
        os.chown(keyring, 480, -1)  # salt user
    except FileNotFoundError:
        pass


def admin(**kwargs):
    ''' Generates admin keyring '''

    keyring = f"{BOOTSTRAP_DIR}/files/ceph.client.admin.keyring"
    try:
        podman = podman_ng.Podman(__pillar__)
        podman = _ceph_authtool(podman)
        # yapf: disable
        podman.args([
            "--create-keyring", keyring,
            "--gen-key",
            "-n", "client.admin",
            "--cap", "mon", "'allow *'",
            "--cap", "osd", "'allow *'",
            "--cap", "mds", "'allow *'",
            "--cap", "mgr", "'allow *'"
        ])
        # yapf: enable
        log.info(podman.command)

        ret = _podman(kwargs['__pub_fun'], podman.command, keyring)
        return rs.outputter(ret, out=kwargs.get('out', None), opts=__opts__)
    except Exception as exc:
        log.error(exc)
        return {
            'name': kwargs['__pub_fun'],
            'result': False,
            'comment': exc.args
        }


def import_admin(**kwargs):
    '''
    Adds the admin keyring to keyring
    (i.e. cat ceph.client.admin.keyring >> keyring)
    '''
    keyring = f"{BOOTSTRAP_DIR}/files/ceph.client.admin.keyring"
    try:
        podman = podman_ng.Podman(__pillar__)
        podman = _ceph_authtool(podman)
        # yapf: disable
        podman.args([
            f"{BOOTSTRAP_DIR}/files/keyring",
            "--import-keyring", keyring
        ])
        # yapf: enable
        log.info(podman.command)

        ret = _podman(kwargs['__pub_fun'], podman.command, keyring)
        return rs.outputter(ret, out=kwargs.get('out', None), opts=__opts__)
    except Exception as exc:
        log.error(exc)
        return {
            'name': kwargs['__pub_fun'],
            'result': False,
            'comment': exc.args
        }


def bootstrap(**kwargs):
    ''' Generates osd bootstrap keyring '''

    keyring = f"{BOOTSTRAP_DIR}/files/ceph.keyring"
    try:
        podman = podman_ng.Podman(__pillar__)
        podman = _ceph_authtool(podman)
        # yapf: disable
        podman.args([
            "--create-keyring", keyring,
            "--gen-key",
            "-n", "client.bootstrap-osd",
            "--cap", "mon", "bootstrap-osd"
        ])
        # yapf: enable
        log.info(podman.command)

        ret = _podman(kwargs['__pub_fun'], podman.command, keyring)
        return rs.outputter(ret, out=kwargs.get('out', None), opts=__opts__)
    except Exception as exc:
        log.error(exc)
        return {
            'name': kwargs['__pub_fun'],
            'result': False,
            'comment': exc.args
        }


def import_bootstrap(**kwargs):
    '''
    Adds the bootstrap keyring to keyring (i.e. cat ceph.keyring >> keyring)
    '''
    keyring = f"{BOOTSTRAP_DIR}/files/ceph.keyring"
    try:
        podman = podman_ng.Podman(__pillar__)
        podman = _ceph_authtool(podman)
        # yapf: disable
        podman.args([
            f"{BOOTSTRAP_DIR}/files/keyring",
            "--import-keyring", keyring
        ])
        # yapf: enable
        log.info(podman.command)

        ret = _podman(kwargs['__pub_fun'], podman.command, keyring)
        return rs.outputter(ret, out=kwargs.get('out', None), opts=__opts__)
    except Exception as exc:
        log.error(exc)
        return {
            'name': kwargs['__pub_fun'],
            'result': False,
            'comment': exc.args
        }


CEPH_BIN = "/usr/bin/ceph"
CEPH_ETC_DIR = "/etc/ceph"


def _ceph_bin(podman):

    podman.env(f"CONTAINER_IMAGE={podman.container_image}") \
          .env(f"NODE_NAME={podman.node_name}") \
          .vol(f"{BOOTSTRAP_DIR}:{BOOTSTRAP_DIR}") \
          .vol(f"{CEPH_ETC_DIR}:{CEPH_ETC_DIR}") \
          .entrypoint([f"{CEPH_BIN}", f"{podman.container_image}"])
    # Without chaining nor backslashes
    # podman.env(f"NODE_NAME={podman.node_name}")
    # podman.vol(f"{BOOTSTRAP_DIR}:{BOOTSTRAP_DIR}")
    # podman.vol(f"{CEPH_ETC_DIR}:{CEPH_ETC_DIR}")
    # podman.entrypoint([f"{CEPH_BIN}", f"{podman.container_image}"])
    return podman


def mgr(name, **kwargs):
    ''' Generates mgr keyring '''
    keyring = f"{BOOTSTRAP_DIR}/files/mgr-{name}.keyring"

    try:
        podman = podman_ng.Podman(__pillar__)
        podman = _ceph_bin(podman)
        # yapf: disable
        podman.args([
            "auth", "get-or-create", f"mgr.{name}",
            "mon", "'allow profile mgr'",
            "osd", "'allow *'",
            "mds", "'allow *'",
            "-o", keyring
        ])
        # yapf: enable
        log.info(podman.command)

        ret = _podman(kwargs['__pub_fun'], podman.command, keyring)
        return rs.outputter(ret, out=kwargs.get('out', None), opts=__opts__)
    except Exception as exc:
        log.error(exc)
        return {
            'name': kwargs['__pub_fun'],
            'result': False,
            'comment': exc.args
        }


def setup(**kwargs):
    '''
    Simple wrapper for grouping the bootstrap related functions of this module.
    '''
    steps = {
        mon: 'mon',
        bootstrap: 'bootstrap',
        admin: 'admin',
        import_bootstrap: 'import_bootstrap',
        import_admin: 'import_admin'
    }

    for step in steps:
        ret = step(out='yaml', __pub_fun=f"keyring.{steps[step]}")
        if not ret['result']:
            return ret

    return {
        'name': kwargs['__pub_fun'],
        'result': True,
        'comment': "Creation and import of keyrings completed"
    }
