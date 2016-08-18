#!/usr/bin/python

import salt.key
import salt.client
import time
import logging

log = logging.getLogger(__name__)

def ready():
    """
    Wait for all minions to respond
    """
    ret = {}
    client = salt.client.get_local_client(__opts__['conf_file'])

    while True:
        try:
            results = client.cmd('*', 'test.ping', timeout=__opts__['timeout'])
        except SaltClientError as client_error:
            print(client_error)
            return ret

        minions = set(results.keys())
        key = salt.key.Key(__opts__)
        salt_keys = set(key.list_keys()['minions'])
        if minions == salt_keys:
            log.warn("All minions are ready")
            break
        log.warn("Waiting on {}".format(",".join(list(salt_keys - minions))))
        time.sleep(6)

    return True

