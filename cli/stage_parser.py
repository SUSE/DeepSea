# -*- coding: utf-8 -*-
"""
This module is responsible for the parsing of DeepSea stage files
"""
from __future__ import absolute_import
from __future__ import print_function

import logging
import os
import pwd
import time

from collections import defaultdict
from io import StringIO
from multiprocessing import Process, Queue

import salt.client
import salt.minion
import salt.exceptions

from .common import redirect_output


# pylint: disable=C0103
logger = logging.getLogger(__name__)


class OrchestrationNotFound(Exception):
    """
    No orchestration file found exception
    """
    pass


class RenderingException(Exception):
    """
    Exception class that represents a rendering error
    """
    def __init__(self, error_list):
        super(RenderingException, self).__init__(error_list)
        self.error_list = error_list

    def pretty_error_desc_str(self):
        """
        Returns a more user-friendly message of the exception
        """
        errors = []
        for error_desc in self.error_list:
            idx = error_desc.find("SaltRenderError:")
            if idx != -1:
                # SaltRenderError exception, we may remove the stack trace, only
                # the syntax error description is usefull.
                errors.append(error_desc[idx:])
            else:
                errors.append(error_desc)
        res = ""
        for error in self.error_list:
            res += "  - {}\n".format(error.replace("\n", "\n    "))
        return res


class StateRenderingException(RenderingException):
    """
    Exception class that represents a state rendering error
    """
    def __init__(self, minion, state, error_list):
        super(StateRenderingException, self).__init__(error_list)
        self.minion = minion
        self.state = state


class StageRenderingException(RenderingException):
    """
    Exception class that represents a stage rendering error
    """
    def __init__(self, stage_name, error_list):
        super(StageRenderingException, self).__init__(error_list)
        self.stage_name = stage_name


class SaltClient(object):
    _OPTS_ = None
    _CALLER_ = None
    _LOCAL_ = None
    _MASTER_ = None

    @classmethod
    def _opts(cls):
        """
        Initializes and retrieves the Salt opts structure
        """
        if cls._OPTS_ is None:
            cls._OPTS_ = salt.config.minion_config('/etc/salt/minion')
        return cls._OPTS_

    @classmethod
    def caller(cls):
        """
        Initializes and retrieves the Salt caller client instance
        """
        if cls._CALLER_ is None:
            cls._CALLER_ = salt.client.Caller(mopts=cls._opts())
        return cls._CALLER_

    @classmethod
    def local(cls):
        """
        Initializes and retrieves the Salt local client instance
        """
        if cls._LOCAL_ is None:
            cls._LOCAL_ = salt.client.LocalClient()
        return cls._LOCAL_

    @classmethod
    def master(cls):
        if cls._MASTER_ is None:
            _opts = salt.config.master_config('/etc/salt/master')
            _opts['file_client'] = 'local'
            cls._MASTER_ = salt.minion.MasterMinion(_opts)
        return cls._MASTER_


class SLSRenderer(object):
    """
    Helper class to render sls files
    """

    @classmethod
    def render(cls, state_name, target=None):
        """
        This function makes use of state.show_low_sls to render sls files
        Args:
            state_name (str): the salt state name (can be an orchestrator state)
        """
        if target:
            return cls._render_in_minion(state_name, target)

        return cls._render_in_master(state_name)

    @classmethod
    def _render_in_minion(cls, state_name, target, retry=True):
        logger.info("Rendering states=%s on=%s", state_name, target)
        err = StringIO()
        out = StringIO()

        out2 = None
        err2 = None
        with redirect_output(out, err):
            if isinstance(state_name, str):
                state_name = [state_name]

            res = SaltClient.local().cmd(target, 'deepsea.show_low_sls',
                                         state_name, tgt_type="compound")

            logger.debug("Rendering result: %s", res)
            for minion, states in res.items():
                if isinstance(states, str):
                    logger.info("call to deepsea module returned: %s", states)
                    if states.endswith("is not available."):
                        if not retry:
                            res = StateRenderingException(
                                minion, None,
                                ['deepsea module not available'])
                            break

                        logger.info("deepsea module not available: syncing "
                                    "modules")
                        SaltClient.local().cmd(target, 'saltutil.sync_modules',
                                               [], tgt_type="compound")
                        res, out2, err2 = cls._render_in_minion(state_name,
                                                                target, False)
                else:
                    for state, steps in states.items():
                        if steps and isinstance(steps[0], str):
                            res = StateRenderingException(minion, state, steps)

        if isinstance(res, RenderingException):
            # pylint: disable=E0702
            raise res
        if out2 is not None and err is not None:
            out_str = out2
            err_str = err2
        else:
            out_str = out.getvalue()
            err_str = err.getvalue()
            logger.debug("OUT:\n%s", out.getvalue())
            logger.debug("ERR:\n%s", err.getvalue())

        out.close()
        err.close()
        return res, out_str, err_str

    @classmethod
    def _render_in_master(cls, state_name):
        logger.info("Rendering state=%s on=master", state_name)

        def subproc_fun(queue):
            """
            Subprocess wrapper function. This function will be executed by a child process,
            and run the stage parsing as the "salt" user.
            """
            # changing process user to "salt" so that any runner side-effects during SLS rendering
            # are done with salt user as owner
            pw = pwd.getpwnam("salt")
            os.setgid(pw.pw_gid)
            os.setuid(pw.pw_uid)

            err = StringIO()
            out = StringIO()
            with redirect_output(out, err):
                res = SaltClient.master().functions['state.show_low_sls'](
                    state_name)

            queue.put(res)
            queue.put(out.getvalue())
            queue.put(err.getvalue())
            out.close()
            err.close()

        queue = Queue()
        p = Process(target=subproc_fun, args=[queue])
        p.start()
        p.join()
        res = queue.get()
        out = queue.get()
        err = queue.get()

        logger.debug("Rendering result: %s", res)
        if res and isinstance(res[0], str):  # exception case
            res = StageRenderingException(state_name, res)

        if isinstance(res, RenderingException):
            raise res

        logger.debug("OUT:\n%s", out)
        logger.debug("ERR:\n%s", err)

        return res, out, err


class SLSParser(object):
    """
    SLS files parser
    """

    @classmethod
    def parse_step(cls, step_dict, target=None):
        logger.debug("parsing step [%s] %s", target, step_dict)
        if step_dict['state'] == 'salt' and step_dict['fun'] == 'state':
            return SaltState(step_dict)
        if step_dict['state'] == 'salt' and step_dict['fun'] == 'runner':
            return SaltRunner(step_dict)
        if step_dict['state'] == 'salt' and step_dict['fun'] == 'function':
            return SaltExecutionFunction(step_dict, step_dict['tgt'])
        if step_dict['state'] == 'module' and step_dict['fun'] == 'run':
            return SaltExecutionFunction(step_dict, target)
        return SaltStateFunction(step_dict, target)

    @staticmethod
    def notify_listener(listeners, states, minion=None):
        for l in listeners:
            l.stage_parsing_state(states, minion)

    @classmethod
    def parse_stage(cls, stage_name, hide_state_steps, only_visible_steps,
                    monitor_listeners=None):
        if monitor_listeners is None:
            monitor_listeners = []

        steps = []
        t0 = time.time()
        SLSParser.notify_listener(monitor_listeners, [stage_name])
        stage, out, _ = SLSRenderer.render(stage_name)
        t1 = time.time()
        logger.info("parsing stage sls file took: %ss", t1-t0)
        for step_dict in stage:
            step = cls.parse_step(step_dict)
            steps.append(step)

        if hide_state_steps:
            steps = cls._process_states_requisites(stage_name, steps)
            steps = cls._reorder(stage_name, steps)
            return steps, out

        states_to_render = defaultdict(set)
        for step in [s for s in steps if isinstance(s, SaltState)]:
            if step.sls:
                states_to_render[step.target[0]].add(step.sls)

        t0 = time.time()
        states_rendering = defaultdict(lambda: defaultdict(
            lambda: defaultdict(dict)))
        for target, states in states_to_render.items():
            SLSParser.notify_listener(monitor_listeners, states, target)
            res, _, _ = SLSRenderer.render(list(states), target)
            for minion, state_res in res.items():
                if isinstance(state_res, list):
                    assert len(states) == 1
                    state_res = {list(states)[0]: state_res}
                for state_name, state_steps in state_res.items():
                    states_rendering[target][state_name][minion] = state_steps
        t1 = time.time()
        logger.info("parsing stage states sls files took: %ss", t1-t0)

        for step in [s for s in steps if isinstance(s, SaltState)]:
            for minion, state_steps in states_rendering[step.target[0]][step.sls].items():
                step.target_expanded.append(minion)
                for s_step_dict in state_steps:
                    s_step = cls.parse_step(s_step_dict, minion)
                    if not only_visible_steps or s_step.visible:
                        step.steps[minion].append(s_step)

        steps = cls._process_states_requisites(stage_name, steps)
        steps = cls._reorder(stage_name, steps)

        return steps

    @classmethod
    def _search_step(cls, steps, state, sid):
        """
        Searches a step that matches the module name and state id
        Args:
            steps (list): list of steps
            mod_name (str): salt module name, can be None
            sid (str): state id
        """
        for step in steps:
            if state is None or step.state == state:
                if step.get_arg('name') == sid or step.desc == sid:
                    return step

        return None

    @classmethod
    def _process_states_requisites(cls, stage_name, steps):
        def process_requisite_directive(step, directive):
            """
            Processes a requisite directive
            """
            reqs = step.get_arg(directive)
            if not reqs:
                return

            reqs_t = []
            for req in reqs:
                if isinstance(req, str):
                    reqs_t.append((None, req))
                else:
                    reqs_t.extend([(k, v) for k, v in req.items()])

            for mod, sid in reqs_t:
                logger.debug("searching for state=%s desc/name=%s", mod, sid)
                req_step = cls._search_step(steps, mod, sid)
                logger.debug("found state dependency from: %s to: %s", step,
                             req_step)
                assert req_step
                if directive in ['require', 'watch', 'onchanges']:
                    step.on_success_deps.append(req_step)
                elif directive == 'onfail':
                    step.on_fail_deps.append(req_step)

        # process state requisites
        for step in steps:
            for directive in ['require', 'watch', 'onchanges', 'onfail']:
                process_requisite_directive(step, directive)
            if isinstance(step, SaltState):
                for _, s_steps in step.steps.items():
                    cls._process_states_requisites(stage_name, s_steps)

        return steps

    @classmethod
    def _reorder(cls, stage_name, steps):
        def all_deps_available(p_nsteps, p_deps):
            for p_dep in p_deps:
                if p_dep not in p_nsteps:
                    return False
            return True

        nsteps = []
        prev_len = len(steps)
        while steps:
            for idx, step in enumerate(steps):
                deps = list(step.on_success_deps)
                deps.extend(step.on_fail_deps)
                if all_deps_available(nsteps, deps):
                    nsteps.append(step)
                    steps.pop(idx)
                    break

            if len(steps) == prev_len:
                raise StageRenderingException(stage_name,
                                              ["Recursive requisite found"])
            prev_len = len(steps)

        return nsteps


class SaltStep(object):
    """
    Base class to represent a single stage step
    """
    def __init__(self, step_dict):
        self.step_dict = step_dict
        self.on_success_deps = []
        self.on_fail_deps = []

    @property
    def desc(self):
        return self.step_dict['__id__']

    def __str__(self):
        return self.desc

    def __repr__(self):
        return str(self.step_dict)

    @property
    def state(self):
        return self.step_dict['state']

    def get_arg(self, key):
        """
        Returns the arg value for the key
        """
        if key in self.step_dict:
            return self.step_dict[key]
        return None

    def pretty_string(self):
        """
        Returns a user-readable string representation of this step
        """
        pass


class SaltState(SaltStep):
    """
    Class to represent a Salt state apply step
    """
    def __init__(self, step_dict):
        super(SaltState, self).__init__(step_dict)
        self.target_expanded = []
        self.steps = defaultdict(list)

    @property
    def sls(self):
        if 'sls' not in self.step_dict:
            return None
        return self.step_dict['sls']

    @property
    def target(self):
        if self.target_expanded:
            return self.target_expanded
        return [self.step_dict['tgt']]

    def isTargetExpanded(self):
        return len(self.target_expanded) > 0

    def __str__(self):
        return "SaltState(desc: {}, sls: {}, target: {})" \
                .format(self.desc, self.sls, self.target)


class SaltRunner(SaltStep):
    """
    Class to represent a Salt runner step
    """

    @property
    def function(self):
        return self.step_dict['name']

    def __str__(self):
        return "SaltRunner(desc: {}, fun: {})".format(self.desc, self.function)


class SaltTargettedStep(SaltStep):
    """
    Class to represent Salt steps that target a specific minion
    """
    def __init__(self, step_dict, target):
        super(SaltTargettedStep, self).__init__(step_dict)
        self.target = target

    def isTargetExpanded(self):
        return False

    @property
    def visible(self):
        if 'fire_event' in self.step_dict:
            return self.step_dict['fire_event']
        return False


class SaltStateFunction(SaltTargettedStep):
    """
    Class to represent a Salt state function
    """
    @property
    def function(self):
        return self.step_dict['state'] + "." + self.step_dict['fun']

    @property
    def args(self):
        if self.function == 'pkg.installed':
            if 'pkgs' in self.step_dict:
                return self.step_dict['pkgs']
        if 'name' in self.step_dict:
            return [self.step_dict['name']]
        return []

    def __str__(self):
        return "SaltStateFunc(desc: {}, fun: {}, args: {}, target={})" \
                .format(self.desc, self.function, self.args, self.target)

    def pretty_string(self):
        if self.args:
            return "{}({})".format(self.function, ", ".join(self.args))
        return self.function


class SaltExecutionFunction(SaltTargettedStep):
    """
    Class to represent a Salt module.run step
    """
    @property
    def function(self):
        return self.step_dict['name']

    @property
    def args(self):
        args = []
        if 'm_name' in self.step_dict:
            args.append(self.step_dict['m_name'])
        elif 'arg' in self.step_dict:
            args.extend(self.step_dict['arg'])
        if 'kwargs' in self.step_dict:
            for k, v in self.step_dict['kwargs'].items():
                args.append("{}={}".format(k, v))
        return args

    def __str__(self):
        return "SaltExecFunc(desc: {}, fun: {}, args: {}, target: {})" \
                .format(self.desc, self.function, self.args, self.target)

    def pretty_string(self):
        if self.args:
            return "{}({})".format(self.function, ", ".join(self.args))
        return self.function
