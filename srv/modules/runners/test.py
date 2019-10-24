from ext_lib.utils import humanize_return, exec_runner
from ext_lib.exceptions import RunnerException, ModuleException
from ext_lib.operation import exec_module
from ext_lib.decorators import catches
"""
This is an example runner function that calls one minion-module internally.

It's expected to run in the following contexts:

By a human (default):
---------------------

This is probably the default. In this case we expect the function to be interactive
and verbose.

If an error is detected, the message is printed to the screen. The details are not
revealed.

By another runner (called_by_runner=True, non_interactive=True):
---------------------------------------------------------------

This is a probable context as we should allow to make runners composable.
Think of a scenario where we have `salt-run mon.deploy`, `salt-run mgr.deploy` and `salt-run osd.deploy`
These may be combined to create a `salt-run ceph.deploy` to create a 'one button' deployment.

In order to make this work, we need a way to pass information about the success or failure of the
runner to the invoking runner. This implementation uses Exceptions (ModuleException & RunnerException)
to standardize the communication between calls.

A disadvantage with this approach is that runners can't properly pass Exceptions to other runners.
This is an implementation choice/limitation of salt. It will instead return the stacktrace of the other runner
as a string.
To circumvent that, I created a function called exec_runner() in ext_lib.utils that re-raises an Exception
with the necessary information.
It's a bit hacky but I couldn't come up with a something else that makes runner callable by other runners
without loosing information.

By the orchestrator (called_by_orch=True, non_interactive=True):
---------------------------------------------------------------

It's the users choice if he wants to initiate an operation using the `salt-run`
or the `ceph orchestrator` interface. More importantly though is the dashboard.
All operations triggered in the dashboard are executed via the orchestrator. In order to
provide useful information we have to pass detailed returnstrucutres or meaninful error messages
up the stack.






Choosing this design, we have the benefit of a structured way of writing runners
independent of their inner workings. Runners would follow a similar theme.
Their composition stays the same.

try:
    <tuple> = func()

except Module/RunnerException:
    handle_exception()

finally:
    return <based_on_context[orch, runner, human]>

"""


@catches(ModuleException)
def good(non_interactive=False, called_by_runner=False, called_by_orch=False):
    results = list()

    result, data = exec_module(
        module='keyring',
        function='mon',
        target='roles:master',
        arguments=['admin'])

    results.append(result)

    result, data = exec_module(
        module='keyring',
        function='mon',
        target='roles:mon',
        arguments=['admin'])

    # maybe we should collect the 'data' var aswell..
    results.append(result)

    return results


@catches(ModuleException)
def bad(called_by_runner=False, called_by_orch=False):
    results = list()


    result, data = exec_module(
        module='keyring',
        function='mon_failure',
        target='roles:mon',
        arguments=['admin'])
        # TODO:
        # kwargs implementation is missing
    results.append(result)

    return results


@catches(RunnerException)
def runner_calls_runner(called_by_runner=False, called_by_orch=False):
    """
    Temporarily going with 'called_by_runner' kwargs ..
    Not happy with that at all, but I didn't figure out
    how to get the 'context' like in plain python (__name__ == '__main__')
    """
    # This is a runner that calls a module behind the scene

    results = list()

    #                                        this can be offloaded to exec_runner
    result, data = exec_runner('test.good')
    results.append(result)
    result, data = exec_runner('test.bad')
    results.append(result)
    result, data = exec_runner('test.good')
    results.append(result)

    return results

@catches(RunnerException)
def runner_calls_runner_calls_runner(called_by_runner=False,
                                     called_by_orch=False):
    result, data = exec_runner('test.runner_calls_runner')
