# -*- coding: utf-8 -*-
"""
DeepSea stage's progress monitor
"""
from __future__ import absolute_import
from __future__ import print_function

from .saltevent import SaltEventProcessor, EventListener


class Monitor(object):
    """
    Stage monitoring class
    """

    class DeepSeaEventListener(EventListener):
        """
        Salt event listener for DeepSea
        """
        def __init__(self, monitor):
            self.monitor = monitor

        def handle_new_runner_event(self, event):
            if event.fun == 'runner.state.orch':
                if event.args and event.args[0].startswith('ceph.stage.'):
                    print("Starting stage -> {}".format(event.args[0]))

        def handle_ret_runner_event(self, event):
            if event.fun == 'runner.state.orch':
                if event.args and event.args[0].startswith('ceph.stage.'):
                    print("Ended stage -> {}".format(event.args[0]))

    def __init__(self):
        self.processor = SaltEventProcessor()
        self.processor.add_listener(Monitor.DeepSeaEventListener(self))

    def start(self):
        """
        Start the monitoring thread
        """
        self.processor.start()

    def stop(self):
        """
        Stop the monitoring thread
        """
        self.processor.stop()
