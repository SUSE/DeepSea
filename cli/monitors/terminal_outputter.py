# -*- coding: utf-8 -*-
"""
This module is responsible outputting the DeepSee stage execution progress to the terminal
"""
from __future__ import absolute_import
from __future__ import print_function

from collections import OrderedDict
import datetime
import logging
import os
import threading
import time

from ..common import PrettyPrinter as PP
from ..monitor import MonitorListener

# pylint: disable=C0111
# pylint: disable=C0103
logger = logging.getLogger(__name__)


class ProgressBarPrinter(MonitorListener):
    """
    This class takes care of printing DeepSea execution in the terminal as progress bar
    """
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


class SimplePrinter(MonitorListener):
    def __init__(self):
        self.total_steps = None
        self.errors = OrderedDict()

    def stage_started(self, stage_name):
        PP.println("Starting stage: {}".format(stage_name))

    def stage_parsing_started(self, stage_name):
        PP.print("Parsing stage {} steps... ".format(stage_name))

    def stage_parsing_finished(self, stage):
        PP.println("done")
        self.total_steps = stage.total_steps()

    def stage_finished(self, stage):
        if not self.errors and not stage.success:
            PP.println(PP.bold("Stage execution failed: "))
            ret = stage.end_event.raw_event['data']['return']
            if isinstance(ret, dict):
                for data in stage.end_event.raw_event['data']['return']['data'].values():
                    for state in data.values():
                        if not state['result']:
                            PP.println("  - {}".format(state['__id__']))
            elif isinstance(ret, str):
                for line in ret.split('\n'):
                    PP.println("  {}".format(line))
            else:
                PP.println("  Unknown Error")

            return

        succeeded = stage.current_step - len(self.errors)
        PP.println("Finished stage {}: succeeded={}/{} failed={}/{}"
                   .format(stage.name, succeeded, self.total_steps, len(self.errors),
                           self.total_steps))

        if self.errors:
            PP.println()
            PP.println(PP.bold("Failures summary:\n"))
            for step, error in self.errors.items():
                if isinstance(error, dict):
                    step_dir_path = "/srv/salt/{}".format(step.replace('.', '/'))
                    if os.path.exists(step_dir_path):
                        PP.println("{} ({}):".format(step, step_dir_path))
                    else:
                        PP.println("{}:".format(step))
                    for minion, event in error.items():
                        PP.println("  {}:".format(minion))
                        ret_data = event.raw_event['data']['return']
                        if isinstance(ret_data, dict):
                            ret_data = ret_data.values()
                        for substep in ret_data:
                            if isinstance(substep, dict):
                                if not substep['result']:
                                    PP.println("    {}: {}".format(substep['__id__'],
                                                                   substep['comment']))
                                    if 'changes' in substep:
                                        if 'stdout' in substep['changes']:
                                            PP.println("        stdout: {}".format(
                                                substep['changes']['stdout']))
                                        if 'stderr' in substep['changes']:
                                            PP.println("        stderr: {}".format(
                                                substep['changes']['stderr']))
                            else:
                                PP.println("    {}".format(substep))
                else:
                    step_file_path = "/srv/modules/runners/{}.py".format(step[:step.find('.')])
                    if os.path.exists(step_file_path):
                        PP.println("{} ({}):".format(step, step_file_path))
                    else:
                        PP.println("{}:".format(step))
                    traceback = error.raw_event['data']['return']
                    for line in traceback.split('\n'):
                        PP.println("  {}".format(line))

    def step_runner_started(self, step):
        PP.print("[{}/{}] Executing runner {}... "
                 .format(step.order, self.total_steps, step.name))
        if step.skipped:
            PP.println("skipped")

    def step_runner_finished(self, step):
        if not step.success:
            if step.name not in self.errors:
                self.errors[step.name] = step.end_event
        if step.success:
            PP.println("ok")
        else:
            PP.println("fail")

    def step_state_started(self, step):
        PP.println("[{}/{}] Executing sstate {}... "
                   .format(step.order, self.total_steps, step.name))
        if step.skipped:
            PP.println("skipped")

    def step_state_minion_finished(self, step, minion):
        if not step.targets[minion]['success']:
            if step.name not in self.errors:
                self.errors[step.name] = OrderedDict()
            self.errors[step.name][minion] = step.targets[minion]['event']
        PP.print("  in {}... ".format(minion))
        if step.targets[minion]['success']:
            PP.println("ok")
        else:
            PP.println("fail")


class ThreadedStepListPrinter(MonitorListener):
    """
    This class takes care of printing DeepSea execution in the terminal as a list of steps, but
    uses its own thread to allow the output of time clock counters for each step
    """
    # pylint: disable=C0103
    OK = PP.green(PP.bold(u"\u2713"))
    FAIL = PP.red(u"\u274C")
    WAITING = PP.orange(u"\u23F3")

    class Step(object):
        def __init__(self, printer, step):
            self.printer = printer
            self.step = step
            self.finished = False
            self.reprint = False
            if step.start_event:
                self.start_ts = datetime.datetime.strptime(step.start_event.stamp,
                                                           "%Y-%m-%dT%H:%M:%S.%f")
            else:
                self.start_ts = None

            if step.skipped:
                self.finished = True

        def print(self):
            """
            Prints the status of a step
            """
            if not self.reprint:
                self.reprint = True
            else:
                self.clean()

        def clean(self):
            """
            Prepare for re-print of step
            """
            raise NotImplementedError()

        def ftime(self, tr):
            if tr.seconds > 0:
                return "{}s".format(int(round(tr.seconds+tr.microseconds/1000000.0)))
            else:
                return "{}s".format(round(tr.seconds+tr.microseconds/1000000.0, 1))
            # return "{}s".format(round(tr.seconds+tr.microseconds/1000000.0, 1))

    class Runner(Step):
        def __init__(self, printer, step):
            super(ThreadedStepListPrinter.Runner, self).__init__(printer, step)

        def clean(self):
            PP.print("\x1B[A\x1B[K")

        def print(self):
            super(ThreadedStepListPrinter.Runner, self).print()

            PP.p_bold("{:12}".format("[{}/{}]: ".format(self.step.order,
                                                        self.printer.total_steps)))
            PP.print(PP.blue("{:.<55} ".format(self.step.name)))

            if self.step.finished:
                if self.step.skipped:
                    PP.println(PP.grey(' skipped'))
                else:
                    PP.print(ThreadedStepListPrinter.OK if self.step.success
                             else ThreadedStepListPrinter.FAIL)
                    ts = datetime.datetime.strptime(self.step.end_event.stamp,
                                                    "%Y-%m-%dT%H:%M:%S.%f")
                    PP.println(" ({})".format(self.ftime(ts-self.start_ts)))
            else:
                ts = datetime.datetime.now()
                PP.print(ThreadedStepListPrinter.WAITING)
                PP.println(" ({})".format(self.ftime(ts-self.start_ts)))

    class State(Step):
        def __init__(self, printer, step):
            super(ThreadedStepListPrinter.State, self).__init__(printer, step)

        def clean(self):
            if self.step.skipped:
                PP.print("\x1B[A")
            else:
                PP.print("\x1B[A" * (len(self.step.targets)+1))

        def print(self):
            super(ThreadedStepListPrinter.State, self).print()

            if self.step.skipped:
                PP.p_bold("\x1B[K{:12}".format("[{}/{}]: "
                          .format(self.step.order, self.printer.total_steps)))
                PP.print(PP.orange("{:.<55}".format(self.step.name)))
                PP.println(PP.grey(' skipped'))
                return

            PP.p_bold("\x1B[K{:12}".format("[{}/{}]: ".format(self.step.order,
                                                              self.printer.total_steps)))
            PP.println(PP.orange("{} on".format(self.step.name)))

            for target, data in self.step.targets.items():
                PP.print(PP.cyan("\x1B[K{:12}{:.<55} ".format('', target)))
                if data['finished']:
                    PP.print(ThreadedStepListPrinter.OK if data['success']
                             else ThreadedStepListPrinter.FAIL)
                    ts = datetime.datetime.strptime(data['event'].stamp,
                                                    "%Y-%m-%dT%H:%M:%S.%f")
                    PP.println(" ({})".format(self.ftime(ts-self.start_ts)))
                else:
                    ts = datetime.datetime.now()
                    PP.print(ThreadedStepListPrinter.WAITING)
                    PP.println(" ({})".format(self.ftime(ts-self.start_ts)))

    class PrinterThread(threading.Thread):
        def __init__(self, printer):
            super(ThreadedStepListPrinter.PrinterThread, self).__init__()
            self.printer = printer
            self.daemon = True
            self.running = True

        def stop(self):
            self.running = False
            self.join()

        def run(self):
            self.running = True
            PP.print("\x1B[?25l")  # hides cursor
            while self.running:
                time.sleep(0.1)
                if self.printer.step:
                    with self.printer.print_lock:
                        self.printer.step.print()

            PP.print("\x1B[?25h")  # shows cursor

    def __init__(self):
        super(ThreadedStepListPrinter, self).__init__()
        self.stage = None
        self.total_steps = None
        self.errors = None
        self.step = None
        self.thread = None
        self.print_lock = threading.Lock()

    def stage_started(self, stage_name):
        os.system('clear')
        PP.p_bold("Starting stage: ")
        PP.println(PP.light_purple(stage_name))

        self.errors = OrderedDict()
        self.stage = None
        self.total_steps = None

    def stage_parsing_started(self, stage_name):
        PP.print(PP.info("Parsing {} steps... ".format(stage_name)))
        PP.println(ThreadedStepListPrinter.WAITING)

    def stage_parsing_finished(self, stage):
        PP.print("\x1B[A\x1B[K")
        PP.print(PP.info("Parsing {} steps... ".format(stage.name)))
        PP.println(ThreadedStepListPrinter.OK)
        PP.println()

        self.stage = stage
        self.total_steps = stage.total_steps()

        self.thread = ThreadedStepListPrinter.PrinterThread(self)
        self.thread.start()

    def stage_finished(self, stage):
        self.step = None
        self.thread.stop()
        self.thread = None

        PP.println("\x1B[K")

        if not self.errors and not stage.success:
            PP.println(PP.bold("Stage execution failed: "))
            ret = stage.end_event.raw_event['data']['return']
            if isinstance(ret, dict):
                for data in stage.end_event.raw_event['data']['return']['data'].values():
                    for state in data.values():
                        if not state['result']:
                            PP.println(PP.red("  - {}".format(state['__id__'])))
            elif isinstance(ret, str):
                for line in ret.split('\n'):
                    PP.println(PP.red("  {}".format(line)))
            else:
                PP.println(PP.red("  Unknown Error"))

            return

        PP.p_bold("Ended stage: ")
        PP.print(PP.light_purple("{} ".format(self.stage.name)))
        succeeded = stage.current_step - len(self.errors)
        PP.print(PP.green("succeeded={}/{}".format(succeeded, self.total_steps)))
        if self.errors:
            PP.print(PP.red(" failed={}/{}".format(len(self.errors), self.total_steps)))

        start_ts = datetime.datetime.strptime(stage.start_event.stamp, "%Y-%m-%dT%H:%M:%S.%f")
        end_ts = datetime.datetime.strptime(stage.end_event.stamp, "%Y-%m-%dT%H:%M:%S.%f")
        PP.print(PP.yellow(" time={}s".format(round((end_ts-start_ts).total_seconds(), 1))))
        PP.println()

        if self.errors:
            PP.println()
            PP.println(PP.bold("Failures summary:\n"))
            for step, error in self.errors.items():
                if isinstance(error, dict):
                    step_dir_path = "/srv/salt/{}".format(step.replace('.', '/'))
                    if os.path.exists(step_dir_path):
                        PP.println(PP.orange("{} ({}):".format(step, step_dir_path)))
                    else:
                        PP.println(PP.orange("{}:".format(step)))
                    for minion, event in error.items():
                        PP.println(PP.cyan("  {}:".format(minion)))
                        ret_data = event.raw_event['data']['return']
                        if isinstance(ret_data, dict):
                            ret_data = ret_data.values()
                        for substep in ret_data:
                            if isinstance(substep, dict):
                                if not substep['result']:
                                    PP.println("    {}: {}".format(PP.info(substep['__id__']),
                                                                   PP.red(substep['comment'])))
                                    if 'changes' in substep:
                                        if 'stdout' in substep['changes']:
                                            PP.println("        stdout: {}".format(
                                                PP.red(substep['changes']['stdout'])))
                                        if 'stderr' in substep['changes']:
                                            PP.println("        stderr: {}".format(
                                                PP.red(substep['changes']['stderr'])))
                            else:
                                PP.println("    {}".format(PP.red(substep)))
                        logger.debug("state error in minion '%s':\n%s", minion, event.raw_event)
                else:
                    step_file_path = "/srv/modules/runners/{}.py".format(step[:step.find('.')])
                    if os.path.exists(step_file_path):
                        PP.println(PP.orange("{} ({}):".format(step, step_file_path)))
                    else:
                        PP.println(PP.orange("{}:".format(step)))
                    traceback = error.raw_event['data']['return']
                    for line in traceback.split('\n'):
                        PP.println(PP.red("  {}".format(line)))

                    logger.debug("runner error:\n%s", error.raw_event)

    def step_runner_started(self, step):
        with self.print_lock:
            self.step = ThreadedStepListPrinter.Runner(self, step)
            self.step.print()

    def step_runner_finished(self, step):
        if not step.success:
            if step.name not in self.errors:
                self.errors[step.name] = step.end_event
        with self.print_lock:
            self.step.finished = True
            self.step.print()

    def step_state_started(self, step):
        with self.print_lock:
            self.step = ThreadedStepListPrinter.State(self, step)
            self.step.print()

    def step_state_minion_finished(self, step, minion):
        if not step.targets[minion]['success']:
            if step.name not in self.errors:
                self.errors[step.name] = OrderedDict()
            self.errors[step.name][minion] = step.targets[minion]['event']

        with self.print_lock:
            self.step.finished = True
            self.step.print()

    def step_state_finished(self, step):
        # do nothing for now
        pass
