# -*- coding: utf-8 -*-
"""
DeepSea stage's progress monitor
"""
from __future__ import absolute_import
from __future__ import print_function

import logging
import operator
import os

from .common import PrettyPrinter as PP, print_progress
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
        def __init__(self, step, name):
            """
            Args:
                step (stage_parse.SaltStep): the parsed step
            """
            self.step = step
            self.name = name
            self.jid = None
            self.finished = False
            self.success = None

        def start(self, jid):
            self.jid = jid

        def finish(self, success):
            self.success = success
            self.finished = True

    class TargetedStep(Step):
        def __init__(self, step, name):
            super(Stage.TargetedStep, self).__init__(step, name)
            self.targets = None
            self.sub_steps = []
            self.curr_sub_step = 0

        def start(self, jid, targets):
            super(Stage.TargetedStep, self).start(jid)
            self.targets = {}
            for target in targets:
                self.targets[target] = {
                    'finished': False,
                    'success': None
                }

        def finish(self, target, success):
            self.targets[target] = {
                'finished': True,
                'success': success
            }
            if reduce(operator.__and__, [t['finished'] for t in self.targets.values()]):
                super(Stage.TargetedStep, self).finish(
                    reduce(operator.__and__, [t['success'] for t in self.targets.values()]))

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
        self._current_step = 0

        self._steps = []
        _curr_state = None
        for step in self._parsed_steps:
            wrapper = None
            if isinstance(step, SaltRunner):
                wrapper = Stage.Step(step, step.fun)
                _curr_state = None
            elif isinstance(step, SaltState):
                wrapper = Stage.TargetedStep(step, step.state)
                _curr_state = wrapper
            elif isinstance(step, SaltModule) or isinstance(step, SaltBuiltIn):
                assert _curr_state
                _curr_state.sub_steps.append(Stage.Step(step, step.fun))
                continue

            assert wrapper
            self._steps.append(wrapper)

    def start(self, jid):
        """
        Flags this stage as executing, and stores its salt job id
        """
        self._executing = True
        self.jid = jid

        self._current_step = 0

        os.system('clear')
        PP.p_bold("Starting stage: ")
        PP.println(PP.magenta(self.name))
        self.print_progress()

    def finish(self, success):
        """
        Flags this stage as finished, and stores the result
        """
        assert self._executing
        self._executing = False
        self.success = success

        #PP.print("\x1B[A")
        PP.println("\x1B[K")
        self.print_progress()
        print()
        PP.p_bold("Ended stage: ")
        PP.println(PP.magenta("{} total={}/{}".format(self.name, self._current_step,
                                                      len(self._steps))))

    def start_step(self, event):
        assert self._executing

        if isinstance(event, NewRunnerEvent):
            curr_step = self._steps[self._current_step]
            if isinstance(curr_step.step, SaltRunner):
                if curr_step.name == event.fun[7:]:
                    curr_step.start(event.jid)
                    #PP.print("\x1B[A")
                    #PP.print("\x1B[K")
                    PP.p_bold("Executing: ")
                    PP.print(PP.orange("{:.<40} ".format(curr_step.name)))

                    self.print_progress()

        elif isinstance(event, NewJobEvent):
            curr_step = self._steps[self._current_step]
            if isinstance(curr_step, Stage.TargetedStep):
                step_name = event.args[0] if event.fun == 'state.sls' else event.fun
                if curr_step.name == step_name:
                    curr_step.start(event.jid, event.targets)
                    #PP.print("\x1B[A")
                    #PP.print("\x1B[K")
                    PP.p_bold("Executing: ")
                    PP.println(PP.orange("{} on".format(curr_step.name)))
                    for target in event.targets:
                        PP.println(PP.cyan("{:11}{:.<40} ".format('', target)))

                    self.print_progress()

        else:
            assert False

    def finish_step(self, event):
        """
        Consumes the current step
        Args:
            event (saltevent.SaltEvent): the step object
        """
        assert self._executing

        if isinstance(event, RetRunnerEvent):
            curr_step = self._steps[self._current_step]
            if curr_step.jid and curr_step.jid == event.jid:
                curr_step.finish(event.success)
                #PP.print("\x1B[A")
                #PP.print("\x1B[A")
                #PP.print("\x1B[K")
                #PP.p_bold("Executing: ")
                #PP.print(PP.orange("{:.<40} ".format(curr_step.name)))
                done = (PP.green(PP.bold(u"\u2713")) if curr_step.success else
                        PP.red(PP.bold(u"\u274C")))
                PP.println(done)
                self._current_step += 1
                self.print_progress()

        elif isinstance(event, RetJobEvent):
            curr_step = self._steps[self._current_step]
            if curr_step.jid and curr_step.jid == event.jid:
                curr_step.finish(event.minion, event.success)
                # PP.print("\x1B[A")
                for iii in range(0, len(curr_step.targets)):
                    PP.print("\x1B[A")
                for target, data in curr_step.targets.items():
                    PP.print(PP.cyan("\x1B[K{:11}{:.<40} ".format('', target)))
                    if data['finished']:
                        done = PP.green(PP.bold(u"\u2713")) if data['success'] else \
                                                               PP.red(PP.bold(u"\u274C"))
                        PP.println(done)
                    else:
                        PP.println('')
                    self.print_progress()
                if curr_step.finished:
                    self._current_step += 1

        else:
            assert False

    def state_result_step(self, event):
        """
        Consumes teh current step
        Args:
            event (saltevent.StateResultEvent): the state result event
        """
        assert self._executing

        curr_step = self._steps[self._current_step]
        assert not curr_step.finished

        if event.jid == curr_step.jid:
            # we still need to verify if state result matches current sub step
            # curr_step.finish_sub_step(event.result)
            pass

    def print_progress(self):
        """
        Prints a progress bar
        """
        # PP.println("\x1B[K")
        # progress_array = [step.success for step in self._steps]
        # if self._current_step >= len(self._steps):
        #     suffix = (PP.green(PP.bold(u"\u2713")) if self.success else
        #               PP.red(PP.bold(u"\u274C")))
        # else:
        #     suffix = PP.orange("running {}".format(self._steps[self._current_step].name))
        # print_progress(progress_array, self._current_step, self.name[5:],
        #                suffix, 50)
        # PP.print("\x1B[A")
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
        self.stage_map = {}

    def start_stage(self, event):
        """
        Sets the current running stage
        Args:
            event (NewRunnerEvent): the DeepSea state.orch start event
        """
        self._running_stage = self.stage_map[event.args[0]]
        self._running_stage.start(event.jid)
        logger.info("Start stage: %s jid=%s", self._running_stage.name, self._running_stage.jid)

    def end_stage(self, event):
        """
        Sets the current running stage as finished
        Args:
            event (RetRunnerEvent): the DeepSea state.orch end event
        """
        self._running_stage.finish(event.success)
        logger.info("End stage: %s jid=%s success=%s", self._running_stage.name,
                    self._running_stage.jid, event.success)
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
        self._running_stage.start_step(event)

    def end_step(self, event):
        """
        Marks a step as finished from the execution tracking
        Args:
            event (RetJobEvent | RetRunnerEvent): the salt end event
        """
        if not self._running_stage:
            # not inside a running stage, igore step
            return
        self._running_stage.finish_step(event)

    def state_result_step(self, event):
        if not self._running_stage:
            # not inside a running stage, igore step
            return
        self._running_stage.state_result_step(event)

    def start(self):
        """
        Start the monitoring thread
        """
        self.stage_map['ceph.stage.0'] = Stage('ceph.stage.0',
                                               SLSParser.parse_state_steps('ceph.stage.0'))
        self.stage_map['ceph.stage.1'] = Stage('ceph.stage.1',
                                               SLSParser.parse_state_steps('ceph.stage.1'))
        self.stage_map['ceph.stage.2'] = Stage('ceph.stage.2',
                                               SLSParser.parse_state_steps('ceph.stage.2'))
        self.stage_map['ceph.stage.3'] = Stage('ceph.stage.3',
                                               SLSParser.parse_state_steps('ceph.stage.3'))
        self.stage_map['ceph.stage.4'] = Stage('ceph.stage.4',
                                               SLSParser.parse_state_steps('ceph.stage.4'))
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
