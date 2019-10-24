from .validator import evaluate_module_return
from .exceptions import ModuleException, NoMinionsFound
from .utils import LocalClient
from salt.exceptions import SaltClientError

def exec_module(module='', function='', target='', arguments=[], **kwargs):
    """"""
    raise_on_failure = kwargs.get('raise_on_failure', True)
    tgt_type = kwargs.get('tgt_type', 'pillar')

    assert module
    assert function
    assert target

    # TODO: validate if the target actually matches something.
    # The question is how to do that without loosing too much performance.
    # If we pre-query the 'target' search string using test.true
    # it might be not too bad?
    # If we don't pre-validate the 'target' we get printed
    # No minions matched the target. No command was sent, no jid was assigned.
    # without additional context to the screen.

    _validate_target(target, tgt_type, module, function)

    ret = LocalClient().cmd(
        target, f'{module}.{function}', arguments, tgt_type=tgt_type)

    if not evaluate_module_return(ret):
        # evaluate_module_return writes a detailed message to the screen
        if raise_on_failure:
            raise ModuleException(False, ret)
        return (False, ret)
    return (True, ret)


def _validate_target(target, tgt_type, module, function):
    import sys
    import os
    # When search matches no minions, salt prints to stdout.  Suppress stdout.
    # TODO: implement this as with a contextmanager.. seems more suited than abusing
    # 'try: finally' to re-set the default sys.stdout
    try:
        _stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        minions = LocalClient().cmd(target, 'test.true', [], tgt_type=tgt_type)
        if not minions:
            raise NoMinionsFound(False, target, module, function, tgt_type)
    finally:
        sys.stdout = _stdout
