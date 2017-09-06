# -*- coding: utf-8 -*-
"""
DeepSea stage's progress monitor
"""
# pylint: disable=W1699
from __future__ import absolute_import
from __future__ import print_function

import logging
import operator
import threading

from .common import PrettyPrinter as PP
from .salt_event import SaltEventProcessor
from .salt_event import EventListener
from .salt_event import NewJobEvent, NewRunnerEvent, RetJobEvent, RetRunnerEvent
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
            self.args_str = ""

        def start(self, event):
            self.jid = event.jid
            self.start_event = event
            first = True
            for arg in event.args:
                if isinstance(arg, dict):
                    for key, val in arg.items():
                        if key in ['concurrent', 'saltenv', '__kwarg__', 'queue']:
                            continue
                        if first:
                            self.args_str += "{}={}".format(key, val)
                            first = False
                        else:
                            self.args_str += ", {}={}".format(key, val)
                    first = True
                else:
                    if arg == self.name:
                        continue
                    if first:
                        first = True
                        self.args_str += "{}".format(arg)
                    else:
                        self.args_str += ", {}".format(arg)

        def finish(self, event):
            self.success = event.success
            self.finished = True
            self.end_event = event

    class TargetedStep(Step):
        def __init__(self, step, name, order):
            super(Stage.TargetedStep, self).__init__(step, name, order)
            self.targets = None
            self.sub_steps = []

        # pylint: disable=W0221
        def start(self, event):
            super(Stage.TargetedStep, self).start(event)
            self.targets = {}
            for target in event.targets:
                self.targets[target] = {
                    'finished': False,
                    'success': None,
                    'states': [Stage.Step(s.step, s.name, s.order) for s in self.sub_steps
                               if s.step.target == target]
                }

        def finish(self, event):
            self.targets[event.minion]['finished'] = True
            self.targets[event.minion]['success'] = event.success and event.retcode == 0
            self.targets[event.minion]['event'] = event

            if reduce(operator.__and__, [t['finished'] for t in self.targets.values()]):
                self.success = reduce(
                    operator.__and__, [t['success'] for t in self.targets.values()])
                self.finished = True

        def state_result(self, event):
            for sstep in self.targets[event.minion]['states']:
                if isinstance(sstep.step, SaltModule):
                    if sstep.name == event.name or sstep.name == event.state_id:
                        sstep.success = event.result
                        sstep.finished = True
                        sstep.end_event = event
                elif isinstance(sstep.step, SaltBuiltIn):
                    name = sstep.step.get_arg('name')
                    if not name:
                        name = sstep.step.desc
                    if name == event.name or name == event.state_id:
                        sstep.success = event.result
                        sstep.finished = True
                        sstep.end_event = event

    def __init__(self, name, steps, enable_dynamic):
        self.name = name
        self._parsed_steps = steps
        self.jid = None
        self.success = None
        self._executing = False
        self.current_step = 0
        self.start_event = None
        self.end_event = None
        self._enable_dynamic = enable_dynamic
        self._dynamic_steps = {}

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

        if self.current_step >= len(self._steps):
            return None

        curr_step = self._steps[self.current_step]

        if isinstance(event, NewRunnerEvent):
            if isinstance(curr_step.step, SaltRunner):
                if not curr_step.jid and curr_step.name == event.fun[7:]:
                    curr_step.start(event)
                    return curr_step

        elif isinstance(event, NewJobEvent):
            if isinstance(curr_step, Stage.TargetedStep):
                step_name = event.args[0] if event.fun == 'state.sls' else event.fun
                if not curr_step.jid and curr_step.name == step_name:
                    curr_step.start(event)
                    return curr_step

        else:
            assert False

        if not self._enable_dynamic:
            return None

        if curr_step.end_event is not None:
            # only allow dynamic steps as substeps after the first step
            return None

        # this step is not part of stage parsed steps
        if isinstance(event, NewRunnerEvent):
            step = Stage.Step(None, event.fun[7:], -1)
            step.start(event)
            if self.current_step == 0 and curr_step.start_event is None:
                # check for duplicates before starting step 1
                for ex_step in self._dynamic_steps.values():
                    if (ex_step.name == step.name and
                            ex_step.args_str == step.args_str):
                        logger.info("FOUND DUPLICATE: %s(%s)", ex_step.name, ex_step.args_str)
                        # possible parsing generated duplicate
                        return None
            self._dynamic_steps[event.jid] = step
            return step
        elif isinstance(event, NewJobEvent):
            step_name = event.args[0] if event.fun == 'state.sls' else event.fun
            step = Stage.TargetedStep(None, step_name, -1)
            step.start(event)
            if self.current_step == 0 and curr_step.start_event is None:
                # check for duplicates before starting step 1
                for ex_step in self._dynamic_steps.values():
                    if (ex_step.name == step.name and ex_step.targets.keys() == event.targets and
                            ex_step.args_str == step.args_str):
                        # possible parsing generated duplicate
                        return None
            self._dynamic_steps[event.jid] = step
            return step

        return None

    def finish_step(self, event):
        """
        Consumes the current step
        Args:
            event (saltevent.SaltEvent): the step object
        """
        assert self._executing

        if self.current_step >= len(self._steps):
            return None

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

        if not self._enable_dynamic:
            return None

        # this step is not part of stage parsed steps
        if isinstance(event, RetRunnerEvent):
            if event.jid in self._dynamic_steps:
                step = self._dynamic_steps[event.jid]
                step.finish(event)
                return step
        elif isinstance(event, RetJobEvent):
            if event.jid in self._dynamic_steps:
                step = self._dynamic_steps[event.jid]
                step.finish(event)
                return step

        return None

    def state_result_step(self, event):
        """
        Consumes teh current step
        Args:
            event (saltevent.StateResultEvent): the state result event
        """
        assert self._executing

        if self.current_step >= len(self._steps):
            return None

        curr_step = self._steps[self.current_step]
        assert not curr_step.finished

        if event.jid == curr_step.jid:
            curr_step.state_result(event)
            return curr_step

        return None

    def check_if_current_step_will_run(self):
        assert self._executing

        if self.current_step >= len(self._steps):
            return None

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

    def stage_parsing_finished(self, stage, output):
        """
        This function is called when a stage parsing finished
        Args:
            stage (Stage): the stage object or None if a parsing error occurred
            output (str): the stdout output of parsing
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

    def step_state_result(self, step, event):
        """
        This function is called when a Salt state result is received
        Args:
            step (Stage.TargetedStep): the step upon this state result was stored
            event (saltevent.StateResultEvent): the event object
        """
        pass

    def step_state_finished(self, step):
        """
        This function is called when a Salt state finishes executing in all targets
        Args:
            step (Stage.Step): the step object
        """
        pass


class Monitor(threading.Thread):
    """
    Stage monitoring class
    """

    class Event(object):
        def __init__(self, monitor, func, event):
            self.monitor = monitor
            self.func = func
            self.event = event

        def call(self):
            logger.debug("handle: %s", self.event)
            getattr(self.monitor, self.func)(self.event)

    class DeepSeaEventListener(EventListener):
        """
        Salt event listener for DeepSea
        """
        def __init__(self, monitor):
            self.monitor = monitor

        def handle_new_runner_event(self, event):
            if 'pillar' in event.fun or 'saltutil.find_job' in event.fun:
                return
            logger.debug("buffer: %s", event)
            if event.fun == 'runner.state.orch':
                self.monitor.append_event(Monitor.Event(self.monitor, 'start_stage', event))
            else:
                self.monitor.append_event(Monitor.Event(self.monitor, 'start_step', event))

        def handle_ret_runner_event(self, event):
            if 'pillar' in event.fun or 'saltutil.find_job' in event.fun:
                return
            logger.debug("buffer: %s", event)
            if event.fun == 'runner.state.orch':
                self.monitor.append_event(Monitor.Event(self.monitor, 'end_stage', event))
            else:
                self.monitor.append_event(Monitor.Event(self.monitor, 'end_step', event))

        def handle_new_job_event(self, event):
            if 'pillar' in event.fun or 'saltutil.find_job' in event.fun or 'grains' in event.fun:
                return
            if event.fun == 'deepsea.render_sls':
                return
            logger.debug("buffer: %s", event)
            self.monitor.append_event(Monitor.Event(self.monitor, 'start_step', event))

        def handle_ret_job_event(self, event):
            if 'pillar' in event.fun or 'saltutil.find_job' in event.fun or 'grains' in event.fun:
                return
            if event.fun == 'deepsea.render_sls':
                return
            logger.debug("buffer: %s", event)
            self.monitor.append_event(Monitor.Event(self.monitor, 'end_step', event))

        def handle_state_result_event(self, event):
            logger.debug("buffer: %s", event)
            self.monitor.append_event(Monitor.Event(self.monitor, 'state_result_step', event))

    def __init__(self, show_state_steps, show_dynamic_steps):
        super(Monitor, self).__init__()
        self._processor = SaltEventProcessor()
        self._processor.add_listener(Monitor.DeepSeaEventListener(self))
        self._show_state_steps = show_state_steps
        self._show_dynamic_steps = show_dynamic_steps
        self._running_stage = None
        self._monitor_listeners = []
        self._event_lock = threading.Lock()
        self._event_cond = threading.Condition(self._event_lock)
        self._event_buffer = []
        self._running = False
        self._stage_steps = {}

    def parse_stage(self, stage_name):
        self._fire_event('stage_started', stage_name)
        self._fire_event('stage_parsing_started', stage_name)
        parsed_steps, out = SLSParser.parse_state_steps(stage_name, not self._show_state_steps,
                                                        True, False)
        self._stage_steps[stage_name] = (parsed_steps, out)

    def append_event(self, event):
        with self._event_cond:
            self._event_buffer.append(event)
            self._event_cond.notify()

    def start(self):
        """
        Start the monitoring thread
        """
        logger.info("Starting the DeepSea event monitoring")
        self._processor.start()
        super(Monitor, self).start()

    def stop(self, wait=False):
        """
        Stop the monitoring thread
        """
        logger.info("Stopping the DeepSea event monitoring")
        self._running = False
        self._processor.stop()

        if wait:
            self.wait_to_finish()

    def wait_to_finish(self):
        """
        Blocks until the Salt event processor thread finishes
        """
        self._processor.join()
        self.join()

    def is_running(self):
        """
        Checks wheather the Salt event process is still runnning
        """
        return self._processor.is_running() and self._running

    def run(self):
        self._running = True
        while self._running:
            with self._event_cond:
                if self._event_buffer:
                    event = self._event_buffer.pop(0)
                    event.call()
                else:
                    self._event_cond.wait(0.2)

    def add_listener(self, listener):
        """
        Register a monitor listener
        Args:
            listener (MonitorListener): the listener object
        """
        assert isinstance(listener, MonitorListener)
        self._monitor_listeners.append(listener)

    def _fire_event(self, event, *args):
        logger.debug("fire event: %s", event)
        for listener in self._monitor_listeners:
            getattr(listener, event)(*args)

    def start_stage(self, event):
        """
        Sets the current running stage
        Args:
            event (NewRunnerEvent): the DeepSea state.orch start event
        """
        stage_name = event.args[0]
        if stage_name in self._stage_steps:
            parsed_steps, out = self._stage_steps[stage_name]
        else:
            self._fire_event('stage_started', stage_name)
            self._fire_event('stage_parsing_started', stage_name)
            parsed_steps, out = SLSParser.parse_state_steps(stage_name,
                                                            not self._show_state_steps,
                                                            True, False)
        self._running_stage = Stage(stage_name, parsed_steps, self._show_dynamic_steps)

        self._fire_event('stage_parsing_finished', self._running_stage, out)

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
        logger.info("End stage: %s jid=%s success=%s", tmp_stage.name, tmp_stage.jid, event.success)
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
        if not step:
            return
        if isinstance(step, Stage.TargetedStep):
            logger.info("Started State step: [%s/%s] name=%s(%s) on=%s", step.order,
                        self._running_stage.total_steps(), step.name, step.args_str,
                        step.targets.keys())
            self._fire_event('step_state_started', step)
        else:
            logger.info("Started Runner step: [%s/%s] name=%s(%s)", step.order,
                        self._running_stage.total_steps(), step.name, step.args_str)
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
            logger.info("Finished State step: [%s/%s] name=%s(%s) in=%s success=%s", step.order,
                        self._running_stage.total_steps(), step.name, step.args_str,
                        event.minion, step.targets[event.minion]['success'])
            if not step.targets[event.minion]['success']:
                logger.info("State step error:\n%s", PP.format_dict(event.raw_event))
            self._fire_event('step_state_minion_finished', step, event.minion)
            if step.finished:
                self._fire_event('step_state_finished', step)
        else:
            logger.info("Finished Runner step: [%s/%s] name=%s(%s) success=%s", step.order,
                        self._running_stage.total_steps(), step.name, step.args_str,
                        event.success)
            if not event.success:
                logger.info("State step error:\n%s", PP.format_dict(event.raw_event))
            self._fire_event('step_runner_finished', step)

        skipped = self._running_stage.check_if_current_step_will_run()
        while skipped:
            if isinstance(skipped, Stage.TargetedStep):
                logger.info("Skipping state step: [%s/%s] name=%s(%s)", skipped.order,
                            self._running_stage.total_steps(), skipped.name, skipped.args_str)
                self._fire_event('step_state_started', skipped)
            else:
                logger.info("Skipping runner step: [%s/%s] name=%s(%s)", skipped.order,
                            self._running_stage.total_steps(), skipped.name, skipped.args_str)
                self._fire_event('step_runner_started', skipped)
            skipped = self._running_stage.check_if_current_step_will_run()

    def state_result_step(self, event):
        if not self._show_state_steps:
            return
        if not self._running_stage:
            # not inside a running stage, igore step
            return
        step = self._running_stage.state_result_step(event)
        if not step:
            return
        logger.info("State Result: %s: %s result=%s", event.state_id, event.name, event.result)
        self._fire_event('step_state_result', step, event)
