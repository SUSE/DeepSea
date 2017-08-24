# -*- coding: utf-8 -*-
"""
This module is responsible outputting the DeepSee stage execution progress to the terminal
"""
from __future__ import absolute_import
from __future__ import print_function

from collections import OrderedDict
import os

from ..common import PrettyPrinter as PP
from ..monitor import MonitorListener


class StepListPrinter(MonitorListener):
    """
    This class takes care of printing DeepSea execution in the terminal as a list of steps
    """
    # pylint: disable=C0103
    OK = PP.green(PP.bold(u"\u2713"))
    FAIL = PP.red(u"\u274C")
    WAITING = PP.orange(u"\u23F3")

    def __init__(self, use_colors=True):
        self.stage = None
        self.total_steps = None
        if not use_colors:
            StepListPrinter.OK = "ok"
            StepListPrinter.FAIL = "fail"
            StepListPrinter.WAITING = "waiting"

        self.errors = None

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

    def stage_finished(self, stage):
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
            PP.print(PP.red(" failed: {}/{}".format(len(self.errors), self.total_steps)))
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
                        for substep in event.raw_event['data']['return'].values():
                            if not substep['result']:
                                PP.println("    {}: {}".format(PP.info(substep['__id__']),
                                                               PP.red(substep['comment'])))
                else:
                    step_file_path = "/srv/modules/runners/{}.py".format(step[:step.find('.')])
                    if os.path.exists(step_file_path):
                        PP.println(PP.orange("{} ({}):".format(step, step_file_path)))
                    else:
                        PP.println(PP.orange("{}:".format(step)))
                    traceback = error.raw_event['data']['return']
                    for line in traceback.split('\n'):
                        PP.println(PP.red("  {}".format(line)))

    def step_runner_started(self, step):
        PP.p_bold("{:12}".format("[{}/{}]: ".format(step.order, self.total_steps)))
        PP.print(PP.blue("{:.<55} ".format(step.name)))

    def step_runner_finished(self, step):
        if not step.success:
            if step.name not in self.errors:
                self.errors[step.name] = step.end_event

        PP.println(StepListPrinter.OK if step.success else StepListPrinter.FAIL)

    def step_state_started(self, step):
        PP.p_bold("{:12}".format("[{}/{}]: ".format(step.order, self.total_steps)))
        PP.println(PP.orange("{} on".format(step.name)))
        for target in step.targets.keys():
            PP.print(PP.cyan("{:12}{:.<55} ".format('', target)))
            PP.println(StepListPrinter.WAITING)

    def step_state_minion_finished(self, step, minion):
        if not step.targets[minion]['success']:
            if step.name not in self.errors:
                self.errors[step.name] = OrderedDict()
            self.errors[step.name][minion] = step.targets[minion]['event']

        PP.print("\x1B[A" * len(step.targets))
        for target, data in step.targets.items():
            PP.print(PP.cyan("\x1B[K{:12}{:.<55} ".format('', target)))
            if data['finished']:
                PP.println(StepListPrinter.OK if data['success'] else StepListPrinter.FAIL)
            else:
                PP.println(StepListPrinter.WAITING)

    def step_state_finished(self, step):
        # do nothing for now
        pass


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
