# -*- coding: utf-8 -*-
"""
DeepSea CLI
"""
from __future__ import absolute_import
from __future__ import print_function

import argparse
import signal
import sys

from .monitor import Monitor


def _parse_cli_args():
    """
    This function initializes and parses the CLI arguments
    """
    parser = argparse.ArgumentParser(prog="deepsea")
    parser.add_argument("-m", "--monitor",
                        help="Monitors and shows progress of DeepSea salt commands",
                        action="store_true")
    return parser.parse_args()


def run_monitor():
    """
    Run the DeepSea stage monitor and progress visualizer
    """
    monitor = Monitor()

    # pylint: disable=W0613
    def sigint_handler(*args):
        """
        SIGINT signal handler
        """
        monitor.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, sigint_handler)

    print("Use Ctrl+C to stop the monitor")
    monitor.start()


def main():
    """
    CLI main function
    """
    args = _parse_cli_args()

    if args.monitor:
        run_monitor()
