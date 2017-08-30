# -*- coding: utf-8 -*-
"""
DeepSea stage's progress monitor
"""
from __future__ import absolute_import
from __future__ import print_function

import logging
import operator

from .saltevent import SaltEventProcessor
from .saltevent import EventListener
from .saltevent import NewJobEvent, NewRunnerEvent, RetJobEvent, RetRunnerEvent
from .stage_parser import SLSParser, SaltRunner, SaltState, SaltModule, SaltBuiltIn


# pylint: disable=C0111
# pylint: disable=C0103
logger = logging.getLogger(__name__)


class Stage(object):
    """
    Class that models the execution of a DeepSea stage
    """

    class Step(object):
        """
        Class that models the execution of a single step
        """
        def __init__(self, step, name, order):
            """
            Args:
                step (stage_parse.SaltStep): the parsed step
            """
            self.step = step
            self.name = name
            self.order = order
            self.jid = None
            self.finished = False
            self.success = None
            self.start_event = None
            self.end_event = None
            self.skipped = False

        def start(self, event):
            self.jid = event.jid
            self.start_event = event

        def finish(self, event):
            self.success = event.success
            self.finished = True
            self.end_event = event

    class TargetedStep(Step):
        def __init__(self, step, name, order):
            super(Stage.TargetedStep, self).__init__(step, name, order)
            self.targets = None
            self.sub_steps = []
            self.curr_sub_step = 0

        # pylint: disable=W0221
        def start(self, event):
            super(Stage.TargetedStep, self).start(event)
            self.targets = {}
            for target in event.targets:
                self.targets[target] = {
                    'finished': False,
                    'success': None
                }

        def finish(self, event):
            self.targets[event.minion] = {
                'finished': True,
                'success': event.success and event.retcode == 0,
                'event': event
            }
            if reduce(operator.__and__, [t['finished'] for t in self.targets.values()]):
                self.success = reduce(
                    operator.__and__, [t['success'] for t in self.targets.values()])
                self.finished = True

        def current_sub_step(self):
            return self.sub_steps[self.curr_sub_step]

        def finish_sub_step(self, result):
            self.sub_steps[self.curr_sub_step].start(self.jid)
            self.sub_steps[self.curr_sub_step].finish(result)
            self.curr_sub_step += 1

    def __init__(self, name, steps):
        self.name = name
        self._parsed_steps = steps
        self.jid = None
        self.success = None
        self._executing = False
        self.current_step = 0
        self.start_event = None
        self.end_event = None

        self._steps = []
        _curr_state = None
        for step in self._parsed_steps:
            wrapper = None
            if isinstance(step, SaltRunner):
                wrapper = Stage.Step(step, step.fun, len(self._steps)+1)
                _curr_state = None
            elif isinstance(step, SaltState):
                wrapper = Stage.TargetedStep(step, step.state, len(self._steps)+1)
                _curr_state = wrapper
            elif isinstance(step, SaltModule) or isinstance(step, SaltBuiltIn):
                assert _curr_state
                _curr_state.sub_steps.append(Stage.Step(step, step.fun,
                                                        len(_curr_state.sub_steps)+1))
                continue

            assert wrapper
            self._steps.append(wrapper)

    def total_steps(self):
        return len(self._steps)

    def start(self, event):
        """
        Flags this stage as executing, and stores its salt job id
        """
        self._executing = True
        self.jid = event.jid
        self.start_event = event
        self.current_step = 0

    def finish(self, event):
        """
        Flags this stage as finished, and stores the result
        """
        assert self._executing
        self._executing = False
        self.success = event.success
        self.end_event = event

    def start_step(self, event):
        assert self._executing

        if isinstance(event, NewRunnerEvent):
            curr_step = self._steps[self.current_step]
            if isinstance(curr_step.step, SaltRunner):
                if curr_step.name == event.fun[7:]:
                    curr_step.start(event)
                    return curr_step

        elif isinstance(event, NewJobEvent):
            curr_step = self._steps[self.current_step]
            if isinstance(curr_step, Stage.TargetedStep):
                step_name = event.args[0] if event.fun == 'state.sls' else event.fun
                if curr_step.name == step_name:
                    curr_step.start(event)
                    return curr_step

        else:
            assert False

        return None

    def finish_step(self, event):
        """
        Consumes the current step
        Args:
            event (saltevent.SaltEvent): the step object
        """
        assert self._executing

        if isinstance(event, RetRunnerEvent):
            curr_step = self._steps[self.current_step]
            if curr_step.jid and curr_step.jid == event.jid:
                curr_step.finish(event)
                self.current_step += 1
                return self._steps[self.current_step-1]

        elif isinstance(event, RetJobEvent):
            curr_step = self._steps[self.current_step]
            if curr_step.jid and curr_step.jid == event.jid:
                curr_step.finish(event)
                if curr_step.finished:
                    self.current_step += 1
                return curr_step

        else:
            assert False

        return None

    def state_result_step(self, event):
        """
        Consumes teh current step
        Args:
            event (saltevent.StateResultEvent): the state result event
        """
        assert self._executing

        curr_step = self._steps[self.current_step]
        assert not curr_step.finished

        if event.jid == curr_step.jid:
            # we still need to verify if state result matches current sub step
            # curr_step.finish_sub_step(event.result)
            pass

        return curr_step

    def check_if_current_step_will_run(self):
        assert self._executing

        curr_step = self._steps[self.current_step]
        for dep in curr_step.step.on_success_deps:
            for i in range(1, self.current_step+1):
                dep_step = self._steps[self.current_step-i]
                if dep_step.step.desc == dep.desc:
                    if not dep_step.success:
                        curr_step.skipped = True
                        self.current_step += 1
                        return curr_step
        for dep in curr_step.step.on_fail_deps:
            for i in range(1, self.current_step+1):
                dep_step = self._steps[self.current_step-i]
                if dep_step.step.desc == dep.desc:
                    if dep_step.success:
                        curr_step.skipped = True
                        self.current_step += 1
                        return curr_step

        return None


class MonitorListener(object):
    def stage_started(self, stage_name):
        """
        This function is called when a stage starts
        Args:
            stage (str): the stage name
        """
        pass

    def stage_parsing_started(self, stage_name):
        """
        This function is called when a stage parsing started
        Args:
            stage (str): the stage name
        """
        pass

    def stage_parsing_finished(self, stage):
        """
        This function is called when a stage parsing finished
        Args:
            stage (Stage): the stage object or None if a parsing error occurred
        """
        pass

    def stage_finished(self, stage):
        """
        This function is called when a stage finished execution
        Args:
            stage (Stage): the stage object
        """
        pass

    def step_runner_started(self, step):
        """
        This function is called when a runner starts executing
        Args:
            step (Stage.Step): the step object
        """
        pass

    def step_runner_finished(self, step):
        """
        This function is called when a runner finishes
        Args:
            step (Stage.Step): the step object
        """
        pass

    def step_state_started(self, step):
        """
        This function is called when a Salt state starts executing
        Args:
            step (Stage.Step): the step object
        """
        pass

    def step_state_minion_finished(self, step, minion):
        """
        This function is called when a Salt state finishes in a particular minion
        Args:
            step (Stage.Step): the step object
            minion (str): the minion id
        """
        pass

    def step_state_result(self, step):
        """
        This function is called when a Salt state result is received
        Args:
            step (Stage.Step): the step object
        """
        pass

    def step_state_finished(self, step):
        """
        This function is called when a Salt state finishes executing in all targets
        Args:
            step (Stage.Step): the step object
        """
        pass


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
            if 'pillar' in event.fun:
                return
            logger.debug("handle: %s", event)
            if event.fun == 'runner.state.orch':
                self.monitor.start_stage(event)
            else:
                self.monitor.start_step(event)

        def handle_ret_runner_event(self, event):
            if 'pillar' in event.fun:
                return
            logger.debug("handle: %s", event)
            if event.fun == 'runner.state.orch':
                self.monitor.end_stage(event)
            else:
                self.monitor.end_step(event)

        def handle_new_job_event(self, event):
            if 'pillar' in event.fun:
                return
            logger.debug("handle: %s", event)
            self.monitor.start_step(event)

        def handle_ret_job_event(self, event):
            if 'pillar' in event.fun:
                return
            logger.debug("handle: %s", event)
            self.monitor.end_step(event)

        def handle_state_result_event(self, event):
            logger.debug("handle: %s", event)
            self.monitor.state_result_step(event)

    def __init__(self):
        self._processor = SaltEventProcessor()
        self._processor.add_listener(Monitor.DeepSeaEventListener(self))

        self._running_stage = None
        self.monitor_listeners = []

    def add_listener(self, listener):
        """
        Register a monitor listener
        Args:
            listener (MonitorListener): the listener object
        """
        assert isinstance(listener, MonitorListener)
        self.monitor_listeners.append(listener)

    def _fire_event(self, event, *args):
        logger.debug("fire event: %s", event)
        for listener in self.monitor_listeners:
            getattr(listener, event)(*args)

    def start_stage(self, event):
        """
        Sets the current running stage
        Args:
            event (NewRunnerEvent): the DeepSea state.orch start event
        """
        stage_name = event.args[0]
        self._fire_event('stage_started', stage_name)
        self._fire_event('stage_parsing_started', stage_name)
        self._running_stage = Stage(stage_name, SLSParser.parse_state_steps(stage_name))
        self._fire_event('stage_parsing_finished', self._running_stage)
        self._running_stage.start(event)
        logger.info("Start stage: %s jid=%s", self._running_stage.name, self._running_stage.jid)

    def end_stage(self, event):
        """
        Sets the current running stage as finished
        Args:
            event (RetRunnerEvent): the DeepSea state.orch end event
        """
        if not self._running_stage:
            # not inside a running stage, igore step
            return

        self._running_stage.finish(event)
        tmp_stage = self._running_stage
        self._running_stage = None
        logger.info("End stage: %s jid=%s success=%s", tmp_stage, tmp_stage.jid, event.success)
        self._fire_event('stage_finished', tmp_stage)

    def start_step(self, event):
        """
        Adds a new step to the execution tracking
        Args:
            event (NewJobEvent | NewRunnerEvent): the salt start event
        """
        if not self._running_stage:
            # not inside a running stage, igore step
            return
        step = self._running_stage.start_step(event)
        logger.debug("started step: %s", step)
        if not step:
            return
        if isinstance(step, Stage.TargetedStep):
            self._fire_event('step_state_started', step)
        else:
            self._fire_event('step_runner_started', step)

    def end_step(self, event):
        """
        Marks a step as finished from the execution tracking
        Args:
            event (RetJobEvent | RetRunnerEvent): the salt end event
        """
        if not self._running_stage:
            # not inside a running stage, igore step
            return
        step = self._running_stage.finish_step(event)
        if not step:
            return
        if isinstance(step, Stage.TargetedStep):
            self._fire_event('step_state_minion_finished', step, event.minion)
            if step.finished:
                self._fire_event('step_state_finished', step)
        else:
            self._fire_event('step_runner_finished', step)

        skipped = self._running_stage.check_if_current_step_will_run()
        while skipped:
            if isinstance(skipped, Stage.TargetedStep):
                self._fire_event('step_state_started', skipped)
            else:
                self._fire_event('step_runner_started', skipped)
            skipped = self._running_stage.check_if_current_step_will_run()

    def state_result_step(self, event):
        if not self._running_stage:
            # not inside a running stage, igore step
            return
        step = self._running_stage.state_result_step(event)
        if not step:
            return
        self._fire_event('step_state_result', step)

    def start(self):
        """
        Start the monitoring thread
        """
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
