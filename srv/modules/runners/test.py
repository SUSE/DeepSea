from ext_lib.utils import do_x, runner, humanize_return, evaluate_runner_return


def return_struct(machine=False):
    # This is a module call behind the scene
    result, data = do_x()

    if machine:
        # TODO: this needs to be silenced, currently this will be printed to the screen.
        return result, data

    # replace print with logger of choice
    return humanize_return(result)


def runner_calls_runner(machine=False):
    """
    Temporarily going with 'machine' kwargs ..
    Not happy with that at all, but I didn't figure out
    how to get the 'context' like in plain python (__name__ == '__main__')
    """
    # This is a runner that calls a module behind the scene
    result, data = runner().cmd('test.return_struct', ['machine=True'])

    if machine:
        # TODO: this needs to be silenced, currently this will be printed to the screen.
        return result, data

    return humanize_return(result)
