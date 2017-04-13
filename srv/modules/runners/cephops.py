# -*- coding: utf-8 -*-
import logging
from subprocess import Popen, PIPE

log = logging.getLogger(__name__)


def set_noout():
    __jid_event__.fire_event({'message': 'Setting noout'}, 'salt/ceph/set/noout')
