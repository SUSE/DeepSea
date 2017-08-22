# -*- coding: utf-8 -*-
"""
DeepSea CLI
"""
from __future__ import absolute_import
from __future__ import print_function

import argparse
import logging.config
import logging
import signal
import sys

from .common import PrettyPrinter as PP
from .monitor import Monitor
from .stage_parser import SLSParser


def _parse_cli_args():
    """
    This function initializes and parses the CLI arguments
    """
    parser = argparse.ArgumentParser(prog="deepsea")
    parser.add_argument("-m", "--monitor",
                        help="monitors and shows the progress of DeepSea salt commands",
                        action="store_true")
    parser.add_argument("--show-stage-steps", help="Lists the steps of a given DeepSea stage",
                        type=str)
    parser.add_argument("--log-level", help="set log level (default: none)",
                        choices=["info", "error", "debug", "none"], default="none")
    parser.add_argument("--log-file", help="log file location", type=str,
                        default="/var/log/deepsea.log")
    return parser.parse_args()


def _setup_logging(log_level, log_file):
    """
    Logging configuration
    """
    if log_level == "none":
        return

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
        },
        'handlers': {
            'file': {
                'level': log_level.upper(),
                'filename': log_file,
                'class': 'logging.FileHandler',
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['file'],
                'level': log_level.upper(),
                'propagate': True,
            }
        }
    })


def _run_monitor():
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


def _run_show_stage_steps(stage_name):
    """
    Runs stage parser and prints the list of steps
    """
    PP.p_header("Parsing stage: {}".format(stage_name))
    steps = SLSParser.parse_state_steps(stage_name)
    print()
    PP.p_bold("List of steps for stage: {}".format(stage_name))
    for i, step in enumerate(steps):
        print("{}: {}".format(PP.yellow(i), step))
    print()


def main():
    """
    CLI main function
    """
    args = _parse_cli_args()

    _setup_logging(args.log_level, args.log_file)

    if args.monitor:
        _run_monitor()
    elif args.show_stage_steps:
        _run_show_stage_steps(args.show_stage_steps)
