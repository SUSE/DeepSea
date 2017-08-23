# -*- coding: utf-8 -*-
"""
DeepSea stage's progress monitor
"""
from __future__ import absolute_import
from __future__ import print_function

import collections
import logging

from .common import PrettyPrinter as PP
from .saltevent import SaltEventProcessor
from .saltevent import EventListener
from .saltevent import NewJobEvent, NewRunnerEvent, RetJobEvent, RetRunnerEvent
from .stage_parser import SLSParser


# pylint: disable=C0103
logger = logging.getLogger(__name__)


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

        def handle_salt_event(self, event):
            PP.p_header(event)

        def handle_new_runner_event(self, event):
            if 'pillar' not in event.fun:
                logger.debug("handle: %s", event)
            if event.fun == 'runner.state.orch':
                if event.args and event.args[0].startswith('ceph.stage.'):
                    self.monitor.start_stage(event)
            else:
                self.monitor.start_step(event)

        def handle_ret_runner_event(self, event):
            if 'pillar' not in event.fun:
                logger.debug("handle: %s", event)
            if event.fun == 'runner.state.orch':
                if event.args and event.args[0].startswith('ceph.stage.'):
                    self.monitor.end_stage(event)
            else:
                self.monitor.end_step(event)

        def handle_new_job_event(self, event):
            if 'pillar' not in event.fun:
                logger.debug("handle: %s", event)
            self.monitor.start_step(event)

        def handle_ret_job_event(self, event):
            if 'pillar' not in event.fun:
                logger.debug("handle: %s", event)
            self.monitor.end_step(event)

    def __init__(self):
        self._processor = SaltEventProcessor()
        self._processor.add_listener(Monitor.DeepSeaEventListener(self))

        self._running_stage = None
        self._steps_completed = 0
        self.stage_map = {}

    def start_stage(self, event):
        """
        Sets the current running stage
        Args:
            event (NewRunnerEvent): the DeepSea state.orch start event
        """
        self._running_stage = Stage(event.args[0], event.jid)
        logger.info("Start stage: %s jid=%s", self._running_stage.name, self._running_stage.jid)

        # PP.pl_bold("Start stage -> {}".format(self._running_stage.name))

    def end_stage(self, event):
        """
        Sets the current running stage as finished
        Args:
            event (RetRunnerEvent): the DeepSea state.orch end event
        """
        self._running_stage.finish()
        logger.info("End stage: %s jid=%s success=%s", self._running_stage.name,
                    self._running_stage.jid, event.success)
        # print("Finish stage -> {} -> {}".format(self._running_stage.name, event.success))
        self._running_stage = None

    def start_step(self, event):
        """
        Adds a new step to the execution tracking
        Args:
            event (NewJobEvent | NewRunnerEvent): the salt start event
        """
        if not self._running_stage:
            # not inside a running stage, igore step
            return
        step = None
        if isinstance(event, NewJobEvent):
            if event.fun == 'state.sls':
                step = StateStep(event.args[0], event.jid, event.minions)
                logger.info("Starting state step: %s jid=%s targets=%s", step.name, step.jid,
                            step.targets)
            else:
                # print("Running {} -> ".format(event.fun, event.args))
                # ignore jobs that are not state.sls for now
                return
        elif isinstance(event, NewRunnerEvent):
            step = RunnerStep(event.fun, event.jid)
            logger.info("Starting runner step: %s jid=%s", step.name, step.jid)
        else:
            assert False
        # print("Running {}".format(step))
        self._running_stage.add_step(step)

    def end_step(self, event):
        """
        Marks a step as finished from the execution tracking
        Args:
            event (RetJobEvent | RetRunnerEvent): the salt end event
        """
        if not self._running_stage:
            # not inside a running stage, igore step
            return

    def start(self):
        """
        Start the monitoring thread
        """
        self.stage_map['ceph.stage.1'] = {
            'steps': SLSParser.parse_state_steps('ceph.stage.1'),
            'done': 0
        }
        self._processor.start()

    def stop(self):
        """
        Stop the monitoring thread
        """
        logger.info("Stopping the DeepSea event monitoring")
        self._processor.stop()

    def wait_to_finish(self):
        """
        Blocks until the Salt event processor thread finishes
        """
        self._processor.join()

    def is_running(self):
        """
        Checks wheather the Salt event process is still runnning
        """
        return self._processor.is_running()
