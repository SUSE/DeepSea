# -*- coding: utf-8 -*-
"""
This module is responsible for the parsing of DeepSea stage files
"""
from __future__ import absolute_import
from __future__ import print_function

import glob
import logging
import os
import pickle
import StringIO

from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor

import salt.client

from .common import redirect_stdout, redirect_stderr


# pylint: disable=C0103
logger = logging.getLogger(__name__)


__opts__ = salt.config.minion_config('/etc/salt/minion')
__opts__['file_client'] = 'local'
__caller__ = salt.client.Caller(mopts=__opts__)
__local__ = salt.client.LocalClient()


class OrchestrationNotFound(Exception):
    """
    No orchestration file found exception
    """
    pass


executor = ThreadPoolExecutor(max_workers=5)


class SLSRenderer(object):
    """
    Helper class to render sls files
    """

    @staticmethod
    def render(file_name):
        """
        This function makes use of slsutil salt module to render sls files
        Args:
            file_name (str): the sls file path
        """
        err = StringIO.StringIO()
        out = StringIO.StringIO()
        with redirect_stderr(err):
            with redirect_stdout(out):
                result = __caller__.cmd('slsutil.renderer', file_name)
        logger.info("Rendered SLS file %s, stdout\n%s", file_name, out.getvalue())
        logger.debug("Rendered SLS file %s, stderr\n%s", file_name, err.getvalue())
        return result, out.getvalue(), err.getvalue()

    @staticmethod
    def _deserialize_ordered_dict(udict):
        """
        Constructs an OrdereredDict from a standard python dictionary
        """
        if not isinstance(udict, dict) and not isinstance(udict, list):
            return udict

        if isinstance(udict, list):
            return [SLSRenderer._deserialize_ordered_dict(e) for e in udict]

        result = OrderedDict()
        kv_array = [(key, val) for key, val in udict.items()]
        kv_array.sort(key=lambda (_, val): val['__order__'])
        for key, val in kv_array:
            result[key] = SLSRenderer._deserialize_ordered_dict(val['__val__'])
        return result

    @staticmethod
    def render_state(state_name, target):
        """
        This function makes use of slsutil salt module to render sls files in the target minions
        Args:
            file_name (str): the sls file path
            target (str): the minion id
        """
        result = __local__.cmd(target, 'deepsea.render_sls', [state_name], expr_form="compound")
        nres = {}
        for key, val in result.items():
            nres[key] = SLSRenderer._deserialize_ordered_dict(val)
        logger.info("Rendered state %s for minions=%s", state_name, nres.keys())
        return nres

    @staticmethod
    def render_states(target_states):
        """
        This function makes use of slsutil salt module to render state sls in the target minions
        Args:
            target_states (dict): dictionary where key is the minion target and value the
                                  list of states
        """
        result = {}
        for target, states in target_states.items():
            logger.info("Rendering states=%s on=%s", states, target)
            out = __local__.cmd(target, 'deepsea.render_sls', [states], expr_form="compound")
            for key, val in out.items():
                if isinstance(val, str):
                    logger.info("call to deepsea module returned: %s", val)
                    if val.endswith("is not available."):
                        logger.info("deepsea module not available: syncing modules")
                        __local__.cmd(target, 'saltutil.sync_modules', [], expr_form="compound")
                        return SLSRenderer.render_states(target_states)
                for state_name, content in val.items():
                    if state_name not in result:
                        result[state_name] = {}
                    result[state_name][key] = SLSRenderer._deserialize_ordered_dict(content)
        for key, val in result.items():
            logger.info("Rendered state %s for minions=%s", key, val.keys())
        return result

    @staticmethod
    def async_render(file_name):
        """
        Asynchronous version of SLSRenderer.render function

        Returns Future
        """
        return executor.submit(SLSRenderer.render, file_name)


class SLSParser(object):
    """
    SLS files parser
    """

    _CACHE_FILE_PREFIX_ = "_deepsea"
    _CACHE_DIR_PATH_ = "/tmp"

    @staticmethod
    def _state_name_is_dir(state_name):
        """
        Checks wheather a state_name corresponds to a directory in the filesystem.
        """
        path = "/srv/salt/{}".format(state_name.replace(".", "/"))
        return os.path.isdir(path)

    @staticmethod
    def _state_file_path(state_name):
        """
        Returns the filesystem path of a state file
        Args:
            state_name (str): the salt state name
        """
        if SLSParser._state_name_is_dir(state_name):
            path = "/srv/salt/{}/init.sls".format(state_name.replace(".", "/"))
        else:
            path = "/srv/salt/{}.sls".format(state_name.replace(".", "/"))

        if not os.path.exists(path):
            raise OrchestrationNotFound("could not determine path for {}"
                                        .format(state_name))

        return path

    @staticmethod
    def _gen_state_name_from_include(parent_state, include):
        """
        Generates the salt state name from a state include path.
        Example:
        ceph.stage.4 state contents:

        .. code-block:: yaml
            include:
              - ..iscsi

        The state name generated by this include will be:
        ceph.stage.iscsi
        """
        # counting dots
        dot_count = 0
        for c in include:
            if c == '.':
                dot_count += 1
            else:
                break
        include = include[dot_count:]
        if not SLSParser._state_name_is_dir(parent_state):
            # we need to remove the "file_name" part of the parent state name
            dot_count += 1
        if dot_count > 1:
            # The state it's not ceph.stage.4.iscsi but ceph.stage.iscsi if
            # the include has two dots (..) in it.
            parent_state = ".".join(parent_state.split('.')[:-(dot_count - 1)])

        return "{}.{}".format(parent_state, include)

    @staticmethod
    def _traverse_state_dict(state_dict, minion, only_visible_steps):
        """
        Parses the all steps (actions) triggered by the execution of a state file.
        It recursevely follows "include" directives, and state files.
        Args:
            state_name (str): the salt state name, e.g., ceph.stage.1
            only_visible_steps (bool): wheather to parse state declarations that have
                                       fire_event=True
            cache (bool): wheather load/store the results in a cache file

        Returns:
            list(StepType): a list of steps
        """
        result = []
        if not state_dict:
            return result
        for key, steps in state_dict.items():
            if isinstance(steps, dict):
                for fun, args in steps.items():
                    logger.debug("Parsing step: desc={} fun={} step={}"
                                 .format(key, fun, args))
                    if fun == 'module.run':
                        module = SaltModule(key, minion, args)
                        if not only_visible_steps or module.get_arg('fire_event'):
                            result.append(module)
                    else:
                        builtin = SaltBuiltIn(key, fun, minion, args)
                        if not only_visible_steps or builtin.get_arg('fire_event'):
                            result.append(builtin)

        return result

    @staticmethod
    def _traverse_state(state_name, target, only_visible_steps, cache):
        """
        Parses the all steps (actions) triggered by the execution of a state file.
        It recursevely follows "include" directives, and state files.
        Args:
            state_name (str): the salt state name, e.g., ceph.stage.1
            only_visible_steps (bool): wheather to parse state declarations that have
                                       fire_event=True
            cache (bool): wheather load/store the results in a cache file

        Returns:
            list(StepType): a list of steps
        """

        cache_file_path = '{}/{}_{}_{}_{}.bin'.format(SLSParser._CACHE_DIR_PATH_,
                                                      SLSParser._CACHE_FILE_PREFIX_,
                                                      state_name, only_visible_steps, target)
        if cache:
            if os.path.exists(cache_file_path):
                logger.info("state %s found in cache, loading from cache...", state_name)
                # pylint: disable=W8470
                with open(cache_file_path, mode='rb') as binfile:
                    return pickle.load(binfile)

        result = []
        # path = SLSParser._state_file_path(state_name)
        logger.info("Parsing state: %s", state_name)
        state_dict_minions = SLSRenderer.render_state(state_name, target)
        for minion, state_dict in state_dict_minions.items():
            for key, steps in state_dict.items():
                if isinstance(steps, dict):
                    for fun, args in steps.items():
                        logger.debug("Parsing step: desc={} fun={} step={}"
                                     .format(key, fun, args))
                        if fun == 'module.run':
                            module = SaltModule(key, minion, args)
                            if not only_visible_steps or module.get_arg('fire_event'):
                                result.append(module)
                        else:
                            builtin = SaltBuiltIn(key, fun, minion, args)
                            if not only_visible_steps or builtin.get_arg('fire_event'):
                                result.append(builtin)

        if cache:
            # pylint: disable=W8470
            with open(cache_file_path, mode='wb') as binfile:
                pickle.dump(result, binfile)

        return result

    @staticmethod
    def _traverse_stage(state_name, stages_only, only_visible_steps, cache):
        """
        Parses the all steps (actions) triggered by the execution of a state file.
        It recursevely follows "include" directives, and state files.
        Args:
            state_name (str): the salt state name, e.g., ceph.stage.1
            stages_only (bool): only parse stages sls files
            only_visible_steps (bool): wheather to parse state declarations that have
                                       fire_event=True
            cache (bool): wheather load/store the results in a cache file

        Returns:
            list(StepType): a list of steps
        """
        cache_file_path = '{}/{}_{}_{}_{}.bin'.format(SLSParser._CACHE_DIR_PATH_,
                                                      SLSParser._CACHE_FILE_PREFIX_,
                                                      stages_only, only_visible_steps,
                                                      state_name)
        if cache:
            if os.path.exists(cache_file_path):
                logger.info("state %s found in cache, loading from cache...", state_name)
                # pylint: disable=W8470
                with open(cache_file_path, mode='rb') as binfile:
                    return pickle.load(binfile)

        result = []
        path = SLSParser._state_file_path(state_name)
        logger.info("Parsing state file: %s", path)
        state_dict, out, _ = SLSRenderer.render(path)
        for key, steps in state_dict.items():
            if key == 'include':
                for inc in state_dict['include']:
                    logger.debug("Handling include of: parent={} include={}"
                                 .format(state_name, inc))
                    include_state_name = SLSParser._gen_state_name_from_include(state_name, inc)
                    sub_res, sub_out = SLSParser._traverse_stage(include_state_name, stages_only,
                                                                 only_visible_steps, cache)
                    result.extend(sub_res)
                    if sub_out:
                        out += "\n{}".format(sub_out)
            else:
                if isinstance(steps, dict):
                    for fun, args in steps.items():
                        logger.debug("Parsing step: desc={} fun={} step={}".format(key, fun, args))
                        if fun == 'salt.state':
                            state = SaltState(key, args)
                            result.append(state)
                        elif fun == 'salt.runner':
                            result.append(SaltRunner(key, args))
                        elif fun == 'module.run':
                            module = SaltModule(key, None, args)
                            module.target = module.get_arg('tgt')
                            if not only_visible_steps or module.get_arg('fire_event'):
                                result.append(module)
                        else:
                            builtin = SaltBuiltIn(key, fun, None, args)
                            builtin.target = builtin.get_arg('tgt')
                            if not only_visible_steps or builtin.get_arg('fire_event'):
                                result.append(builtin)

        if not stages_only:
            render_states = defaultdict(list)
            for state in result:
                if isinstance(state, SaltState) and not state.rendered:
                    render_states[state.target].append(state.state)

            rendered_states = SLSRenderer.render_states(render_states)
            nresult = []
            for state in result:
                nresult.append(state)
                if isinstance(state, SaltState) and not state.rendered:
                    state.rendered = True
                    for minion, state_dict in rendered_states[state.state].items():
                        nresult.extend(SLSParser._traverse_state_dict(state_dict, minion,
                                                                      only_visible_steps))
            result = nresult

        if cache:
            # pylint: disable=W8470
            with open(cache_file_path, mode='wb') as binfile:
                pickle.dump((result, out), binfile)

        return result, out

    @staticmethod
    def _search_step(steps, mod_name, sid):
        """
        Searches a step that matches the module name and state id
        Args:
            steps (list): list of steps
            mod_name (str): salt module name, can be None
            sid (str): state id
        """
        for step in steps:
            if mod_name:
                if isinstance(step, SaltRunner):
                    if mod_name != 'salt':
                        continue
                elif isinstance(step, SaltState):
                    if mod_name != 'salt':
                        continue
                else:
                    step_mod = step.fun[:step.fun.find('.')]
                    if mod_name != step_mod:
                        continue
            name_arg = step.get_arg('name')
            if step.desc == sid or (name_arg and name_arg == sid):
                return step
        return None

    @staticmethod
    def parse_state_steps(state_name, stages_only=True, only_visible_steps=True, cache=True):
        """
        Parses the all steps (actions) triggered by the execution of a state file
        Args:
            state_name (str): the salt state name, e.g., ceph.stage.1
            only_events (bool): wheather to parse state declarations that have fire_event=True
            cache (bool): wheather load/store the results in a cache file

        Returns:
            list(StepType): a list of steps
            str: the parsing stdout
        """
        result, out = SLSParser._traverse_stage(state_name, stages_only, only_visible_steps,
                                                cache)

        def process_requisite_directive(step, directive):
            """
            Processes a requisite directive
            """
            req = step.get_arg(directive)
            if req:
                if not isinstance(req, list):
                    # usually req will be a list of dicts, this is just for
                    # the case when req is not a list and maintain the same code
                    # below
                    req = [req]

                for req in req:
                    if isinstance(req, dict):
                        for mod, sid in req.items():
                            req_step = SLSParser._search_step(result, mod, sid)
                            assert req_step
                            if directive in ['require', 'watch', 'onchanges']:
                                step.on_success_deps.append(req_step)
                            elif directive == 'onfail':
                                step.on_fail_deps.append(req_step)
                    else:
                        req_step = SLSParser._search_step(result, None, req)
                        assert req_step
                        if directive in ['require', 'watch', 'onchanges']:
                            step.on_success_deps.append(req_step)
                        elif directive == 'onfail':
                            step.on_fail_deps.append(req_step)

        # process state requisites
        for step in result:
            for directive in ['require', 'watch', 'onchanges', 'onfail']:
                process_requisite_directive(step, directive)

        return result, out

    @staticmethod
    def clean_cache(state_name):
        """
        Deletes all cache files
        """
        if not state_name:
            cache_files = '{}/{}_*.bin'.format(SLSParser._CACHE_DIR_PATH_,
                                               SLSParser._CACHE_FILE_PREFIX_)
        else:
            cache_files = '{}/{}_*_{}.bin'.format(SLSParser._CACHE_DIR_PATH_,
                                                  SLSParser._CACHE_FILE_PREFIX_,
                                                  state_name)
        logger.info("cleaning cache: %s", cache_files)
        for cache_file in glob.glob(cache_files):
            os.remove(cache_file)


class SaltStep(object):
    """
    Base class to represent a single stage step
    """
    def __init__(self, desc, args):
        self.desc = desc
        self.args = args
        self.on_success_deps = []
        self.on_fail_deps = []

    def __str__(self):
        return self.desc

    def get_arg(self, key):
        """
        Returns the arg value for the key
        """
        if isinstance(self.args, dict):
            if key in self.args:
                return self.args[key]
        elif isinstance(self.args, list):
            arg = [arg for arg in self.args if key in arg]
            if arg:
                return arg[0][key]
        else:
            assert False
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
    def __init__(self, desc, args):
        super(SaltState, self).__init__(desc, args)
        self.state = self.get_arg('sls')
        if not self.state:
            self.state = self.get_arg('name')
        self.target = self.get_arg('tgt')
        self.rendered = False

    def __str__(self):
        return "SaltState(desc: {}, state: {}, target: {})".format(self.desc, self.state,
                                                                   self.target)


class SaltRunner(SaltStep):
    """
    Class to represent a Salt runner step
    """
    def __init__(self, desc, args):
        super(SaltRunner, self).__init__(desc, args)
        self.fun = self.get_arg('name')

    def __str__(self):
        return "SaltRunner(desc: {}, fun: {})".format(self.desc, self.fun)


class SaltModule(SaltStep):
    """
    Class to represent a Salt module step
    """
    def __init__(self, desc, target, args):
        super(SaltModule, self).__init__(desc, args)
        self.fun = self.get_arg('name')
        self.target = target

    def pretty_string(self):
        def process_args(args):
            """
            Auxiliary function
            """
            arg_list = ""
            first = True
            for val in args:
                if not val:
                    continue
                if isinstance(val, dict):
                    for key2, val2 in val.items():
                        if first:
                            arg_list += "{}={}".format(key2, val2)
                            first = False
                        else:
                            arg_list += ", {}={}".format(key2, val2)
                else:
                    if first:
                        arg_list += val
                        first = False
                    else:
                        arg_list += ", {}".format(val)
            return arg_list

        arg_list = process_args([self.get_arg(key) for key in ['pkg', 'pkgs', 'kwargs']])

        if arg_list:
            return "{}({})".format(self.fun, arg_list)
        else:
            return "{}: {}".format(self.desc, self.fun)

    def __str__(self):
        return "SaltModule(desc: {}, fun: {})".format(self.desc, self.fun)


class SaltBuiltIn(SaltStep):
    """
    Class to represent a Salt built-in command step

    Built-in commands like cmd.run and file.managed need
    to be condensed.
    """
    def __init__(self, desc, fun, target, args):
        super(SaltBuiltIn, self).__init__(desc, args)
        self.fun = fun
        self.target = target
        self.args = dict()
        for arg in args:
            if isinstance(arg, dict):
                for key, val in arg.items():
                    self.args[key] = val
            else:
                self.args['nokey'] = arg

    def pretty_string(self):
        arg_list = ""
        first = True
        for key, val in self.args.items():
            if key in ['name', 'pkg', 'pkgs']:
                if isinstance(val, list):
                    val = ", ".join(val)
                if first:
                    arg_list += val
                    first = False
                else:
                    arg_list += ", {}".format(val)
        if arg_list:
            return "{}({})".format(self.fun, arg_list)
        else:
            return "{}({})".format(self.fun, self.desc)

    def __str__(self):
        return "SaltBuiltIn(desc: {}, fun: {}, args: {})".format(self.desc, self.fun, self.args)
