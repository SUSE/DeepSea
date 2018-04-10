# -*- coding: utf-8 -*-

"""
Heath related checks for Ceph
"""

from __future__ import absolute_import
import json
import time
import logging
# pylint: disable=import-error,3rd-party-module-not-gated
import salt.ext.six as six
import rados
# pylint: disable=incompatible-py3-code
log = logging.getLogger(__name__)


class HealthCheck(object):

    def __init__(self, **kwargs):
        """
        Default settings can be overridden
        """
        if 'nohealthcheck' not in kwargs and 'status' not in kwargs:
            msg = "status argument required\nExample: status=HEALTH_OK"
            raise ValueError(msg)

        self.settings = {
            'conf': "/etc/ceph/ceph.conf",
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
        self.cluster = rados.Rados(conffile=self.settings['conf'])
        self.cluster.connect()

    def _wait(self, cmd, success):
        """
        Poll until the status "matches" the specificed number of checks.
        """
        i = 0
        check = 0

        log.debug('wait on condition of command {}'.format(cmd))
        while i < (self.settings['timeout']/self.settings['delay']):
            ret,output,err = self.cluster.mon_command(cmd, b'', timeout=6)
            json_output = json.loads(output)

            if success(json_output):
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

    def _check_status(self, current):
        """
        Return the "correct" matching status
        """
        if self.settings['negate']:
            log.debug("status != {}".format(self.settings['status']))
            return (current != self.settings['status'])
        else:
            log.debug("status == {}".format(self.settings['status']))
            return (current == self.settings['status'])


class FsStatusCheck(HealthCheck):
    """
    Check the fsmap status of the cep status output. Wait till all active MDS's
    daemons have reached up:active status
    """

    def __init__(self, **kwargs):
        super(FsStatusCheck, self).__init__(**kwargs)

    def wait_for_healthy_mds(self):
        """
        Poll until all active MDS' are up:active
        """
        cmd = json.dumps({"prefix":"status", "format":"json" })

        def success(status):
            if 'fsmap' in status:
                fsmap = status['fsmap']
            else:
                raise RuntimeError('No fsmap found in status output')

            for rank in fsmap['by_rank']:
                if not self._check_status(rank['status']):
                    return False
            return True

        self._wait(cmd, success)


class HealthStatusCheck(HealthCheck):
    """
    Check the Ceph health status.  Wait to return until the number of
    successive checks matches the desired state.
    """

    def __init__(self, **kwargs):
        super(HealthStatusCheck, self).__init__(**kwargs)

    def wait(self):
        """
        Poll until the status "matches" the specificed number of checks.
        """
        cmd = json.dumps({"prefix":"health", "format":"json" })

        def success(health):
            if 'overall_status' in health:
                current_status = health['overall_status']
            if 'status' in health:
                current_status = health['status']
            if current_status:
                log.debug("status: {}".format(current_status))
            else:
                raise RuntimeError("Neither status nor overall_status defined in health check")

            return self._check_status(current_status)


        self._wait(cmd, success)

    def just(self):
        """
        Sleep a set amount
        """
        time.sleep(self.settings['delay'])


def just(**kwargs):
    """
    Wait for the delay
    """
    healthcheck = HealthStatusCheck(**kwargs)
    healthcheck.just()


def until(**kwargs):
    """
    Wait around until the status matches.
    """
    healthcheck = HealthStatusCheck(**kwargs)
    healthcheck.wait()


def until_mds(**kwargs):
    """
    Wait around for fsmap changes.
    """
    fscheck = FsStatusCheck(**kwargs)
    fscheck.wait_for_healthy_mds()


def out(**kwargs):
    """
    Negate the check.  That is, wait out the status such as HEALTH_ERR.
    """
    kwargs.update({'negate': True})
    healthcheck = HealthStatusCheck(**kwargs)
    healthcheck.wait()


def _skip_dunder(settings):
    """
    Skip double underscore keys
    """
    return {k: v for k, v in six.iteritems(settings) if not k.startswith('__')}
