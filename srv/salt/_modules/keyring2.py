# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error

"""
An example of structured and human friendly returns.  Additionally, ideal
logging if we can get the packages in place.
"""

from __future__ import absolute_import
from __future__ import print_function
import sys
from subprocess import Popen, PIPE
import time
import logging
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


BOOTSTRAP_DIR = "/srv/salt/ceph/bootstrap"

class PodmanCmd(object):

    def __init__(self, name):
        self.name = name
        self.node_name = __grains__['host']
        self.container_image = __pillar__['ceph_image']
        self.cmd = ""

    def check(self):
        ''' Verify values are set '''
        if not self.node_name:
            return "Grains 'host' is empty - check `salt-call grains.get host`"
        if not self.container_image:
            return "Container image not set - check `salt-call pillar.get ceph_image`"
        return ""

    def podman_base(self):
        ''' returns podman prefix command '''
        return ["/usr/bin/podman",
               "run",
               "--rm",
               "--net=host",
               "-e", f"CONTAINER_IMAGE={self.container_image}",
               "-e", f"NODE_NAME={self.node_name}"]

    def bootstrap_cmd(self):
        ''' returns bootstrap keyring command '''
        return self.podman_base() + [
               "-v", f"{BOOTSTRAP_DIR}:{BOOTSTRAP_DIR}",
               "--entrypoint", "/usr/bin/ceph-authtool",
               f"{self.container_image}",
               "--create-keyring", f"{BOOTSTRAP_DIR}/keyring",
               "--gen-key",
               "-n", "mon.",
               "--cap", "mon", "allow *"]

    def admin_cmd(self):
        ''' returns admin keyring command '''
        return self.podman_base() + [
               "-v", f"{BOOTSTRAP_DIR}:{BOOTSTRAP_DIR}",
               "--entrypoint", "/usr/bin/ceph-authtool",
               f"{self.container_image}",
               "--create-keyring", f"{BOOTSTRAP_DIR}/ceph.client.admin.keyring",
               "--gen-key",
               "-n", "client.admin",
               "--cap", "mon", "allow *",
               "--cap", "osd", "allow *",
               "--cap", "mds", "allow *",
               "--cap", "mgr", "allow *"]

    def bad_cmd(self):
        ''' returns a command with an error '''
        return ["/usr/bin/podman",
               "xyz"]

    def run(self):
        ''' Executes a command '''
        ret = { 'name': self.name,
                'changes': {},
                'result': False,
                'rc': '',
                'comment': '' }

        err = self.check()
        if err:
            ret['comment'] = err
            log.error(err)
            return ret

        log.info(self.cmd)
        proc = Popen(self.cmd, stdout=PIPE, stderr=PIPE)
        proc.wait()
        out = [line.decode() for line in proc.stdout]
        log.info(f"stdout: {' '.join(out)}")
        err = [line.decode() for line in proc.stderr]
        log.info(f"stderr: {' '.join(err)}")

        ret['rc'] = proc.returncode
        if proc.returncode == 0:
            ret['result'] = True
            ret['changes'] = {'out': " ".join(out)}
            ret['comment'] = " ".join(err)
        else:
            ret['comment'] = " ".join(out) + " ".join(err)
            log.error(f"rc: {ret['rc']} -- {ret['comment']}")

        log.debug(f"ret: {ret}")
        return ret


def _friendly(ret):
    ''' Returns human readable output or error '''
    if ret['result']:
        return ret['changes']['out']
    else:
        if ret['rc']:
            return f"podman exit code: {ret['rc']}\n{ret['comment']}"
        return ret['comment']


def bootstrap():
    ''' human interface '''
    return _friendly(bootstraprc())


def bootstraprc():
    ''' runner api  '''
    podman = PodmanCmd('keyring2.bootstraprc')
    podman.cmd = podman.bootstrap_cmd()
    return podman.run()


def admin():
    ''' human interface '''
    return _friendly(adminrc())


def adminrc():
    ''' runner api  '''
    podman = PodmanCmd('keyring2.adminrc')
    podman.cmd = podman.admin_cmd()
    return podman.run()


def bad():
    ''' human interface '''
    return _friendly(badrc())


def  badrc():
    ''' runner api '''
    podman = PodmanCmd('keyring2.badrc')
    podman.cmd = podman.bad_cmd()
    return podman.run()



