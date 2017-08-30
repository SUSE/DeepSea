# -*- coding: utf-8 -*-
"""
DeepSea CLI
"""
from __future__ import absolute_import
from __future__ import print_function

import logging.config
import logging
import os
import signal
import sys
import time
import click

from .common import PrettyPrinter as PP
from .monitor import Monitor
from .monitors.terminal_outputter import StepListPrinter
from .stage_parser import SLSParser, SaltState, SaltRunner, SaltModule


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
    monitor.add_listener(StepListPrinter())

    logger = logging.getLogger(__name__)

    # pylint: disable=W0613
    def sigint_handler(*args):
        """
        SIGINT signal handler
        """
        logger.debug("SIGINT, calling monitor.stop()")
        PP.pl_bold("\x1b[2K\rShutting down...")
        print()
        monitor.stop()

    signal.signal(signal.SIGINT, sigint_handler)

    os.system('clear')
    print("Use Ctrl+C to stop the monitor")
    PP.p_bold("Initializing DeepSea progess monitor...")
    monitor.start()
    PP.pl_bold(" Done.")
    print()
    if sys.version_info > (3, 0):
        logger.debug("Python 3: blocking main thread on join()")
        monitor.wait_to_finish()
    else:
        logger.debug("Python 2: polling for monitor.is_running() %s", monitor.is_running())
        while monitor.is_running():
            time.sleep(2)
        monitor.wait_to_finish()


def _run_show_stage_steps(stage_name, cache):
    """
    Runs stage parser and prints the list of steps
    """
    PP.p_header("Parsing stage: {}".format(stage_name))
    steps = SLSParser.parse_state_steps(stage_name, False, cache)
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
                arg = step.desc
                if 'name' in step.args:
                    arg = step.args['name']
                step_str = "BuiltIn({}, {})".format(step.fun, arg)
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


@click.group(name="deepsea")
@click.option('--log-level', default='info',
              type=click.Choice(["info", "error", "debug", "silent"]),
              help="set log level (default: info)")
@click.option('--log-file', default='/var/log/deepsea.log',
              type=click.Path(dir_okay=False),
              help="the file path for the log to be stored (default: /var/log/deepsea.log)")
def cli(log_level, log_file):
    _setup_logging(log_level, log_file)


@click.command(short_help='starts DeepSea progress monitor')
@click.option('--clear-cache', is_flag=True, help="clear steps cache")
@click.option('--no-cache', is_flag=True, help="don't store/use stage parsing results cache")
def monitor(clear_cache, no_cache):
    if clear_cache:
        SLSParser.clean_cache(None)
    _run_monitor()


@click.group(short_help='stage related commands')
def stage():
    pass


@click.command(name='show', short_help='show DeepSea stage steps')
@click.argument('stage_name', 'the DeepSea stage name')
@click.option('--clear-cache', is_flag=True, help="clear steps cache")
@click.option('--no-cache', is_flag=True, help="don't store/use stage parsing results cache")
def stage_show(stage_name, clear_cache, no_cache):
    if clear_cache:
        SLSParser.clean_cache(None)
    _run_show_stage_steps(stage_name, not no_cache)


def main():
    """
    CLI main function
    """
    cli.add_command(monitor)
    cli.add_command(stage)
    stage.add_command(stage_show)
    cli()
