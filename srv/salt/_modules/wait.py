#!/usr/bin/python

import rados
import json
import time
import logging
import pprint

log = logging.getLogger(__name__)


class HealthCheck(object):
    """
    Check the Ceph health status.  Wait to return until the number of
    successive checks matches the desired state.
    """

    def __init__(self, **kwargs):
        """
        Default settings can be overridden
        """
        if 'status' not in kwargs:
            msg = "status argument required\nExample: status=HEALTH_OK"
            raise ValueError(msg)

        self.settings = {
            'conf' : "/etc/ceph/ceph.conf",
            'timeout': 300,
            'check': 2,
            'delay': 6,
            'negate': False
        }
        self.settings.update(kwargs)
        log.debug("settings: {}".format(_skip_dunder(self.settings)))
        self._connect()

    def _connect(self):
        """
        Connect to Ceph cluster
        """
        self.cluster=rados.Rados(conffile=self.settings['conf'])
        self.cluster.connect()

    def wait(self):
        """
        Poll until the status "matches" the specificed number of checks.
        """
        cmd = json.dumps({"prefix":"health", "format":"json" })
        i=0
        check = 0

        while i < (self.settings['timeout']/self.settings['delay']):
            ret,output,err = self.cluster.mon_command(cmd, b'', timeout=6)
            current_status = json.loads(output)['overall_status']
            log.debug("status: {}".format(current_status))

            if self._check_status(current_status, self.settings):
                check += 1
                if check == self.settings['check']:
                    log.debug("{} checks succeeded".format(self.settings['check']))
                    return True
            else:
                # Reset check counter
                check = 0
            i += 1
            time.sleep(self.settings['delay'])

        # Bail out
        log.debug("Timeout expired")
        raise RuntimeError("Timeout expired")

    def _check_status(self, current, settings):
        """
        Return the "correct" matching status
        """
        if settings['negate']:
            log.debug("status != {}".format(settings['status']))
            return (current != settings['status'])
        else:
            log.debug("status == {}".format(settings['status']))
            return (current == settings['status'])

def until(**kwargs):
    """
    Wait around until the status matches.
    """
    hc = HealthCheck(**kwargs)
    hc.wait()


def out(**kwargs):
    """
    Negate the check.  That is, wait out the status such as HEALTH_ERR.
    """
    kwargs.update({ 'negate': True })
    hc = HealthCheck(**kwargs)
    hc.wait()


def _skip_dunder(settings):
    """
    Skip double underscore keys
    """
    return {k:v for k,v in settings.iteritems() if not k.startswith('__')}

