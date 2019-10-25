class ModuleException(Exception):
    def __init__(self, result, data):
        self.result = result
        self.data = data

    def pretty_print_data(self):
        [
            print(f"insert nice failure output for {minion}")
            for minion, job_data in self.data.items()
        ]

    def output_for_orchestrator(self):
        return f"Caught an Exception while running <dummy>.(ment for orchestrator)"

    def output_for_human(self):
        return f"Caught an Exception while running <dummy>.(ment for a human)"

    def __str__(self):
        return f"Insert some nice data from self.data : {self.result}"


class AbortedByUser(Exception):

    def __init__(self, answer):
        self.answer =  answer

    def __repr__(self):
        return f"Aborted by user with answer {self.answer}"

class NoMinionsFound(Exception):
    def __init__(self, result, target, module, function, tgt_type):
        self.result = result
        self.target = target
        self.module = module
        self.function = function
        self.tgt_type = tgt_type

    def _prefix(self):
        if self.tgt_type == 'pillar':
            return "-I"
        if self.tgt_type == 'compound':
            return ""
        if self.tgt_type == 'grain':
            return "-G"

    @property
    def guide(self):
        return f"""
This is usally due to a wrong pillar configuration. Please verify if
the targeted role is assigned to any hosts. Verify it with:

salt {self._prefix()} {self.target} test.true
        """

    def output_for_orchestrator(self):
        return f"{self.module}.{self.function} failed. Can't find minions assigned to role {self.target} (ment for orchestrator)"

    def output_for_human(self):
        return f"{self.module}.{self.function} failed. Can't find minions assigned to role {self.target} (ment for human)\n{self.guide}"

    def __str__(self):
        return f"NoMinionsFound<{self.target}>"


class RunnerException(Exception):
    """ Runner command failed """

    def __init__(self, cmd, msg=None):
        # TODO: Add meaningful/useful attributes
        self.cmd = cmd
        self.msg = msg or 'Default error message'

    def output_for_orchestrator(self):
        return f"Caught an Exception in runner {self.cmd} (ment for orchestrator)"

    def output_for_human(self):
        return f"Caught an Exception in runner {self.cmd} (ment for a human)"
