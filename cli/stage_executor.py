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

import logging
import os
import signal
import subprocess
import threading
import time
import sys

from .common import clean_pyc_files
from .monitor import Monitor
from .monitors.terminal_outputter import SimplePrinter, StepListPrinter
from .stage_parser import RenderingException


# pylint: disable=C0103
logger = logging.getLogger(__name__)


class StageExecutor(threading.Thread):
    """
    Executes a stage in its own process
    """
    def __init__(self, stage_name):
        super(StageExecutor, self).__init__()
        self.stage_name = stage_name
        self.proc = None
        self.retcode = None

    def run(self):
        """
        Runs the stage in a different process
        """
        clean_pyc_files()
        with open(os.devnull, "w") as fnull:
            self.proc = subprocess.Popen(["salt-run", "state.orch", self.stage_name],
                                         stdout=fnull, stderr=fnull)
            self.retcode = self.proc.wait()

    def interrupt(self):
        """
        Sends SIGINT signal to the salt-run process
        """
        if self.proc:
            self.proc.send_signal(signal.SIGINT)

    def is_running(self):
        """
        Checks if the salt-run process is running
        """
        return self.proc is not None and self.retcode is None


def run_stage(stage_name, hide_state_steps, hide_dynamic_steps, simple_output):
    """
    Runs a stage
    Args:
        stage_name (str): the stage name
        hide_state_steps (bool): don't show state result steps
        hide_dynamic_steps (bool): don't show runtime generated steps
        simple_output (bool): use the minimal outputter
    """
    mon = Monitor(not hide_state_steps, not hide_dynamic_steps)
    printer = SimplePrinter() if simple_output else StepListPrinter(False)
    mon.add_listener(printer)
    try:
        mon.parse_stage(stage_name)
    except RenderingException:
        return 2

    mon.start()
    executor = StageExecutor(stage_name)

    # pylint: disable=W0613
    def sigint_handler(*args):
        """
        SIGINT signal handler
        """
        logger.debug("SIGINT, stopping stage executor")
        if executor.is_running():
            executor.interrupt()
        else:
            if mon.is_running():
                mon.stop(True)
            sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    executor.start()

    if sys.version_info > (3, 0):
        logger.debug("Python 3: blocking main thread on join()")
        executor.join()
    else:
        logger.debug("Python 2: polling for monitor.is_running() %s", mon.is_running())
        while executor.is_running():
            time.sleep(1)
        executor.join()

    time.sleep(1)
    mon.stop(True)
    return executor.retcode
