# -*- coding: utf-8 -*-
# pylint: disable=too-many-branches,too-many-statements
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

import pkg_resources
import click

from .config import Config
from .common import PrettyPrinter as PP, PrettyFormat as PF
from .common import requires_root_privileges, clean_pyc_files
from .monitor import Monitor
from .monitors.terminal_outputter import StepListPrinter, SimplePrinter
from .stage_executor import run_stage
from .stage_parser import SLSParser, SaltRunner, SaltState, SaltStateFunction, \
                          SaltExecutionFunction, StageRenderingException, \
                          StateRenderingException


def _setup_logging():
    """
    Logging configuration
    """
    if Config.LOG_LEVEL == "silent":
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
                'level': Config.LOG_LEVEL.upper(),
                'filename': Config.LOG_FILE_PATH,
                'class': 'logging.FileHandler',
                'formatter': 'standard'
            },
        },
        'loggers': {
            '': {
                'handlers': ['file'],
                'level': Config.LOG_LEVEL.upper(),
                'propagate': True,
            }
        }
    })


def _run_monitor(show_state_steps, show_dynamic_steps, simple_output):
    """
    Run the DeepSea stage monitor and progress visualizer
    """
    mon = Monitor(show_state_steps, show_dynamic_steps)
    listener = SimplePrinter() if simple_output else StepListPrinter()
    mon.add_listener(listener)

    logger = logging.getLogger(__name__)

    # pylint: disable=W0613
    def sigint_handler(*args):
        """
        SIGINT signal handler
        """
        logger.debug("SIGINT, calling monitor.stop()")
        if not simple_output:
            PP.pl_bold("\x1b[2K\rShutting down...")
        else:
            PP.println("Shutting down...")
        PP.println()
        mon.stop()

    signal.signal(signal.SIGINT, sigint_handler)

    if not simple_output:
        os.system('clear')
        PP.println("Use Ctrl+C to stop the monitor")
        PP.p_bold("Initializing DeepSea progess monitor...")
    else:
        PP.println("Use Ctrl+C to stop the monitor")
        PP.print("Initializing DeepSea progess monitor...")

    mon.start()
    if not simple_output:
        PP.pl_bold(" done.")
    else:
        PP.println(" done")

    PP.println()
    if sys.version_info > (3, 0):
        logger.debug("Python 3: blocking main thread on join()")
        mon.wait_to_finish()
    else:
        logger.debug("Python 2: polling for monitor.is_running() %s", mon.is_running())
        while mon.is_running():
            time.sleep(2)
        mon.wait_to_finish()


def _validate_stage_file_exists(stage_name):
    """
    Verifies if the stage file corresponding to the stage_name arg really exists
    """
    # check if stage exists
    stage_file = "/srv/salt/{}".format(stage_name.replace('.', '/'))
    if not os.path.exists(stage_file) and not os.path.exists("{}.sls".format(stage_file)):
        PP.println("{}: Stage {} does not exist".format(PP.red("ERROR"),
                                                        PP.cyan(stage_name)))
        sys.exit(1)


def _print_deps(step, indent, step_order_map):
    if step.on_success_deps or step.on_fail_deps:
        if step.on_success_deps:
            PP.print("{}".format(" " * indent))
            deps = [step_order_map[id(s)] for s in step.on_success_deps]
            deps.sort()
            PP.print(PP.dark_yellow("if_success=[{}] ".format(", ".join(deps))))
        if step.on_fail_deps:
            PP.print("{}".format(" " * indent))
            deps = [step_order_map[id(s)] for s in step.on_fail_deps]
            deps.sort()
            PP.println(PP.dark_yellow("if_fail=[{}]".format(", ".join(deps))))
        else:
            PP.println()


def _print_stage_step(step, indent, step_order_map):
    if isinstance(step, SaltState):
        PP.print(PP.orange(step.sls_str))
        PP.print(PP.dark_green(" ({})".format(step.desc)))
        PP.println(PP.orange(" on"))
        _print_deps(step, indent, step_order_map)

        for minion in step.target:
            PP.print("{}".format(" " * indent))
            PP.println(PP.cyan(minion))
            step_count = 1
            for s_step in step.steps[minion]:
                PP.print("{}|_ ".format(" " * (indent + 2)))
                if s_step.visible:
                    PP.print(PP.green("+ "))
                else:
                    PP.print(PP.red("- "))
                PP.print(PP.bold("{:3} ".format("{}.".format(step_count))))
                step_order_map[id(s_step)] = str(step_count)
                _print_stage_step(s_step, indent + 11, step_order_map)
                step_count += 1

    elif isinstance(step, SaltRunner):
        PP.print(PP.blue(step.function))
        PP.println(PP.dark_green(" ({})".format(step.desc)))
        _print_deps(step, indent, step_order_map)

    elif isinstance(step, (SaltStateFunction, SaltExecutionFunction)):
        PP.print(PP.grey(step.function))
        if step.args:
            args_str = ", ".join(step.args)
            if len(args_str) > 60:
                args_str = args_str.replace("\n", "\\n")
                args_str = args_str[:57] + "..."
            PP.print(PP.grey("({})".format(args_str)))
        if indent == 10:
            PP.print(PP.dark_green(" ({})".format(step.desc)))
            if step.target:
                PP.print(PP.grey(" on "))
                if isinstance(step.target, list):
                    PP.print(PP.cyan(", ".join(step.target)))
                else:
                    PP.print(PP.cyan(step.target))
        PP.println()
        _print_deps(step, indent, step_order_map)


def _run_show_stage_steps(stage_name, hide_state_steps, only_visible_steps):
    """
    Runs stage parser and prints the list of steps
    """
    _validate_stage_file_exists(stage_name)

    PP.print(PP.dark_yellow("Parsing {} steps... ".format(stage_name)))
    PP.flush()
    t0 = time.time()

    try:
        steps, _ = SLSParser.parse_stage(stage_name, hide_state_steps,
                                         only_visible_steps)
    except StageRenderingException as ex:
        PP.println(PF.FAIL)
        PP.println()
        PP.println(PP.bold("An error occurred while rendering stage: {}"
                           .format(ex.stage_name)))
        for error in ex.error_list:
            PP.println(PP.red("  - {}".format(error)))
        PP.println()
        return
    except StateRenderingException as ex:
        PP.println(PF.FAIL)
        PP.println()
        PP.println(PP.bold("An error occurred while rendering state: {}"
                           .format(ex.state)))
        for error in ex.error_list:
            PP.println(PP.red("  - {}".format(error)))
        PP.println()
        return

    t1 = time.time()
    lat = t1 - t0
    if lat > 0:
        lat = "{}s".format(round(lat, 1))
    else:
        lat = "{}ms".format(round(lat * 1000, 0))
    PP.print(PF.OK)
    PP.println(" ({})".format(lat))
    PP.println()

    state_count = 1
    state_total = len(steps)
    step_order_map = {}
    for step in steps:
        step_order = "[{}/{}]".format(state_count, state_total)
        step_order = "{:10}".format(step_order)
        PP.print(PP.bold(step_order))
        _print_stage_step(step, 10, step_order_map)
        PP.println()
        step_order_map[id(step)] = str(state_count)
        state_count += 1

    PP.println(PP.bold("Additional information:"))
    PP.println("({}): visible steps (fire_event=True)".format(PP.green("+")))
    PP.println("({}): invisible steps (fire_event=False)".format(PP.red("-")))
    PP.println()


@click.group(name="deepsea")
@click.option('-l', '--log-level', default='info',
              type=click.Choice(["info", "error", "debug", "silent"]),
              help="set log level (default: info)")
@click.option('--log-file', default='/var/log/deepsea.log',
              type=click.Path(dir_okay=False),
              help="the file path for the log to be stored (default: /var/log/deepsea.log)")
@click.version_option(pkg_resources.get_distribution('deepsea'), message="%(version)s")
def cli(log_level, log_file):
    """
    DeepSea CLI tool.

    Use this tool to visualize the execution progress of DeepSea, either by
    running the stages directly through "stage run" command, or by monitoring
    the salt-run execution using the "monitor" command.
    """
    Config.LOG_LEVEL = log_level
    Config.LOG_FILE_PATH = log_file


@click.command(name='monitor')
@click.option('--show-state-steps', is_flag=True, help="shows state visible steps progress")
@click.option('--show-dynamic-steps', is_flag=True, help="shows runtime generated steps")
@click.option('--simple-output', is_flag=True, help="minimalistic b&w output")
@requires_root_privileges
def monitor(show_state_steps, show_dynamic_steps, simple_output):
    """
    Starts DeepSea progress monitor.

    This allows to visualize DeepSea execution progress when running DS stages
    using salt-run commands in other terminal sessions.
    """
    _setup_logging()
    _run_monitor(show_state_steps, show_dynamic_steps, simple_output)


@click.group(short_help='stage related commands')
def stage():
    """
    CLI 'stage' group command
    """
    pass


@click.command(name='dry-run', short_help='show DeepSea stage steps')
@click.argument('stage_name', 'the DeepSea stage name')
@click.option('--hide-state-steps', is_flag=True,
              help="this will disable state files steps from being parsed")
@click.option('--only-visible-steps', is_flag=True,
              help="only show the steps that will generate events in the Salt Event Bus")
@click.option('--clear-cache', is_flag=True, help="clear steps cache")
@requires_root_privileges
def stage_dryrun(stage_name, hide_state_steps, only_visible_steps, clear_cache):
    """
    CLI 'stage dry-run' command
    """
    clean_pyc_files()
    _setup_logging()
    if clear_cache:
        SLSParser.clean_cache(None)
    _run_show_stage_steps(stage_name, hide_state_steps, only_visible_steps)


@click.command(name='run', short_help='runs DeepSea stage')
@click.argument('stage_name', 'the DeepSea stage name')
@click.option('--hide-state-steps', is_flag=True, help="shows state visible steps progress")
@click.option('--hide-dynamic-steps', is_flag=True, help="shows runtime generated steps")
@click.option('--simple-output', is_flag=True, help="minimalistic b&w output")
@requires_root_privileges
def stage_run(stage_name, hide_state_steps, hide_dynamic_steps, simple_output):
    """
    Runs a DeepSea stage

    This command is equivalent to run:

        $ salt-run state.orch <stage_name>
    """
    clean_pyc_files()
    _setup_logging()
    _validate_stage_file_exists(stage_name)

    ret = run_stage(stage_name, hide_state_steps, hide_dynamic_steps, simple_output)
    PP.flush()
    sys.exit(ret)


@click.group(name='salt-run')
def salt_run():
    """
    stage command alias
    """
    pass


@click.command(name='state.orch')
@click.argument('stage_name', 'the DeepSea stage name')
@click.option('--hide-state-steps', is_flag=True, help="shows state visible steps progress")
@click.option('--hide-dynamic-steps', is_flag=True, help="shows runtime generated steps")
@click.option('--simple-output', is_flag=True, help="minimalistic b&w output")
@requires_root_privileges
def state_orch(stage_name, hide_state_steps, hide_dynamic_steps, simple_output):
    """
    Runs a DeepSea stage

    This command is equivalent to run:

        $ salt-run state.orch <stage_name>
    """
    _setup_logging()
    _validate_stage_file_exists(stage_name)

    ret = run_stage(stage_name, hide_state_steps, hide_dynamic_steps, simple_output)
    sys.exit(ret)


def main():
    """
    CLI main function
    """
    cli.add_command(monitor)
    cli.add_command(stage)
    cli.add_command(salt_run)
    stage.add_command(stage_dryrun)
    stage.add_command(stage_run)
    salt_run.add_command(state_orch)
    # pylint: disable=E1120,E1123
    cli(prog_name='deepsea')
