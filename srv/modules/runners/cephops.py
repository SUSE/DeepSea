# -*- coding: utf-8 -*-
import logging
from subprocess import Popen, PIPE

log = logging.getLogger(__name__)


def set_noout():
    cmd = ["ceph osd set noout"]
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    for line in stdout:
        log.info(line)
    for line in stderr:
        log.info(line)
    log.info("returncode: {}".format(proc.returncode))
