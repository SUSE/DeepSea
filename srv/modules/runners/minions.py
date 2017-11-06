# -*- coding: utf-8 -*-
# pylint: disable=modernize-parse-error
"""
Small collection of functions intended for all minions.
"""

import time
import logging
import salt.key
import salt.client
import salt.utils
import salt.utils.master
from salt.exceptions import SaltClientError

log = logging.getLogger(__name__)


def help_():
    """
    Usage
    """
    usage = ('salt-run minions.ready:\n'
             'salt-run minions.ready search=target:\n\n'
             '    Check that all minions are responding\n'
             '\n\n'
             'salt-run minions.message content=message:\n\n'
             '    Logs a warning message\n'
             '\n\n')
    print usage
    return ""


def ready(**kwargs):
    """
    Wait for minions to respond.  Compare test.ping results to either
    the list of all accepted keys or search criteria of cached pillar
    data.
    """
    settings = {
                 'timeout': None,
                 'search': None,
                 'sleep': 6,
                 'exception': False
               }
    settings.update(kwargs)

    ret = {}

    end_time = None
    if settings['timeout']:
        end_time = time.time() + settings['timeout']
        log.debug("end time: {}".format(end_time))

    client = salt.client.LocalClient()

    while True:
        try:
            if settings['search']:
                results = client.cmd(settings['search'], 'test.ping',
                                     timeout=__opts__['timeout'],
                                     expr_form="compound")
            else:
                results = client.cmd('*', 'test.ping', timeout=__opts__['timeout'])
        except SaltClientError as client_error:
            print client_error
            return ret

        actual = set(results.keys())

        if settings['search']:
            pillar_util = salt.utils.master.MasterPillarUtil(
                                                     settings['search'], "compound",
                                                     use_cached_grains=True,
                                                     grains_fallback=False,
                                                     opts=__opts__)

            cached = pillar_util.get_minion_pillar()
            expected = set(cached.keys())
        else:
            key = salt.key.Key(__opts__)
            expected = set(key.list_keys()['minions'])

        if actual == expected:
            log.warn("All minions are ready")
            break
        log.warn("Waiting on {}".format(",".join(list(expected - actual))))
        if end_time:
            if end_time < time.time():
                log.warn("Timeout reached")
                if settings['exception']:
                    msg = ("Timeout reached. "
                           "{} seems to be down.").format(",".join(list(expected - actual)))
                    raise RuntimeError(msg)
                return False
        time.sleep(settings['sleep'])

    return True


def message(**kwargs):
    """
    Pass along a message
    """
    log.warn("{}".format(kwargs['content']))
    return ""

__func_alias__ = {
                 'help_': 'help',
                 }
