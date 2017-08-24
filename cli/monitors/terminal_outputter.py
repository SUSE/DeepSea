# -*- coding: utf-8 -*-
"""
This module is responsible outputting the DeepSee stage execution progress to the terminal
"""
from __future__ import absolute_import
from __future__ import print_function

import os

from ..common import PrettyPrinter as PP
from ..monitor import MonitorListener


class StepListPrinter(MonitorListener):
    """
    This class takes care of printing DeepSea execution in the terminal as a list of steps
    """
    # pylint: disable=C0103
    OK = PP.green(PP.bold(u"\u2713"))
    FAIL = PP.red(PP.bold(u"\u274C"))
    WAITING = PP.orange(u"\u23F3")

    def __init__(self, use_colors=True):
        self.stage = None
        self.total_steps = None
        if not use_colors:
            StepListPrinter.OK = "ok"
            StepListPrinter.FAIL = "fail"
            StepListPrinter.WAITING = "waiting"

    def stage_started(self, stage_name):
        os.system('clear')
        PP.p_bold("Starting stage: ")
        PP.println(PP.light_purple(stage_name))

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
        PP.p_bold("Ended stage: ")
        PP.print(PP.light_purple("{} ".format(self.stage.name)))
        PP.println(PP.info("total={}/{}".format(stage.current_step, self.total_steps)))

    def step_runner_started(self, step):
        PP.p_bold("{:12}".format("[{}/{}]: ".format(step.order, self.total_steps)))
        PP.print(PP.orange("{:.<55} ".format(step.name)))

    def step_runner_finished(self, step):
        PP.println(StepListPrinter.OK if step.success else StepListPrinter.FAIL)

    def step_state_started(self, step):
        PP.p_bold("{:12}".format("[{}/{}]: ".format(step.order, self.total_steps)))
        PP.println(PP.orange("{} on".format(step.name)))
        for target in step.targets.keys():
            PP.print(PP.cyan("{:12}{:.<55} ".format('', target)))
            PP.println(StepListPrinter.WAITING)

    def step_state_minion_finished(self, step, minion):
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
