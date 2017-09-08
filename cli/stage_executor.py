# -*- coding: utf-8 -*-
"""
DeepSea Stage executor module
This module is responsible for starting the execution of a DeepSea stage

The user can run a stage like this:
    $ deepsea stage run ceph.stage.0

which is equivalent to:
    $ salt-run state.orch ceph.stage.0
"""
from __future__ import absolute_import

import os
import subprocess
import time

from .common import PrettyPrinter as PP
from .monitor import Monitor
from .monitors.terminal_outputter import SimplePrinter, StepListPrinter


class StageExecutor(object):
    """
    Executes a stage in its own process
    """
    def __init__(self, stage_name):
        super(StageExecutor, self).__init__()
        self.stage_name = stage_name

    def run(self):
        """
        Runs the stage in a different process
        """
        # pylint: disable=W8470
        with open(os.devnull, "w") as fnull:
            ret = subprocess.call(["salt-run", "state.orch", self.stage_name], stdout=fnull,
                                  stderr=fnull)
        return ret


def run_stage(stage_name, hide_state_steps, hide_dynamic_steps, simple_output):
    """
    Runs a stage
    Args:
        stage_name (str): the stage name
        hide_state_steps (bool): don't show state result steps
        hide_dynamic_steps (bool): don't show runtime generated steps
        simple_output (bool): use the minimal outputter
    """
    # check if stage exists
    stage_file = "/srv/salt/{}".format(stage_name.replace('.', '/'))
    if not os.path.exists(stage_file) and not os.path.exists("{}.sls".format(stage_file)):
        PP.println("{}: Stage {} does not exist".format(PP.red("ERROR"),
                                                        PP.cyan(stage_name)))
        return

    mon = Monitor(not hide_state_steps, not hide_dynamic_steps)
    printer = SimplePrinter() if simple_output else StepListPrinter(False)
    mon.add_listener(printer)
    mon.parse_stage(stage_name)
    mon.start()

    executor = StageExecutor(stage_name)
    ret = executor.run()
    time.sleep(1)
    mon.stop(True)
    return ret
