#!/usr/bin/python

import salt.key
import salt.client
import salt.utils
import salt.utils.master
from salt.exceptions import SaltClientError
import time
import logging

log = logging.getLogger(__name__)

def ready(**kwargs):
    """
    Wait for minions to respond.  Compare test.ping results to either
    the list of all accepted keys or search criteria of cached pillar
    data.
    """
    settings = { 
                 'timeout': None,
                 'search': None,
                 'sleep': 6
               }
    settings.update(kwargs)

    ret = {}
    #client = salt.client.get_local_client(__opts__['conf_file'])

    end_time = None
    if settings['timeout']:
        end_time = time.time() + settings['timeout']
        log.debug("end time: {}".format(end_time))

    client = salt.client.LocalClient()

    while True:
        try:
            if settings['search']:
                results = client.cmd(settings['search'], 'test.ping', timeout=__opts__['timeout'], expr_form="compound")
            else:
                results = client.cmd('*', 'test.ping', timeout=__opts__['timeout'])
        except SaltClientError as client_error:
            print(client_error)
            return ret

        actual = set(results.keys())

        if settings['search']:
            pillar_util = salt.utils.master.MasterPillarUtil(settings['search'], "compound",
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
                return False
        time.sleep(settings['sleep'])

    return True

