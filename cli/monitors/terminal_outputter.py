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
        self.current_step = []
        self.rewrite_runner_step = False

    def stage_started(self, stage_name):
        PP.println("Starting stage: {}".format(stage_name))

    def stage_parsing_started(self, stage_name):
        PP.print("Parsing stage {} steps... ".format(stage_name))

    def stage_parsing_finished(self, stage):
        PP.println("done")
        PP.println()
        self.total_steps = stage.total_steps()

    def stage_finished(self, stage):
        if not self.errors and not stage.success:
            PP.println("Stage execution failed: ")
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
            PP.println("Failures summary:")
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
        if step.order > 0:
            if step.order == 1:
                # first step after 'init'
                PP.println()
            PP.print("[{}/{}] Executing runner {}... "
                     .format(step.order, self.total_steps, step.name))
        else:
            if self.current_step:
                if self.current_step:
                    if not self.current_step[-1]['endl']:
                        self.current_step[-1]['endl'] = True
                        PP.println()
                PP.print("         |_  {}... "
                         .format(SimplePrinter.format_runner_event(step.start_event)))
            else:
                PP.print("[init] Executing runner {}... ".format(step.name))
        if step.skipped:
            PP.println("skipped")
        else:
            self.current_step.append({'endl': False})

    def step_runner_finished(self, step):
        if not step.success:
            if step.name not in self.errors:
                self.errors[step.name] = step.end_event

        if step.order > 0:
            if self.current_step[-1]['endl']:
                PP.print("[{}/{}] Executing runner {}... "
                         .format(step.order, self.total_steps, step.name))
        else:
            if len(self.current_step) < 2:
                if self.current_step[-1]['endl']:
                    PP.print("[init] Executing runner {}... ".format(step.name))
            elif self.current_step[-1]['endl']:
                PP.print("         |_  {}... "
                         .format(SimplePrinter.format_runner_event(step.start_event)))
        if step.success:
            PP.println("ok")
        else:
            PP.println("fail")

        self.current_step.pop()

    def step_state_started(self, step):
        if step.order > 0:
            if step.order == 1:
                # first step after 'init'
                PP.println()

            PP.println("[{}/{}] Executing state {}... "
                       .format(step.order, self.total_steps, step.name))
        else:
            if self.current_step:
                if self.current_step:
                    if not self.current_step[-1]['endl']:
                        self.current_step[-1]['endl'] = True
                        PP.println()
                PP.println("         |_  {}... "
                           .format(SimplePrinter.format_state_event(step.start_event)))
            else:
                PP.print("[init] Executing state {}... ".format(step.name))
        if step.skipped:
            PP.println("skipped")
        else:
            self.current_step.append({'endl': True})

    def step_state_minion_finished(self, step, minion):
        if not step.targets[minion]['success']:
            if step.name not in self.errors:
                self.errors[step.name] = OrderedDict()
            self.errors[step.name][minion] = step.targets[minion]['event']

        if step.order > 0:
            PP.print("             in {}... ".format(minion))
        else:
            PP.print("               in {}... ".format(minion))
        if step.targets[minion]['success']:
            PP.println("ok")
        else:
            PP.println("fail")

    def step_state_finished(self, step):
        self.current_step.pop()

    @staticmethod
    def format_runner_event(event):
        if event.fun.startswith('runner.'):
            fun_name = event.fun[7:]
        else:
            fun_name = event.fun
        args = ""
        first = True
        for arg in event.args:
            if isinstance(arg, dict):
                for key, val in arg.items():
                    if first:
                        args += "{}={}".format(key, val)
                        first = False
                    else:
                        args += ", {}={}".format(key, val)
            else:
                if first:
                    first = True
                    args += "{}".format(arg)
                else:
                    args += ", {}".format(arg)
        return "{}({})".format(fun_name, args)

    @staticmethod
    def format_state_event(event):
        fun_name = event.fun
        args = ""
        first = True
        for arg in event.args:
            if isinstance(arg, dict):
                for key, val in arg.items():
                    if first:
                        args += "{}={}".format(key, val)
                        first = False
                    else:
                        args += ", {}={}".format(key, val)
            else:
                if first:
                    first = True
                    args += "{}".format(arg)
                else:
                    args += ", {}".format(arg)
        # return "{}({}) on({})".format(fun_name, args, ", ".join(event.targets))
        return "{}({})".format(fun_name, args)

    def step_state_result(self, event):
        if self.current_step:
            if not self.current_step[-1]['endl']:
                self.current_step[-1]['endl'] = True
                PP.println()
        if event.name == event.state_id:
            PP.println("         |_  {} on {}".format(event.name, event.minion))
        else:
            PP.println("         |_  {}: {} on {}".format(event.state_id, event.name,
                                                          event.minion))


class StepListPrinter(MonitorListener):
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
            self.substeps = OrderedDict()
            if step.start_event:
                self.start_ts = datetime.datetime.strptime(step.start_event.stamp,
                                                           "%Y-%m-%dT%H:%M:%S.%f")
            else:
                self.start_ts = None

            if step.skipped:
                self.finished = True

            self.args = ""
            first = True
            for arg in step.start_event.args:
                if isinstance(arg, dict):
                    for key, val in arg.items():
                        if key in ['concurrent', 'saltenv', '__kwarg__', 'queue']:
                            continue
                        if first:
                            self.args += "{}={}".format(key, val)
                            first = False
                        else:
                            self.args += ", {}={}".format(key, val)
                    first = True
                else:
                    if arg == step.name:
                        continue
                    if first:
                        first = True
                        self.args += "{}".format(arg)
                    else:
                        self.args += ", {}".format(arg)

        def start_runner_substep(self, step):
            self.substeps[step.jid] = StepListPrinter.Runner(self.printer, step)

        def start_state_substep(self, step):
            self.substeps[step.jid] = StepListPrinter.State(self.printer, step)

        def finish_substep(self, step):
            self.substeps[step.jid].finished = True

        # pylint: disable=W0613
        def print(self, substep=False, indent=0):
            """
            Prints the status of a step
            """
            if not self.reprint:
                self.reprint = True
            elif not substep:
                self.clean()

        def clean(self):
            """
            Prepare for re-print of step
            """
            raise NotImplementedError()

        @staticmethod
        def ftime(tr):
            if tr.seconds > 0:
                return "{}s".format(int(round(tr.seconds+tr.microseconds/1000000.0)))
            else:
                return "{}s".format(round(tr.seconds+tr.microseconds/1000000.0, 1))

    class Runner(Step):
        def __init__(self, printer, step):
            super(StepListPrinter.Runner, self).__init__(printer, step)

        def clean(self):
            for substep in self.substeps.values():
                if substep.reprint:
                    substep.clean()
            PP.print("\x1B[A\x1B[K")
            if self.args:
                PP.print("\x1B[A\x1B[K")

        def print(self, substep=False, indent=0):
            super(StepListPrinter.Runner, self).print(substep, indent)

            if not substep:
                if self.step.order > 0:
                    PP.p_bold("{:12}".format("[{}/{}]: ".format(self.step.order,
                                                                self.printer.total_steps)))
                else:
                    PP.p_bold("{:12}".format("[init]: "))
            else:
                PP.print("{}".format(' ' * indent))
                PP.print(PP.grey("{:12}|_ ".format('')))

            if not substep:
                PP.print(PP.blue("{:.<55} ".format(self.step.name)))
            else:
                PP.print(PP.blue("{:.<50} ".format(self.step.name)))

            if self.step.finished:
                if self.step.skipped:
                    PP.println(PP.grey(' skipped'))
                else:
                    PP.print(StepListPrinter.OK if self.step.success
                             else StepListPrinter.FAIL)
                    ts = datetime.datetime.strptime(self.step.end_event.stamp,
                                                    "%Y-%m-%dT%H:%M:%S.%f")
                    PP.println(" ({})"
                               .format(StepListPrinter.Step.ftime(ts-self.start_ts)))
            else:
                ts = datetime.datetime.now()
                PP.print(StepListPrinter.WAITING)
                PP.println(" ({})".format(StepListPrinter.Step.ftime(ts-self.start_ts)))

            if self.args:
                if not substep:
                    PP.println(PP.blue("{:12}({}) ".format('', self.args)))
                else:
                    PP.print("{}".format(' ' * indent))
                    PP.println(PP.blue("{:15}({}) ".format('', self.args)))

            for substep in self.substeps.values():
                substep.print(True, indent+2)

    class State(Step):
        def __init__(self, printer, step):
            super(StepListPrinter.State, self).__init__(printer, step)
            self.state_results = []

        def add_state_result(self, event):
            """
            Appends a state result, only valid for State steps
            """
            self.state_results.append({'event': event, 'reprint': False})

        def clean(self):
            if self.step.skipped:
                PP.print("\x1B[A\x1B[K")
            else:
                for substep in self.substeps.values():
                    if substep.reprint:
                        substep.clean()
                for state_res in self.state_results:
                    if state_res['reprint']:
                        PP.print("\x1B[A\x1B[K")
                if self.args:
                    PP.print("\x1B[A\x1B[K")
                PP.print("\x1B[A\x1B[K" * (len(self.step.targets)+1))

        def print(self, substep=False, indent=0):
            super(StepListPrinter.State, self).print(substep, indent)

            if self.step.skipped:
                PP.p_bold("{:12}".format("[{}/{}]: "
                          .format(self.step.order, self.printer.total_steps)))
                PP.print(PP.orange("{:.<55}".format(self.step.name)))
                PP.println(PP.grey(' skipped'))
                return

            if not substep:
                if self.step.order > 0:
                    PP.p_bold("{:12}".format("[{}/{}]: ".format(self.step.order,
                                                                self.printer.total_steps)))
                else:
                    PP.p_bold("{:12}".format("[init]: "))
            else:
                PP.print("{:12}{}".format('', ' ' * indent))
                PP.print(PP.grey("|_ "))

            PP.print(PP.orange("{}".format(self.step.name)))

            if self.args:
                PP.println()
                if not substep:
                    PP.println(PP.orange("{:12}({}) on".format('', self.args)))
                else:
                    PP.print("{}".format(' ' * indent))
                    PP.println(PP.orange("{:15}({}) on".format('', self.args)))
            else:
                PP.println(PP.orange(" on"))

            for step in self.substeps.values():
                step.print(True, indent+2)

            for target, data in self.step.targets.items():
                if not substep:
                    PP.print("{:12}{}".format('', ' ' * indent))
                    PP.print(PP.cyan("{:.<55} ".format(target)))
                else:
                    PP.print("{:15}{}".format('', ' ' * indent))
                    PP.print(PP.cyan("{:.<50} ".format(target)))
                if data['finished']:
                    PP.print(StepListPrinter.OK if data['success']
                             else StepListPrinter.FAIL)
                    ts = datetime.datetime.strptime(data['event'].stamp,
                                                    "%Y-%m-%dT%H:%M:%S.%f")
                    PP.println(" ({})"
                               .format(StepListPrinter.Step.ftime(ts-self.start_ts)))
                else:
                    ts = datetime.datetime.now()
                    PP.print(StepListPrinter.WAITING)
                    PP.println(" ({})"
                               .format(StepListPrinter.Step.ftime(ts-self.start_ts)))
                for state_res in self.state_results:
                    event = state_res['event']
                    state_res['reprint'] = True
                    if event.minion == target:
                        if event.name == event.state_id:
                            msg = event.name
                        else:
                            msg = "{}: {}".format(event.state_id, event.name)
                        if not substep:
                            PP.print("{:14}{}|_ ".format('', ' ' * indent))
                            PP.print(PP.grey("{:.<50}".format(msg)))
                        else:
                            PP.print("{:17}{}|_ ".format('', ' ' * indent))
                            PP.print(PP.grey("{:.<47}".format(msg)))
                        if event.result:
                            PP.println(u" {}".format(StepListPrinter.OK))
                        else:
                            PP.println(u" {}".format(StepListPrinter.FAIL))

    class PrinterThread(threading.Thread):
        def __init__(self, printer):
            super(StepListPrinter.PrinterThread, self).__init__()
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
                time.sleep(0.5)
                with self.printer.print_lock:
                    if self.printer.step:
                        self.printer.step.print()

            PP.print("\x1B[?25h")  # shows cursor

    def __init__(self):
        super(StepListPrinter, self).__init__()
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
        PP.println(StepListPrinter.WAITING)

    def stage_parsing_finished(self, stage):
        PP.print("\x1B[A\x1B[K")
        PP.print(PP.info("Parsing {} steps... ".format(stage.name)))
        PP.println(StepListPrinter.OK)
        PP.println()

        self.stage = stage
        self.total_steps = stage.total_steps()

        self.thread = StepListPrinter.PrinterThread(self)
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
            if self.step:
                self.step.start_runner_substep(step)
            else:
                self.step = StepListPrinter.Runner(self, step)
                PP.println()
            self.step.print()

    def step_runner_finished(self, step):
        if not step.success:
            if step.name not in self.errors:
                self.errors[step.name] = step.end_event

        with self.print_lock:
            if self.step and self.step.step.jid != step.jid:
                self.step.finish_substep(step)
            else:
                self.step.finished = True
            self.step.print()

            if self.step.step.jid == step.jid:
                self.step = None

    def step_state_started(self, step):
        with self.print_lock:
            if self.step:
                self.step.start_state_substep(step)
            else:
                self.step = StepListPrinter.State(self, step)
                PP.println()

            self.step.print()

    def step_state_minion_finished(self, step, minion):
        if not step.targets[minion]['success']:
            if step.name not in self.errors:
                self.errors[step.name] = OrderedDict()
            self.errors[step.name][minion] = step.targets[minion]['event']

        with self.print_lock:
            if self.step and self.step.step.jid != step.jid:
                self.step.finish_substep(step)
            else:
                self.step.finished = True
            self.step.print()

    def step_state_finished(self, step):
        with self.print_lock:
            if self.step.step.jid == step.jid:
                self.step = None

    def step_state_result(self, event):
        with self.print_lock:
            assert self.step
            assert isinstance(self.step, StepListPrinter.State)
            self.step.add_state_result(event)
            self.step.print()
