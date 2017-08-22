# -*- coding: utf-8 -*-
"""
DeepSea CLI
"""
from __future__ import absolute_import
from __future__ import print_function

import argparse
import logging.config
import logging
import os
import signal
import sys

from .common import PrettyPrinter as PP
from .monitor import Monitor
from .stage_parser import SLSParser, SaltState, SaltRunner, SaltModule


def _parse_cli_args():
    """
    This function initializes and parses the CLI arguments
    """
    parser = argparse.ArgumentParser(prog="deepsea", description="***** DeepSea CLI tool *****")
    parser.add_argument("-m", "--monitor",
                        help="monitors and shows the progress of DeepSea salt commands",
                        action="store_true")
    parser.add_argument("--show-stage-steps", help="Lists the steps of a given DeepSea stage",
                        type=str, metavar="STAGE_NAME")
    parser.add_argument('--list-all-steps', help="Shows all steps even if 'fire_event = False'. "
                                                 "To be used in conjuction with --show-stage-steps",
                        action="store_true")
    parser.add_argument("--log-level", help="set log level (default: info)",
                        choices=["info", "error", "debug", "silent"], default="info")
    parser.add_argument("--log-file", help="log file location", type=str,
                        default="/var/log/deepsea.log")
    return parser.parse_args()


def _setup_logging(log_level, log_file):
    """
    Logging configuration
    """
    if log_level == "silent":
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
        # sys.exit(0)
    signal.signal(signal.SIGINT, sigint_handler)

    os.system('clear')
    print("Use Ctrl+C to stop the monitor")
    monitor.start()


def _run_show_stage_steps(stage_name, all_steps):
    """
    Runs stage parser and prints the list of steps
    """
    PP.p_header("Parsing stage: {}".format(stage_name))
    steps = SLSParser.parse_state_steps(stage_name, not all_steps)
    print()
    PP.p_bold("List of steps for stage {}:".format(stage_name))
    print()
    state_count = 1
    sub_state_count = 1
    for step in steps:
        state_count_str = "{:<2}".format(state_count)
        sub_state_count_str = "{:4}{:>2}.{:<2}".format('', state_count-1, sub_state_count)
        if isinstance(step, SaltState):
            target_str = "{:30}".format(step.target)
            print("{}: [{}] {}".format(PP.bold(state_count_str), PP.magenta(target_str),
                                       PP.green("State({})".format(step.state))))
            state_count += 1
            sub_state_count = 1
        elif isinstance(step, SaltRunner):
            target_str = "{:30}".format('master')
            print("{}: [{}] {}".format(PP.bold(state_count_str), PP.magenta(target_str),
                                       PP.blue("Runner({})".format(step.fun))))
            state_count += 1
        elif isinstance(step, SaltModule):
            print("{}:{:26} {}".format(PP.bold(sub_state_count_str), '',
                                       PP.cyan("Module({})".format(step.fun))))
            sub_state_count += 1
        else:  # SaltBuiltIn
            step_str = "BuiltIn({})".format(step.fun)
            if step.fun in ['file.managed', 'file']:
                step_str = "BuiltIn({}, {})".format(step.fun, step.desc)
            elif step.fun in ['service.running', 'cmd.run']:
                step_str = "BuiltIn({}, {})".format(step.fun, step.args['name'])
            elif step.fun in ['pkg.latest', 'pkg.installed']:
                arg = step.desc
                if 'name' in step.args:
                    arg = step.args['name']
                elif 'pkgs' in step.args:
                    arg = step.args['pkgs']
                step_str = "BuiltIn({}, {})".format(step.fun, arg)

            print("{}:{:26} {}".format(PP.bold(sub_state_count_str), '',
                                       PP.yellow(step_str)))
            sub_state_count += 1
    print()
    PP.p_bold("Total steps of stage {}:".format(len(steps)))
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
        _run_show_stage_steps(args.show_stage_steps, args.list_all_steps)
