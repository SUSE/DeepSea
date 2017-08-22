# -*- coding: utf-8 -*-
"""
DeepSea stage's progress monitor
"""
from __future__ import absolute_import
from __future__ import print_function

import collections
import logging

from .common import print_progress, PrettyPrinter as PP
from .saltevent import SaltEventProcessor
from .saltevent import EventListener
from .saltevent import NewJobEvent, NewRunnerEvent, RetJobEvent, RetRunnerEvent
from .stage_parser import SLSParser


# pylint: disable=C0103
logger = logging.getLogger(__name__)


class Stage(object):
    """
    Class to represent a DeepSea stage execution
    """
    def __init__(self, name, jid):
        self.name = name
        self.jid = jid
        self.running = True
        self.steps = collections.OrderedDict()

    def finish(self):
        """
        Sets this stage has finished
        """
        self.running = False

    def add_step(self, step):
        """
        Add a new step to the list of execution steps
        """
        self.steps[step.jid] = step


class StageStep(object):
    """
    Base class to represent Salt state, module and runner executions within DeepSea stages
    """
    def __init__(self, name, jid):
        self.name = name
        self.jid = jid

    def __str__(self):
        return self.name


class StateStep(StageStep):
    """
    Class to represent Salt state execution within DeepSea stages
    """
    def __init__(self, name, jid, targets):
        super(StateStep, self).__init__(name, jid)
        self.targets = targets

    def __str__(self):
        parent_str = super(StateStep, self).__str__()
        return "State(name: {}, targets: {})".format(parent_str, self.targets)


class RunnerStep(StageStep):
    """
    Class to represent Salt runner execution within DeepSea stages
    """
    def __init__(self, name, jid):
        super(RunnerStep, self).__init__(name, jid)

    def __str__(self):
        parent_str = super(RunnerStep, self).__str__()
        return "Runner(name: {})".format(parent_str)


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

        print("Start stage -> {}".format(self._running_stage.name))

    def end_stage(self, event):
        """
        Sets the current running stage as finished
        Args:
            event (RetRunnerEvent): the DeepSea state.orch end event
        """
        self._running_stage.finish()
        logger.info("End stage: %s jid=%s success=%s", self._running_stage.name,
                    self._running_stage.jid, event.success)
        print("Finish stage -> {} -> {}".format(self._running_stage.name, event.success))
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
        print("Running {}".format(step))
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
        logger.info("Initializing the DeepSea event monitoring")
        PP.p_bold("Initializing DeepSea progess monitor...")
        self.stage_map['ceph.stage.1'] = {
            'steps': SLSParser.parse_state_steps('ceph.stage.1'),
            'done': 0
        }
        PP.p_bold("Done.")
        self._processor.start()

    def stop(self):
        """
        Stop the monitoring thread
        """
        logger.info("Stopping the DeepSea event monitoring")
        self._processor.stop()
