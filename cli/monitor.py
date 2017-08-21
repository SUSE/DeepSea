# -*- coding: utf-8 -*-
"""
DeepSea stage's progress monitor
"""
from __future__ import absolute_import
from __future__ import print_function

import json
import logging
import os

from subprocess import Popen, PIPE

from .saltevent import SaltEventProcessor, EventListener


logger = logging.getLogger(__name__)


class StageParser(object):
    """
    Parses stage state files.
    """
    def __init__(self, stage_name):
        self._stage_name = stage_name
        self._base_dir = '/srv/salt'
        self._sls_file = None
        self._subfiles = []
        self.find_file()
        self.resolve_deps()

    def find_file(self, start_dir='/srv/salt'):
        def walk_dirs(start_dir):
            for root, dirs, files in os.walk(start_dir):
                for _dir in dirs:
                    if _dir in sub_name:
                        return _dir

        logger.debug("stage name: {}".format(self._stage_name))
        init_dir = start_dir
        for sub_name in self._stage_name.split('.'):
            logger.debug("Scanning dirs for {}".format(sub_name))
            new_sub_dir = walk_dirs(init_dir)
            logger.debug("Found sub directory: {}".format(new_sub_dir))
            init_dir = init_dir + "/" + new_sub_dir

        self._sls_file = init_dir + "/default.sls"
        return self._sls_file

    def resolve_deps(self):
        substages = []

        def find_includes(content):
            includes = []
            if 'include' in content:
                includes = [str(inc) for inc in content['include']]
            return includes

        content = self._get_rendered_stage(self._sls_file)
        includes = find_includes(content)
        for inc in includes:
            dot_count = inc.count('.')
            inc = inc.replace('.', '')
            if dot_count == 1:
                stage_name = self._stage_name
            elif dot_count > 1:
                # The it's not ceph.stage.4.iscsi but ceph.stage.iscsi if
                # the include has two dots (..) in it.
                stage_name = ".".join(
                    self._stage_name.split('.')[:-(dot_count - 1)])

            tmp_stage_name = self._stage_name
            self._stage_name = stage_name + "." + inc
            self._subfiles.append(self.find_file())
            # TODO: instead of temping back and forth, refactor to use params
            self._stage_name = tmp_stage_name
        if not self._subfiles:
            self._subfiles.append(self._sls_file)

    def _get_rendered_stage(self, file_name):
        """
        Importing salt.modules.renderer unfortunately does not work as this script is not
        executed within the salt context and therefore lacking the __salt__ and __opts__
        variables.
        """
        cmd = "salt --out=json --static -C \"I@roles:master\" slsutil.renderer {}".format(
            file_name)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = proc.communicate()
        if not stderr:
            # add checks
            return json.loads(stdout).values()[0]

    @property
    def expected_steps(self):
        """
        Currently only states
        """
        states = {}
        logger.debug(
            "Started scraping states from SLS Files: {}".format(self._subfiles))
        for sls in self._subfiles:
            content = self._get_rendered_stage(sls)
            content.pop("retcode")
            if 'include' in content:
                continue
            for stanza, descr in content.iteritems():
                if str(descr) == 'test.nop':
                    continue
                for _type, _info in descr.iteritems():
                    if str(_type) == 'salt.state':
                        for _data in _info:
                            # import pdb;pdb.set_trace()
                            if unicode('sls') in _data:
                                try:
                                    states.update(
                                        {str(_data.values()[0]): str(_info[0][unicode('tgt')])})
                                except:
                                    logger.info("No tgt found")
        logger.debug("Found states for orchestration: {} \n {}".format(
            self._stage_name, states))
        return states


class Stage(object):
    """
    Class to represent a DeepSea stage execution
    """
    def __init__(self, name, jid):
        self.name = name
        self.jid = jid
        self.running = True

    def finish(self):
        """
        Sets this stage has finished
        """
        self.running = False


class Monitor(object):
    """
    Stage monitoring class
    """

    class DeepSeaEventListener(EventListener):
        """
        Salt event listener for DeepSea
        """
        def __init__(self, monitor):
            self.monitor = monitor

        def handle_new_runner_event(self, event):
            if event.fun == 'runner.state.orch':
                if event.args and event.args[0].startswith('ceph.stage.'):
                    self.monitor.start_stage(event)

        def handle_ret_runner_event(self, event):
            if event.fun == 'runner.state.orch':
                if event.args and event.args[0].startswith('ceph.stage.'):
                    self.monitor.end_stage(event)

    def __init__(self):
        self._processor = SaltEventProcessor()
        self._processor.add_listener(Monitor.DeepSeaEventListener(self))

        self._running_stage = None

    def start_stage(self, event):
        """
        Sets the current running stage
        Args:
            event (NewRunnerEvent): the DeepSea state.orch start event
        """
        self._running_stage = Stage(event.args[0], event.jid)
        logger.info("Start stage: %s jid=%s", self._running_stage.name, self._running_stage.jid)

        parser = StageParser(self._running_stage.name)
        print("Start stage -> {}".format(self._running_stage.name))
        print(parser.expected_steps)

    def end_stage(self, event):
        """
        Sets the current running stage as finished
        Args:
            event (RetRunnerEvent): the DeepSear state.orch end event
        """
        self._running_stage.finish()
        logger.info("End stage: %s jid=%s success=%s", self._running_stage.name, self._running_stage.jid,
                    event.success)
        print("Finish stage -> {} -> {}".format(self._running_stage.name, event.success))
        self._running_stage = None

    def start(self):
        """
        Start the monitoring thread
        """
        self._processor.start()

    def stop(self):
        """
        Stop the monitoring thread
        """
        self._processor.stop()
