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
