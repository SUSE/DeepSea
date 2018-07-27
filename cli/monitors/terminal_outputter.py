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
import re
import threading
import time

from ..common import PrettyPrinter as PP, check_terminal_utf8_support
from ..monitor import MonitorListener
from ..stage_parser import StateRenderingException


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

    def stage_parsing_finished(self, stage, output, exception):
        if exception:
            PP.println("fail")
            PP.println()
            if isinstance(exception, StateRenderingException):
                PP.println("An error occurred when rendering one of the following states:")
                for state in exception.states:
                    PP.print("    - {}".format(state))
                    PP.println(" ({})".format("/srv/salt/{}".format(state.replace(".", "/"))))
            else:
                PP.println("An error occurred while rendering the stage file:")
                PP.println("    {}".format(exception.stage_file))
            PP.println()
            PP.println("Error description:")
            PP.println(exception.pretty_error_desc_str())
            return

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
                            ret_data = list(ret_data.values())
                        if isinstance(ret_data, list):
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
                            for line in ret_data.split('\n'):
                                PP.println("    {}".format(line))
                else:
                    step_file_path = "/srv/modules/runners/{}.py".format(step[:step.find('.')])
                    if os.path.exists(step_file_path):
                        PP.println("{} ({}):".format(step, step_file_path))
                    else:
                        PP.println("{}:".format(step))

                    if error is not None:
                        traceback = error.raw_event['data']['return']
                        for line in traceback.split('\n'):
                            PP.println("  {}".format(line))
                        logger.debug("runner error:\n%s", error.raw_event)
                    else:
                        PP.println("  runner response was not received")
                        logger.debug("runner error: response was not received")

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
        self.current_step.append({'endl': False})

    def step_runner_finished(self, step):
        if step.order > 0 and not step.success:
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

    def step_runner_skipped(self, step):
        if step.order == 1:
            # first step after 'init'
            PP.println()
        PP.println("[{}/{}] Executing runner {}... skipped"
                   .format(step.order, self.total_steps, step.name))

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
        self.current_step.append({'endl': True})

    def step_state_minion_finished(self, step, minion):
        if step.order > 0 and not step.targets[minion]['success']:
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

    def step_state_skipped(self, step):
        if step.order == 1:
            # first step after 'init'
            PP.println()

        PP.println("[{}/{}] Executing state {}... skipped"
                   .format(step.order, self.total_steps, step.name))

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
                    first = False
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
                    first = False
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
    HAS_UTF8_SUPPORT = check_terminal_utf8_support()
    # pylint: disable=C0103
    OK = PP.green(PP.bold(u"\u2713")) if HAS_UTF8_SUPPORT else PP.green("OK")
    FAIL = PP.red(u"\u274C") if HAS_UTF8_SUPPORT else PP.red("Fail")
    WAITING = PP.orange(u"\u23F3") if HAS_UTF8_SUPPORT else PP.orange("Running")

    STAGE = staticmethod(PP.magenta)
    INFO = staticmethod(PP.dark_yellow)
    RUNNER = staticmethod(PP.blue)
    STATE = staticmethod(PP.orange)
    MINION = staticmethod(PP.cyan)
    STATE_RES = staticmethod(PP.grey)
    SUCCESS = staticmethod(PP.dark_green)
    FAILURE = staticmethod(PP.red)
    TIME = staticmethod(PP.purple)

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
            if depth > 1:
                prefix_indent += 3
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

        def _find_running_substep(self):
            for substep in self.substeps.values():
                if not substep.finished:
                    return substep
            return self

        def start_runner_substep(self, step):
            substep = self._find_running_substep()
            substep.substeps[step.jid] = SP.Runner(self.printer, step)

        def start_state_substep(self, step):
            substep = self._find_running_substep()
            substep.substeps[step.jid] = SP.State(self.printer, step)

        def finish_substep(self, step):
            if step.jid in self.substeps:
                self.substeps[step.jid].finished = True
                return True
            for substep in self.substeps.values():
                if substep.finish_substep(step):
                    return True
            return False

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
            return "{}s".format(round(tr.seconds+tr.microseconds/1000000.0, 1))

    class Runner(Step):
        def clean(self, desc_width):
            for substep in self.substeps.values():
                if substep.reprint:
                    substep.clean(desc_width-5)
            PP.print("\x1B[A\x1B[K")
            if self.args and len(self.step.name) + len(self.args)+2 >= desc_width:
                PP.print("\x1B[A\x1B[K" * len(SP.format_desc(self.args, desc_width)))

        def print(self, offset, desc_width, depth):
            super(SP.Runner, self).print(offset, desc_width, depth)

            if len(self.step.name) + len(self.args)+2 < desc_width:
                if self.args:
                    desc_length = len(self.step.name) + len(self.args) + 2
                    PP.print(SP.RUNNER("{}({})".format(self.step.name, self.args)))
                else:
                    desc_length = len(self.step.name)
                    PP.print(SP.RUNNER("{}".format(self.step.name)))
                PP.print(SP.RUNNER("{} ".format("." * (desc_width - desc_length))))
                print_args = False
            else:
                desc_length = len(self.step.name)
                PP.print(SP.RUNNER("{}".format(self.step.name)))
                PP.print(SP.RUNNER("{} ".format("." * (desc_width - desc_length))))
                print_args = True

            if self.finished:
                if self.step.skipped:
                    PP.println(PP.grey("skipped"))
                else:
                    PP.print(SP.OK if self.step.success else SP.FAIL)
                    if self.step.end_event:
                        ts = datetime.datetime.strptime(
                            self.step.end_event.stamp, "%Y-%m-%dT%H:%M:%S.%f")
                    else:
                        ts = datetime.datetime.now()
                    PP.println(" ({})".format(SP.Step.ftime(ts-self.start_ts)))
            else:
                ts = datetime.datetime.utcnow()
                PP.print(SP.WAITING)
                PP.println(" ({})".format(SP.Step.ftime(ts-self.start_ts)))

            if self.args and print_args:
                lines = StepListPrinter.format_desc(self.args, desc_width-2)
                lines[-1] += ")"
                first = True
                for line in lines:
                    PP.print(" " * offset)
                    if first:
                        PP.println(SP.RUNNER("({}".format(line)))
                        first = False
                    else:
                        PP.println(SP.RUNNER(" {}".format(line)))

            for substep in self.substeps.values():
                self.printer.print_step(substep, depth+1)

    class State(Step):
        def clean(self, desc_width):
            if self.args and len(self.step.name) + len(self.args) + 5 >= desc_width:
                PP.print("\x1B[A\x1B[K" * len(SP.format_desc(self.args, desc_width)))

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
            super(SP.State, self).print(offset, desc_width, depth)

            if len(self.step.name) + len(self.args)+2 < desc_width:
                if self.args:
                    desc_length = len(self.step.name) + len(self.args) + 2
                    PP.print(SP.STATE("{}({})".format(self.step.name, self.args)))
                else:
                    desc_length = len(self.step.name)
                    PP.print(SP.STATE("{}".format(self.step.name)))
                if not self.step.skipped:
                    PP.print(SP.STATE(" on"))
                print_args = False
            else:
                desc_length = len(self.step.name)
                PP.print(SP.STATE("{}".format(self.step.name)))
                print_args = True

            if self.step.skipped:
                PP.print(SP.STATE("{} ".format("." * (desc_width - desc_length))))
                PP.println(PP.grey('skipped'))
            else:
                PP.println()

            if self.args and print_args:
                lines = SP.format_desc(self.args, desc_width-2)
                lines[-1] += ")"
                if not self.step.skipped:
                    lines[-1] += " on"
                first = True
                for line in lines:
                    PP.print(" " * offset)
                    if first:
                        PP.println(SP.STATE("({}".format(line)))
                        first = False
                    else:
                        PP.println(SP.STATE(" {}".format(line)))

            if self.step.skipped:
                return

            for substep in self.substeps.values():
                self.printer.print_step(substep, depth+1)

            for target, data in self.step.targets.items():
                PP.print(" " * offset)
                PP.print(SP.MINION(target))
                PP.print(SP.MINION("{} ".format("." * (desc_width - len(target)))))
                if data['finished']:
                    PP.print(SP.OK if data['success'] else SP.FAIL)
                    ts = datetime.datetime.strptime(data['event'].stamp,
                                                    "%Y-%m-%dT%H:%M:%S.%f")
                    PP.println(" ({})".format(SP.Step.ftime(ts-self.start_ts)))
                else:
                    ts = datetime.datetime.utcnow()
                    PP.print(SP.WAITING)
                    PP.println(" ({})".format(SP.Step.ftime(ts-self.start_ts)))

                for state_res in data['states']:
                    msg = state_res.step.pretty_string()
                    PP.print(" " * offset)
                    PP.print(SP.STATE_RES("  |_ {}".format(msg)))
                    msg_rest = desc_width - (len(msg) + 3) - 2
                    msg_rest = 0 if msg_rest < 0 else msg_rest
                    PP.print(SP.STATE_RES("{} ".format("." * msg_rest)))
                    if state_res.finished:
                        if state_res.success:
                            PP.println(u"{}".format(SP.OK))
                        else:
                            PP.println(u"{}".format(SP.FAIL))
                    else:
                        PP.println(SP.WAITING)

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
        self.stage_name = None
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
        PP.println(SP.STAGE(stage_name))

        self.stage_name = stage_name
        self.errors = OrderedDict()
        self.stage = None
        self.total_steps = None

    def stage_parsing_started(self, stage_name):
        PP.print(SP.INFO("Parsing {} steps... ".format(stage_name)))
        PP.println(SP.WAITING)
        PP.println()

    def stage_parsing_state(self, states, minion=None):
        # PP.print("\x1B[A\x1B[K")

        PP.print(PP.bold("[parsing] "))
        PP.println(SP.MINION("on {}".format(minion if minion else "master")))
        PP.print("            |_ ")
        for state in states:
            PP.println(PP.light_purple(state))
            PP.print("               ")
        PP.println()

    def stage_parsing_finished(self, stage, output, exception):
        # PP.print("\x1B[A\x1B[K")
        PP.print(SP.INFO("Parsing {} steps... ".format(self.stage_name)))
        if exception:
            PP.println(SP.FAIL)
            PP.println()
            if isinstance(exception, StateRenderingException):
                PP.println(PP.bold("An error occurred when rendering one of the following "
                                   "states:"))
                PP.print(PP.cyan("    - {}".format(exception.state)))
                PP.println(" ({})"
                           .format("/srv/salt/{}"
                                   .format(exception.state.replace(".", "/"))))
            else:
                PP.println(PP.bold("An error occurred while rendering the stage:"))
                PP.println(PP.cyan("    {}".format(exception.stage_name)))
            PP.println()
            PP.println(PP.bold("Error description:"))
            PP.println(PP.red(exception.pretty_error_desc_str()))
            return

        PP.println(SP.OK)
        PP.println()
        self.init_output = output.strip()

        self.stage = stage
        self.total_steps = stage.total_steps()

        self.thread = SP.PrinterThread(self)
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
                    if isinstance(data, dict):
                        data = data.values()
                    for state in data:
                        if isinstance(state, dict):
                            if not state['result']:
                                if '__id__' in state:
                                    PP.println(PP.red("  - {}"
                                                      .format(state['__id__'])))
                                elif 'comment' in state:
                                    PP.println(PP.red(
                                        "  - {}".format(state['comment'])))
                        elif isinstance(state, str):
                            PP.println(PP.red("  {}".format(state)))
            elif isinstance(ret, str):
                for line in ret.split('\n'):
                    PP.println(SP.FAILURE("  {}".format(line)))
            else:
                PP.println(SP.FAILURE("  Unknown Error"))

            return

        PP.p_bold("Ended stage: ")
        PP.print(SP.STAGE("{} ".format(self.stage.name)))
        succeeded = stage.current_step - len(self.errors)
        PP.print(SP.SUCCESS("succeeded={}/{}".format(succeeded, self.total_steps)))
        if self.errors:
            PP.print(SP.FAILURE(" failed={}/{}".format(len(self.errors), self.total_steps)))

        start_ts = datetime.datetime.strptime(stage.start_event.stamp, "%Y-%m-%dT%H:%M:%S.%f")
        end_ts = datetime.datetime.strptime(stage.end_event.stamp, "%Y-%m-%dT%H:%M:%S.%f")
        PP.print(SP.TIME(" time={}s".format(round((end_ts-start_ts).total_seconds(), 1))))
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
                        PP.println(SP.MINION("  {}:".format(minion)))
                        ret_data = event.raw_event['data']['return']
                        if isinstance(ret_data, list):
                            ret_data = dict([(None, val) for val in ret_data])
                        if isinstance(ret_data, dict):
                            for key, substep in ret_data.items():
                                if isinstance(substep, dict):
                                    if not substep['result']:
                                        if '__id__' not in substep:
                                            match = re.match(r".*\|-(.*)_\|-.*", key)
                                            if match:
                                                substep_id = match.group(1)
                                            else:
                                                substep_id = None
                                        else:
                                            substep_id = substep['__id__']
                                        if substep_id:
                                            PP.println("    {}: {}"
                                                       .format(PP.info(substep_id),
                                                               PP.red(substep['comment'])))
                                        else:
                                            PP.println("    {}"
                                                       .format(PP.red(substep['comment'])))
                                        if 'changes' in substep:
                                            if 'stdout' in substep['changes']:
                                                PP.println("        stdout: {}".format(
                                                    PP.red(substep['changes']['stdout'])))
                                            if 'stderr' in substep['changes']:
                                                PP.println("        stderr: {}".format(
                                                    PP.red(substep['changes']['stderr'])))
                                else:
                                    PP.println("    {}".format(PP.red(substep)))
                        elif isinstance(ret_data, str):
                            # pylint: disable=E1101
                            for line in ret_data.split('\n'):
                                PP.println("    {}".format(PP.red(line)))
                        else:
                            PP.println("    {}".format(PP.red(ret_data)))
                        logger.debug("state error in minion '%s':\n%s", minion, event.raw_event)
                else:
                    step_file_path = "/srv/modules/runners/{}.py".format(step[:step.find('.')])
                    if os.path.exists(step_file_path):
                        PP.println(PP.orange("{} ({}):".format(step, step_file_path)))
                    else:
                        PP.println(PP.orange("{}:".format(step)))
                    if error is not None:
                        traceback = error.raw_event['data']['return']
                        for line in traceback.split('\n'):
                            PP.println(PP.red("  {}".format(line)))
                        logger.debug("runner error:\n%s", error.raw_event)
                    else:
                        PP.println(PP.red("  runner response was not received"))
                        logger.debug("runner error: response was not received")

    def step_runner_started(self, step):
        with self.print_lock:
            if self.step:
                # substep starting
                self.step.start_runner_substep(step)
            else:
                self.step = SP.Runner(self, step)
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

    def step_runner_finished(self, step):
        if step.order > 0 and not step.success:
            if step.name not in self.errors:
                self.errors[step.name] = step.end_event

        with self.print_lock:
            if self.step and self.step.step.jid != step.jid:
                # maybe it's a substep
                if not self.step.finish_substep(step):
                    logger.error("substep jid=%s not found: event=\n%s", step.jid, step.end_event)
            elif self.step:
                self.step.finished = True
                self.print_step(self.step)
            if self.step.step.jid == step.jid:
                self.step = None

    def step_runner_skipped(self, step):
        # the step_runner_started already handles skipped steps
        self.step_runner_started(step)
        self.step = None

    def step_state_started(self, step):
        with self.print_lock:
            if self.step:
                self.step.start_state_substep(step)
            else:
                self.step = SP.State(self, step)
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

    def step_state_minion_finished(self, step, minion):
        if step.order > 0 and not step.targets[minion]['success']:
            if step.name not in self.errors:
                self.errors[step.name] = OrderedDict()
            self.errors[step.name][minion] = step.targets[minion]['event']

        with self.print_lock:
            if self.step and self.step.step.jid != step.jid:
                # maybe it's a substep
                if not self.step.finish_substep(step):
                    logger.error("substep jid=%s not found: event=\n%s", step.jid, step.end_event)
            elif self.step:
                self.print_step(self.step)

    def step_state_finished(self, step):
        with self.print_lock:
            if self.step and self.step.step.jid == step.jid:
                self.step.finished = True
                self.step = None

    def step_state_result(self, step, event):
        with self.print_lock:
            assert self.step
            assert isinstance(self.step, StepListPrinter.State)
            self.print_step(self.step)

    def step_state_skipped(self, step):
        # the step_state_started already handles skipped steps
        self.step_state_started(step)
        self.step = None


SP = StepListPrinter
