from subprocess import CompletedProcess, CalledProcessError, TimeoutExpired


class ReturnStruct(object):

    # The location of this class is uncertain. This probably needs to
    # be accessible for all other modules aswell.

    DEFAULT_FAILED_RETURNCODE = 1

    def __init__(self, ret, func_name, module_name):
        """
        Accepts a return structure that can either be
        a CompletedProcess or a dict with the necessary fields:

        Open discussion on the fields.

        Also pass a func_name since this is hard to guess from the data we get
        from the return structure.
        """
        assert ret
        assert func_name
        assert module_name

        if isinstance(ret, CompletedProcess):
            ret = ret.__dict__
            self.command = self._format_command(
                ret.get('args', '') or 'No command captured')
        if isinstance(ret, CalledProcessError) or isinstance(
                ret, TimeoutExpired):
            ret = ret.__dict__
            self.command = self._format_command(
                ret.get('cmd', '') or 'No command captured')
        if not isinstance(ret, dict):
            # untested
            # __init__ shouldn't return non-None -> move that to a separate func
            return self(dict(stderr="Wrong arg type passed to ReturnStruct"))

        self.rc = ret.get('returncode', self.DEFAULT_FAILED_RETURNCODE)
        self.result = False if self.rc != 0 else True

        # Only populated when TimeoutExpired was received.
        # For consistency this should be populated _always_
        # not only when TimeoutExpired is received.
        self.timout = ret.get('timeout', 0)

        # Only populated when TimeoutExpired or CalledProcessError
        # was received. For consistency this should be populated
        # _always_.
        self.output = ret.get('output', '') or 'No output captured'

        self.out = ret.get('stdout', '') or 'No stdout captured'
        self.err = ret.get('stderr', '') or 'No stderr captured'

        # The retrieval of the func_name is horrible.
        # Unfortunately python doesn't allow runtime func_name inspection.
        # See: https://www.python.org/dev/peps/pep-3130/
        self.func_name = func_name
        self.module_name = self._set_module_name(module_name)
        self.comment = self._set_comment()
        self.human_result = self.humanize_bool()
        self.guide = self._guide()

    def _set_module_name(self, module_name):
        """
        salt passes something like:

        salt.ext.load.module.podman

        The only interesting part is the last piece after the dot.

        Fall back to the full module if that's not possible
        """
        try:
            return module_name.split('.')[-1]
        except IndexError:
            return module_name

    def _set_comment(self):
        """
        This can be situational based on what we got from the passed
        arguments.
        I.e. When returncode != 0 we can set the comment the commmand
        that was executed plus the stderr if set.

        This should act as something that can be output to the userfacing
        method(runner). TODO!
        """

        # Very basic example without conditionals that may be suited for logging
        return f"The function {self.func_name} of module {self.module_name} returned with code {self.rc}"

    def _guide(self):
        """ We may give debug guidance to the user if certain criterias are valid """

        if not self.result:
            return f"Try running: salt '<target_minion>' {self.module_name}.{self.func_name}"
        return "No guidance needed"

    def _format_command(self, cmd):
        """
        The extracted raw_command is of type <list> as this is what subprocesses
        expects. This is however not _too_ helpful for a human.
        Adding a concatenated version of the command may help for debugging.

        Think of c&p the command to execute it locally on the machine.
        Not sure if this will just pollute the ouput though.. Discuss!
        """
        if isinstance(cmd, list):
            return ' '.join(cmd)
        if isinstance(cmd, str):
            # cmd is already a string
            return cmd

    def humanize_bool(self):
        """ Translates bool to str"""
        if self.result:
            return 'success'
        return 'failure'
