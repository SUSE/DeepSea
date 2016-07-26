#!/usr/bin/python

import time
import logging

import salt.loader
import salt.utils.event
from salt.utils.event import tagify
from salt.exceptions import SaltInvocationError

log = logging.getLogger(__name__)


"""
The queue runner in salt does not provide a way to check for an empty queue
and then fire an event.  

The requirement for this is connecting the completion of the prep stage0 where
minions are updating/rebooting independently and the remaining stages.
"""
    

def queue(**kwargs):
    """
    Fire an event if a queue is empty
    """

    # The same event drives the deletion and this check.  Give sqlite two
    # seconds to complete its update
    time.sleep(2)

    # defaults
    settings = { 
                 'backend': 'sqlite',
                 'queue': 'prep',
                 'next': 'discovery'
    }
    settings.update(kwargs)

    queue_funcs = salt.loader.queues(__opts__)
    cmd = '{0}.list_length'.format(settings['backend'])
    if cmd not in queue_funcs:
        raise SaltInvocationError('Function "{0}" is not available'.format(cmd))
    ret = queue_funcs[cmd](queue=settings['queue'])

    if (ret == 0): 
        event = salt.utils.event.get_event(
                'master',
                __opts__['sock_dir'],
                __opts__['transport'],
                opts=__opts__,
                listen=False)

        # skip dunder keys
        settings = {k:v for k,v in settings.iteritems() if not k.startswith('__')}
        event.fire_event(settings, tagify(['start', settings['next'], 'stage'], prefix='ceph'))
        log.info("firing event for stage {}".format(settings['next']))
    else:
        log.info("size of queue {} is {}".format(settings['queue'], ret))
    
    


    return ret






