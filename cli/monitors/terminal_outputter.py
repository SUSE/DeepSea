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
from ..salt_event import NewRunnerEvent, NewJobEvent

# pylint: disable=C0111
# pylint: disable=C0103
logger = logging.getLogger(__name__)


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

    def stage_parsing_finished(self, stage, output):
        PP.println("done")
        PP.println()
        PP.println("Stage initialization output:")
        PP.println(output.strip())
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
            PP.print("         {}... ".format(minion))
        else:
            PP.print("               in {}... ".format(minion))
        if step.targets[minion]['success']:
            PP.println("ok")
        else:
            PP.println("fail")

    def step_state_finished(self, step):
        self.current_step.pop()

    def step_state_result(self, step, event):
        if self.current_step:
            if not self.current_step[-1]['endl']:
                self.current_step[-1]['endl'] = True
                PP.println()
        if event.name == event.state_id:
            PP.print("         |_  {}: {} ".format(event.minion, event.name))
        else:
            PP.print("         |_  {}: {}({}) ".format(event.minion, event.state_id, event.name))

        if event.result:
            PP.println("ok")
        else:
            PP.println("fail")

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


class StepListPrinter(MonitorListener):
    """
    This class takes care of printing DeepSea execution in the terminal as a list of steps, but
    uses its own thread to allow the output of time clock counters for each step
    """
    # pylint: disable=C0103
    OK = PP.green(PP.bold(u"\u2713"))
    FAIL = PP.red(u"\u274C")
    WAITING = PP.orange(u"\u23F3")

    def print_step(self, step, depth=0):
        """
        Prints a single step
        Args:
            step (StepListPrinter.Step): the step object
            depth (int): the step depth, if depth > 0 it's a substep
        """
        step_order_width = 9
        step_desc_width = 60
        indent = 2

        if depth == 0:
            # root step
            if step.step.order > 0:
                step_order = "[{}/{}]".format(step.step.order, self.total_steps)
            else:
                step_order = "[init]"

            rest = step_order_width - len(step_order)
            rest = 0 if rest < 0 else rest
            offset = len(step_order) + rest + 1

        else:
            prefix_indent = step_order_width + indent * depth
            offset = prefix_indent + 4

        desc_width = step_desc_width - (offset - step_order_width)

        if not step.reprint:
            step.reprint = True
        elif depth == 0:
            step.clean(desc_width)

        if depth == 0:
            PP.print(PP.bold("{}{} ".format(step_order, " " * rest)))
        else:
            PP.print("{} |_ ".format(" " * prefix_indent))

        step.print(offset, desc_width, depth)

    @staticmethod
    def format_desc(desc, width):
        """
        Breaks the string into an array of strings of max length width
        """
        result = []
        while len(desc) > width:
            idx = desc[:width].rfind(' ')
            if idx != -1:
                result.append(desc[0:idx])
                desc = desc[idx+1:]
            else:
                idx = desc[width-1:].find(' ')
                if idx != -1:
                    idx = idx + (width - 1)
                    result.append(desc[:idx])
                    desc = desc[idx+1:]
                else:
                    break
        result.append(desc)
        return result

    class Step(object):
        def __init__(self, printer, step):
            self.printer = printer
            self.step = step
            self.finished = False
            self.reprint = False
            self.substeps = OrderedDict()
            self.args = step.args_str
            if step.start_event:
                self.start_ts = datetime.datetime.strptime(step.start_event.stamp,
                                                           "%Y-%m-%dT%H:%M:%S.%f")
            else:
                self.start_ts = None

            if step.skipped:
                self.finished = True

        def start_runner_substep(self, step):
            self.substeps[step.jid] = StepListPrinter.Runner(self.printer, step)

        def start_state_substep(self, step):
            self.substeps[step.jid] = StepListPrinter.State(self.printer, step)

        def finish_substep(self, step):
            if step.jid not in self.substeps:
                logger.info("missed start event for this substep: %s", step.end_event)
                return
            self.substeps[step.jid].finished = True

        # pylint: disable=W0613
        def print(self, offset, desc_width, depth):
            """
            Prints the status of a step
            """
            # if not self.reprint:
            #     self.reprint = True
            # else:
            #     self.clean(desc_width)

        def clean(self, desc_width):
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

        def clean(self, desc_width):
            for substep in self.substeps.values():
                if substep.reprint:
                    substep.clean(desc_width-5)
            PP.print("\x1B[A\x1B[K")
            if self.args and len(self.step.name) + len(self.args)+2 >= desc_width:
                PP.print("\x1B[A\x1B[K" * len(StepListPrinter.format_desc(self.args, desc_width)))

        def print(self, offset, desc_width, depth):
            super(StepListPrinter.Runner, self).print(offset, desc_width, depth)

            if len(self.step.name) + len(self.args)+2 < desc_width:
                if self.args:
                    desc_length = len(self.step.name) + len(self.args) + 2
                    PP.print(PP.blue("{}({})".format(self.step.name, self.args)))
                else:
                    desc_length = len(self.step.name)
                    PP.print(PP.blue("{}".format(self.step.name)))
                PP.print(PP.blue("{} ".format("." * (desc_width - desc_length))))
                print_args = False
            else:
                desc_length = len(self.step.name)
                PP.print(PP.blue("{}".format(self.step.name)))
                PP.print(PP.blue("{} ".format("." * (desc_width - desc_length))))
                print_args = True

            if self.finished:
                if self.step.skipped:
                    PP.println(PP.grey("skipped"))
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

            if self.args and print_args:
                lines = StepListPrinter.format_desc(self.args, desc_width-2)
                lines[-1] += ")"
                first = True
                for line in lines:
                    PP.print(" " * offset)
                    if first:
                        PP.println(PP.blue("({}".format(line)))
                        first = False
                    else:
                        PP.println(PP.blue(" {}".format(line)))

            for substep in self.substeps.values():
                self.printer.print_step(substep, depth+1)

    class State(Step):
        def __init__(self, printer, step):
            super(StepListPrinter.State, self).__init__(printer, step)

        def clean(self, desc_width):
            if self.args and len(self.step.name) + len(self.args) + 5 >= desc_width:
                PP.print("\x1B[A\x1B[K" *
                         len(StepListPrinter.format_desc(self.args, desc_width)))

            if self.step.skipped:
                PP.print("\x1B[A\x1B[K")
            else:
                for substep in self.substeps.values():
                    if substep.reprint:
                        substep.clean(desc_width-5)

                for target in self.step.targets.values():
                    PP.print("\x1B[A\x1B[K" * (len(target['states'])+1))
                PP.print("\x1B[A\x1B[K")

        def print(self, offset, desc_width, depth):
            super(StepListPrinter.State, self).print(offset, desc_width, depth)

            if len(self.step.name) + len(self.args)+2 < desc_width:
                if self.args:
                    desc_length = len(self.step.name) + len(self.args) + 2
                    PP.print(PP.orange("{}({})".format(self.step.name, self.args)))
                else:
                    desc_length = len(self.step.name)
                    PP.print(PP.orange("{}".format(self.step.name)))
                if not self.step.skipped:
                    PP.print(PP.orange(" on"))
                print_args = False
            else:
                desc_length = len(self.step.name)
                PP.print(PP.orange("{}".format(self.step.name)))
                print_args = True

            if self.step.skipped:
                PP.print(PP.orange("{} ".format("." * (desc_width - desc_length))))
                PP.println(PP.grey('skipped'))
            else:
                PP.println()

            if self.args and print_args:
                lines = StepListPrinter.format_desc(self.args, desc_width-2)
                lines[-1] += ")"
                if not self.step.skipped:
                    lines[-1] += " on"
                first = True
                for line in lines:
                    PP.print(" " * offset)
                    if first:
                        PP.println(PP.orange("({}".format(line)))
                        first = False
                    else:
                        PP.println(PP.orange(" {}".format(line)))

            if self.step.skipped:
                return

            for substep in self.substeps.values():
                self.printer.print_step(substep, depth+1)

            for target, data in self.step.targets.items():
                PP.print(" " * offset)
                PP.print(PP.cyan(target))
                PP.print(PP.cyan("{} ".format("." * (desc_width - len(target)))))
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

                for state_res in data['states']:
                    msg = state_res.step.pretty_string()
                    PP.print(" " * offset)
                    PP.print(PP.grey("  |_ {}".format(msg)))
                    msg_rest = desc_width - (len(msg) + 3) - 2
                    msg_rest = 0 if msg_rest < 0 else msg_rest
                    PP.print(PP.grey("{} ".format("." * msg_rest)))
                    if state_res.finished:
                        if state_res.success:
                            PP.println(u"{}".format(StepListPrinter.OK))
                        else:
                            PP.println(u"{}".format(StepListPrinter.FAIL))
                    else:
                        PP.println(StepListPrinter.WAITING)

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
                        self.printer.print_step(self.printer.step)

            PP.print("\x1B[?25h")  # shows cursor

    def __init__(self, clear_screen=True):
        super(StepListPrinter, self).__init__()
        self._clear_screen = clear_screen
        self.stage = None
        self.total_steps = None
        self.errors = None
        self.step = None
        self.thread = None
        self.print_lock = threading.Lock()
        self.init_output = None
        self.init_output_printed = False

    def stage_started(self, stage_name):
        if self._clear_screen:
            os.system('clear')
        PP.p_bold("Starting stage: ")
        PP.println(PP.light_purple(stage_name))

        self.errors = OrderedDict()
        self.stage = None
        self.total_steps = None

    def stage_parsing_started(self, stage_name):
        PP.print(PP.info("Parsing {} steps... ".format(stage_name)))
        PP.println(StepListPrinter.WAITING)

    def stage_parsing_finished(self, stage, output):
        PP.print("\x1B[A\x1B[K")
        PP.print(PP.info("Parsing {} steps... ".format(stage.name)))
        PP.println(StepListPrinter.OK)
        PP.println()
        # PP.println(PP.bold("Stage initialization output:"))
        # PP.println(output.strip())
        # PP.println()
        self.init_output = output.strip()

        self.stage = stage
        self.total_steps = stage.total_steps()

        self.thread = StepListPrinter.PrinterThread(self)
        self.thread.start()

    def stage_finished(self, stage):
        self.step = None
        self.thread.stop()
        self.thread = None

        PP.println("\x1B[K")

        if not self.init_output_printed and self.init_output:
            PP.println(PP.bold("Stage initialization output:"))
            PP.println(self.init_output)
            PP.println()

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
            if self.step and isinstance(self.step.step.start_event, NewJobEvent):
                self.step.start_runner_substep(step)
            else:
                self.step = StepListPrinter.Runner(self, step)
                if step.order == 1:
                    PP.println()
                    # first step, need to output initialization stdout
                    if self.init_output:
                        PP.println(PP.bold("Stage initialization output:"))
                        PP.println(self.init_output)
                    self.init_output_printed = True
                    PP.println()
                elif step.order > 1:
                    PP.println()
            self.print_step(self.step)
            if step.skipped:
                self.step = None

    def step_runner_finished(self, step):
        if not step.success:
            if step.name not in self.errors:
                self.errors[step.name] = step.end_event

        with self.print_lock:
            if self.step and self.step.step.jid != step.jid:
                self.step.finish_substep(step)
            elif self.step:
                self.step.finished = True
                self.print_step(self.step)

            if self.step.step.jid == step.jid:
                self.step = None

    def step_state_started(self, step):
        with self.print_lock:
            if self.step and isinstance(self.step.step.start_event, NewRunnerEvent):
                self.step.start_state_substep(step)
            else:
                self.step = StepListPrinter.State(self, step)
                if step.order == 1:
                    PP.println()
                    # first step, need to output initialization stdout
                    if self.init_output:
                        PP.println(PP.bold("Stage initialization output:"))
                        PP.println(self.init_output)
                    self.init_output_printed = True
                    PP.println()
                elif step.order > 1:
                    PP.println()
            self.print_step(self.step)
            if step.skipped:
                self.step = None

    def step_state_minion_finished(self, step, minion):
        if not step.targets[minion]['success']:
            if step.name not in self.errors:
                self.errors[step.name] = OrderedDict()
            self.errors[step.name][minion] = step.targets[minion]['event']

        with self.print_lock:
            if self.step and self.step.step.jid != step.jid:
                self.step.finish_substep(step)
            elif self.step:
                self.step.finished = True
                self.print_step(self.step)

    def step_state_finished(self, step):
        with self.print_lock:
            if self.step and self.step.step.jid == step.jid:
                self.step = None

    def step_state_result(self, step, event):
        with self.print_lock:
            assert self.step
            assert isinstance(self.step, StepListPrinter.State)
            self.print_step(self.step)
