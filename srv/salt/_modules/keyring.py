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


def _podman(name, authtool_args, **kwargs):
    '''
    Call podman with arguments and return desired output.  Gracefully, handle
    exceptions.
    '''
    container_image = __pillar__.get('container_image', None)
    node_name = __grains__.get('host', None)

    ret = __utils__['ret.returnstruct'](name)
    if not container_image:
        return __utils__['ret.err'](
            ret,
            "Container image not set - check `salt-call pillar.get container_image`"
        )
    if not node_name:
        return __utils__['ret.err'](
            ret, "Grains 'host' is empty - check `salt-call grains.get host`")

    # yapf: disable
    common_args = [
        "-e", f"CONTAINER_IMAGE={container_image}",
        "-e", f"NODE_NAME={node_name}",
        "-v", f"{BOOTSTRAP_DIR}:{BOOTSTRAP_DIR}",
        "--entrypoint", f"{CEPH_AUTHTOOL}", f"{container_image}"
    ]
    # yapf: enable

    cmd_args = common_args + authtool_args
    # pylint: disable=broad-except
    try:
        output = kwargs.get('out', None)
        if 'output' in __opts__:
            output = "raw"  # prevent double processing
        ret = __salt__['podman-ng.run'](name, cmd_args)
        return __utils__['ret.outputter'](ret, out_type=output)
    except Exception as exc:
        log.error(exc)
        return {'name': name, 'result': False, 'comment': exc.args[0]}


def mon(**kwargs):
    '''
    Provide podman arguments for generating the initial mon keyring
    '''
    keyring = f"{BOOTSTRAP_DIR}/files/keyring"
    # yapf: disable
    authtool_args = [
        "--create-keyring", keyring,
        "--gen-key",
        "-n", "mon.",
        "--cap", "mon", "allow *"
    ]
    # yapf: enable

    ret = _podman(kwargs['__pub_fun'], authtool_args, **kwargs)
    _chown_salt(keyring)
    return ret


def _chown_salt(keyring):
    '''
    Set the salt user
    '''
    try:
        os.chown(keyring, 480, -1)  # salt user
    except FileNotFoundError:
        pass


def admin(**kwargs):
    '''
    Provide podman arguments for generating the admin keyring
    '''
    keyring = f"{BOOTSTRAP_DIR}/files/ceph.client.admin.keyring"
    # yapf: disable
    authtool_args = [
        "--create-keyring", keyring,
        "--gen-key",
        "-n", "client.admin",
        "--cap", "mon", "allow *",
        "--cap", "osd", "allow *",
        "--cap", "mds", "allow *",
        "--cap", "mgr", "allow *"
    ]
    # yapf: enable

    ret = _podman(kwargs['__pub_fun'], authtool_args, **kwargs)
    _chown_salt(keyring)
    return ret


def import_admin(**kwargs):
    '''
    Adds the admin keyring to keyring
    (i.e. cat ceph.client.admin.keyring >> keyring)
    '''
    # yapf: disable
    authtool_args = [
        f"{BOOTSTRAP_DIR}/files/keyring",
        "--import-keyring", f"{BOOTSTRAP_DIR}/files/ceph.client.admin.keyring"
    ]
    # yapf: enable

    return _podman(kwargs['__pub_fun'], authtool_args, **kwargs)


def bootstrap(**kwargs):
    '''
    Provide podman arguments for generating the osd bootstrap keyring
    '''
    keyring = f"{BOOTSTRAP_DIR}/files/ceph.keyring"
    # yapf: disable
    authtool_args = [
        "--create-keyring", keyring,
        "--gen-key",
        "-n", "client.bootstrap-osd",
        "--cap", "mon", "bootstrap-osd"
    ]
    # yapf: enable

    ret = _podman(kwargs['__pub_fun'], authtool_args, **kwargs)
    _chown_salt(keyring)
    return ret


def import_bootstrap(**kwargs):
    '''
    Adds the bootstrap keyring to keyring (i.e. cat ceph.keyring >> keyring)
    '''
    # yapf: disable
    authtool_args = [
        f"{BOOTSTRAP_DIR}/files/keyring",
        "--import-keyring", f"{BOOTSTRAP_DIR}/files/ceph.keyring"
    ]
    # yapf: enable

    return _podman(kwargs['__pub_fun'], authtool_args, **kwargs)


CEPH_BIN = "/usr/bin/ceph"
CEPH_ETC_DIR = "/etc/ceph"


def _podman2(name, authtool_args, **kwargs):
    '''
    Note the duplication from _podman above with the subtle differences.
    Those differences should be what is obvious
    '''
    container_image = __pillar__.get('container_image', None)
    node_name = __grains__.get('host', None)

    ret = __utils__['ret.returnstruct'](name)
    if not container_image:
        return __utils__['ret.err'](
            ret,
            "Container image not set - check `salt-call pillar.get container_image`"
        )
    if not node_name:
        return __utils__['ret.err'](
            ret, "Grains 'host' is empty - check `salt-call grains.get host`")

    # yapf: disable
    common_args = [
        "-e", f"CONTAINER_IMAGE={container_image}",
        "-e", f"NODE_NAME={node_name}",
        "-v", f"{BOOTSTRAP_DIR}:{BOOTSTRAP_DIR}",
        "-v", f"{CEPH_ETC_DIR}:{CEPH_ETC_DIR}",
        "--entrypoint", f"{CEPH_BIN}", f"{container_image}"
    ]
    # yapf: enable

    cmd_args = common_args + authtool_args
    try:
        output = kwargs.get('out', None)
        if 'output' in __opts__:
            output = "raw"  # prevent double processing
        ret = __salt__['podman-ng.run'](name, cmd_args)
        return __utils__['ret.outputter'](ret, out_type=output)
    except Exception as exc:
        log.error(exc)
        return {'name': name, 'result': False, 'comment': exc.args[0]}


def mgr(name, **kwargs):
    '''
    Provide podman arguments for generating a named mgr keyring
    '''
    keyring = f"{BOOTSTRAP_DIR}/files/mgr-{name}.keyring"
    # yapf: disable
    authtool_args = [
        "auth", "get-or-create", f"mgr.{name}",
        "mon", "'allow profile mgr'",
        "osd", "'allow *'",
        "mds", "'allow *'",
        "-o", keyring
    ]
    # yapf: enable

    ret = _podman2(kwargs['__pub_fun'], authtool_args, **kwargs)
    _chown_salt(keyring)
    return ret


def import_all(**kwargs):
    '''
    Do nearly identical steps need a wrapper?
    '''
    import_admin(**kwargs)
    import_bootstrap(**kwargs)


def setup(**kwargs):
    '''
    Simple wrapper for grouping all the functions of this module.
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
